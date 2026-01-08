# Umbrosa Python Backend

Lambda functions and Step Functions for Umbrosa voice AI automation.

## Architecture

```
EventBridge Scheduler
        ↓
Step Functions (ScheduledCallsWorkflow)
        ↓
    ┌────────────────────────────────┐
    │ 1. Get Scheduled Calls         │
    │ 2. Map (parallel execution)    │
    │    ├─ Get Context (Supabase)   │
    │    └─ Create Vapi Call         │
    └────────────────────────────────┘
        ↓
   Summary Report
```

## Lambda Functions

| Function | Purpose |
|----------|---------|
| `scheduled-calls` | Fetch scheduled calls for batch |
| `get-context` | Retrieve conversation context from Supabase |
| `create-vapi-call` | Create outbound Vapi call |
| `webhook` | Process Vapi webhook and store transcripts |

## Deployment

### Prerequisites

```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Configure AWS credentials (already done)
aws configure import --profile your-admin-profile
```

### Deploy

```bash
# Build SAM template
sam build

# Deploy with interactive prompts
sam deploy --guided

# Or deploy with config file
sam deploy --config-file samconfig.toml
```

### Environment Variables

During deployment, SAM will prompt for:

- `SupabaseUrl`: Supabase project URL
- `SupabaseServiceKey`: Supabase service role key
- `VapiKey`: Vapi API key
- `VapiPhoneNumberId`: Vapi phone number ID
- `MariaAssistantId`: Maria assistant ID (default: f024a1ed-343e-4363-8b2d-9daf6af31110)
- `ViAssistantId`: Vi assistant ID (default: 43950926-3935-4853-8475-14da102748b5)
- `InterviewSeriesMarcus`: Marcus interview series ID
- `InterviewSeriesSue`: Sue interview series ID

## Schedules

- **Morning batch**: 00:30 UTC (9:00 AM Sydney)
- **Afternoon batch**: 05:20 UTC (4:20 PM Sydney)

## Outputs

After deployment, SAM will output:

- `WebhookApiUrl`: Vapi webhook URL (add this to Vapi dashboard)
- `ScheduledCallsWorkflowArn`: Step Functions workflow ARN
- `WebhookFunctionArn`: Webhook Lambda ARN

## Testing

```bash
# Test Step Function manually
aws stepfunctions start-execution \
  --state-machine-arn <WORKFLOW_ARN> \
  --input '{"batch": "morning"}'

# View executions
aws stepfunctions list-executions \
  --state-machine-arn <WORKFLOW_ARN>

# Test webhook (requires Vapi payload)
curl -X POST <WEBHOOK_API_URL> \
  -H 'Content-Type: application/json' \
  -d @test-webhook-payload.json
```

## Monitoring

- **Step Functions**: AWS Console → Step Functions → ScheduledCallsWorkflow
- **CloudWatch Logs**: /aws/lambda/* (all Lambda functions)
- **CloudWatch Alarms**: Auto-created for Lambda errors

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="your-url"
export SUPABASE_SERVICE_KEY="your-key"
export VAPI_API_KEY="your-key"
export VAPI_PHONE_NUMBER_ID="your-phone-id"

# Test individual Lambda functions
python -m lambdas.scheduled-calls.handler
python -m lambdas.get-context.handler
python -m lambdas.create-vapi-call.handler
```

## Pipeline

### GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-southeast-2

      - name: Install SAM CLI
        run: pip install aws-sam-cli

      - name: Build
        run: sam build

      - name: Deploy
        run: sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          VAPI_API_KEY: ${{ secrets.VAPI_API_KEY }}
          VAPI_PHONE_NUMBER_ID: ${{ secrets.VAPI_PHONE_NUMBER_ID }}
```

## Cost

**Free tier usage:**
- Lambda: 1M requests/month (you use ~120/month)
- Step Functions: 4,000 transitions/month (you use ~40/month)
- API Gateway: 1M API calls/month (you use ~60/month)

**Estimated cost**: ~$0/month

## License

MIT
