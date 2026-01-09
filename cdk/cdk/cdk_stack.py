"""
Umbrosa Backend CDK Stack

Deploys Lambda functions, Step Functions, and API Gateway
for scheduled Vapi calls and webhook processing.
"""

from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_events as events,
    aws_events_targets as targets,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct

class UmbrosaBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ============================================
        # Secrets Manager
        # ============================================

        vapi_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "VapiSecret", "umbrosa/vapi_api_key"
        )

        supabase_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "SupabaseSecret", "umbrosa/supabase_service_key"
        )

        config_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "ConfigSecret", "umbrosa/config"
        )

        # ============================================
        # Lambda Functions
        # ============================================

        # Common Lambda configuration
        lambda_props = {
            "runtime": _lambda.Runtime.PYTHON_3_12,
            "timeout": Duration.seconds(60),
            "memory_size": 256,
            "environment": {
                "SUPABASE_URL": config_secret.secret_value_from_json("supabase_url").to_string(),
                "SUPABASE_SERVICE_KEY": supabase_secret.secret_value_to_string(),
                "VAPI_API_KEY": vapi_secret.secret_value_to_string(),
                "VAPI_PHONE_NUMBER_ID": config_secret.secret_value_from_json("vapi_phone_number_id").to_string(),
                "MARIA_ASSISTANT_ID": self.node.try_get_context("maria_assistant_id") or "f024a1ed-343e-4363-8b2d-9daf6af31110",
                "VI_ASSISTANT_ID": self.node.try_get_context("vi_assistant_id") or "43950926-3935-4853-8475-14da102748b5",
                "INTERVIEW_SERIES_MARCUS": self.node.try_get_context("interview_series_marcus") or "a6462580-007c-4e31-805a-acd5de1dfee3",
                "INTERVIEW_SERIES_SUE": self.node.try_get_context("interview_series_sue") or "70b87980-eae2-49b0-98cc-036867a6a1fd",
            },
        }

        # Get Scheduled Calls Function
        get_scheduled_calls_fn = _lambda.Function(
            self,
            "GetScheduledCallsFunction",
            **lambda_props,
            code=_lambda.Code.from_asset("../lambdas/scheduled-calls"),
            handler="handler.lambda_handler",
            description="Get list of scheduled calls for a batch",
        )

        # Get Context Function
        get_context_fn = _lambda.Function(
            self,
            "GetContextFunction",
            **lambda_props,
            code=_lambda.Code.from_asset("../lambdas/get-context"),
            handler="handler.lambda_handler",
            description="Fetch conversation context from Supabase",
        )

        # Create Vapi Call Function
        create_vapi_call_fn = _lambda.Function(
            self,
            "CreateVapiCallFunction",
            **{**lambda_props, "timeout": Duration.seconds(30)},
            code=_lambda.Code.from_asset("../lambdas/create-vapi-call"),
            handler="handler.lambda_handler",
            description="Create outbound Vapi call",
        )

        # Webhook Function
        webhook_fn = _lambda.Function(
            self,
            "WebhookFunction",
            **{**lambda_props, "timeout": Duration.seconds(30)},
            code=_lambda.Code.from_asset("../lambdas/webhook"),
            handler="handler.lambda_handler",
            description="Process Vapi webhook and store transcripts",
        )

        # Grant Lambda functions permission to read secrets
        for fn in [get_scheduled_calls_fn, get_context_fn, create_vapi_call_fn, webhook_fn]:
            vapi_secret.grant_read(fn)
            supabase_secret.grant_read(fn)
            config_secret.grant_read(fn)

        # ============================================
        # API Gateway (for webhook)
        # ============================================

        api = apigateway.RestApi(
            self,
            "UmbrosaApi",
            rest_api_name="Umbrosa Service",
            description="Umbrosa webhook API",
            deploy_options={
                "stage_name": "prod",
                "throttling_burst_limit": 10,
                "throttling_rate_limit": 5,
            },
            default_cors_preflight_options={
                "allow_origins": apigateway.Cors.ALL_ORIGINS,
                "allow_methods": apigateway.Cors.ALL_METHODS,
            },
        )

        webhook_integration = apigateway.LambdaIntegration(webhook_fn)
        api.root.add_resource("webhook").add_method(
            "POST", webhook_integration
        )

        # ============================================
        # Step Functions State Machine
        # ============================================

        # Define Step Functions workflow
        get_scheduled_calls = tasks.LambdaInvoke(
            self,
            "Get Scheduled Calls",
            lambda_function=get_scheduled_calls_fn,
            output_path="$.Payload",
        )

        # Map state for parallel call execution
        get_context = tasks.LambdaInvoke(
            self,
            "Get Conversation Context",
            lambda_function=get_context_fn,
            output_path="$.Payload",
        )

        create_vapi_call = tasks.LambdaInvoke(
            self,
            "Create Vapi Call",
            lambda_function=create_vapi_call_fn,
            output_path="$.Payload",
        )

        # Define the workflow chain
        definition = get_scheduled_calls.next(
            sfn.Map(
                self,
                "Map Calls",
                items_path=sfn.JsonPath.string_at("$.calls"),
                max_concurrency=5,
                result_path="$.results",
            ).item_processor(
                get_context.next(create_vapi_call)
            )
        )

        # Create State Machine
        state_machine = sfn.StateMachine(
            self,
            "ScheduledCallsWorkflow",
            state_machine_name="UmbrosaScheduledCalls",
            definition=definition,
            timeout=Duration.minutes(5),
        )

        # ============================================
        # EventBridge Schedules
        # ============================================

        # Morning batch (9:00 AM Sydney = 11:00 PM UTC previous day)
        # Using cron(30 0 * * ? *) which is 00:30 UTC
        morning_schedule = events.Rule(
            self,
            "MorningScheduleRule",
            schedule=events.Schedule.cron(minute="30", hour="0"),
            description="Trigger morning batch of scheduled calls",
        )
        morning_schedule.add_target(
            targets.SfnStateMachine(
                state_machine,
                input=events.RuleTargetInput.from_object({"batch": "morning"}),
            )
        )

        # Afternoon batch (4:20 PM Sydney = 5:20 AM UTC)
        # Using cron(20 5 * * ? *) which is 05:20 UTC
        afternoon_schedule = events.Rule(
            self,
            "AfternoonScheduleRule",
            schedule=events.Schedule.cron(minute="20", hour="5"),
            description="Trigger afternoon batch of scheduled calls",
        )
        afternoon_schedule.add_target(
            targets.SfnStateMachine(
                state_machine,
                input=events.RuleTargetInput.from_object({"batch": "afternoon"}),
            )
        )

        # ============================================
        # Outputs
        # ============================================

        CfnOutput(
            self,
            "WebhookApiUrl",
            value=api.url_for_path("/webhook"),
            description="Vapi webhook URL",
        )

        CfnOutput(
            self,
            "StateMachineArn",
            value=state_machine.state_machine_arn,
            description="Step Functions State Machine ARN",
        )

        CfnOutput(
            self,
            "GetScheduledCallsFunctionArn",
            value=get_scheduled_calls_fn.function_arn,
            description="Get Scheduled Calls Lambda ARN",
        )
