"""
Lambda 3: Create Vapi Call
Step Function Task: Create outbound call using Vapi SDK
"""

import os
from src.secrets import get_credentials
from vapi import Vapi

def lambda_handler(event, context):
    """
    Create a Vapi outbound call

    Event input:
    {
        "assistantId": "uuid",
        "phoneNumberId": "uuid",
        "customerNumber": "+61467807718",
        "context": "previous conversation context or null",
        "interviewSeriesId": "uuid"
    }

    Returns:
    {
        "vapiCallId": "uuid",
        "customerNumber": "+61467807718",
        "status": "created"
    }
    """
    assistant_id = event.get('assistantId')
    phone_number_id = event.get('phoneNumberId')
    customer_number = event.get('customerNumber')
    previous_context = event.get('context')

    # Get credentials from Secrets Manager
    creds = get_credentials()

    vapi = Vapi(api_key=creds["VAPI_API_KEY"])

    print(f"📞 Creating call to {customer_number}")
    print(f"   → Assistant: {assistant_id}")
    print(f"   → Phone ID: {phone_number_id}")

    try:
        # Prepare assistant overrides
        assistant_overrides = {"variableValues": {}}

        # Inject conversation context
        if previous_context:
            assistant_overrides["variableValues"]["previousContext"] = previous_context
            print(f"   ✓ Injected previous context")

        # Create call
        call = vapi.calls.create(
            phone_number_id=phone_number_id,
            customer_number=customer_number,
            assistant_id=assistant_id,
            assistant_overrides=assistant_overrides
        )

        print(f"✅ Call created: {call.get('id')}")

        return {
            "vapiCallId": call.get('id'),
            "customerNumber": customer_number,
            "status": "created"
        }

    except Exception as e:
        print(f"❌ Error creating Vapi call: {e}")
        raise
