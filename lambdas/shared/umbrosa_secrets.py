"""
Shared utilities for Lambda functions
"""

import os
import json
import boto3
from typing import Dict, Any

# Initialize Secrets Manager client
secrets_client = boto3.client('secretsmanager')


def get_secret(secret_name: str) -> str:
    """Fetch secret value from AWS Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except Exception as e:
        print(f"❌ Error fetching secret {secret_name}: {e}")
        raise


def get_config() -> Dict[str, Any]:
    """Get configuration from secrets"""
    config_arn = os.getenv("CONFIG_SECRET_ARN")
    config_str = get_secret(config_arn)
    return json.loads(config_str)


def get_credentials() -> Dict[str, str]:
    """Get all credentials from secrets"""
    vapi_arn = os.getenv("VAPI_SECRET_ARN")
    supabase_arn = os.getenv("SUPABASE_SECRET_ARN")

    return {
        "VAPI_API_KEY": get_secret(vapi_arn),
        "SUPABASE_SERVICE_KEY": get_secret(supabase_arn),
    }
