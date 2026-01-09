"""
Lambda 4: Vapi Webhook Processor
Handles end-of-call-report from Vapi and stores transcripts to Supabase
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
from supabase import create_client
from secrets import get_credentials, get_config

def lambda_handler(event, context):
    """
    Process Vapi webhook and store transcript to Supabase

    Event input: Vapi webhook payload
    {
        "message": {
            "type": "end-of-call-report",
            "call": {
                "id": "uuid",
                "assistant": {...},
                "analysis": {...}
            }
        }
    }
    """
    print(f"📥 Webhook received at {datetime.utcnow().isoformat()}")

    # Get credentials from Secrets Manager
    creds = get_credentials()
    config = get_config()

    supabase = create_client(
        config.get("supabase_url"),
        creds["SUPABASE_SERVICE_KEY"]
    )

    try:
        # Parse webhook body
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', {})
        call_data = message.get('call', {})

        if message.get('type') != 'end-of-call-report':
            print(f"ℹ️ Ignoring non-end-of-call-report: {message.get('type')}")
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ignored'})
            }

        # Extract data from call
        vapi_call_id = call_data.get('id')
        analysis = call_data.get('analysis', {})
        transcript = call_data.get('transcript', [])

        # Extract structured data
        summary = analysis.get('summary', '')
        key_insights = analysis.get('actionItems', [])
        action_items = analysis.get('actionItems', [])

        # Build context summary
        context_summary = f"Summary: {summary}\n\nKey Insights: {key_insights}"

        # Store in Supabase
        record = {
            'vapi_call_id': vapi_call_id,
            'transcript': transcript,
            'summary': summary,
            'key_insights': key_insights,
            'action_items': action_items,
            'context_summary': context_summary,
            'created_at': datetime.utcnow().isoformat()
        }

        result = supabase.table('call_transcripts').insert(record).execute()

        print(f"✅ Transcript stored for call {vapi_call_id}")
        print(f"   → Supabase ID: {result.data[0].get('id')}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'supabase_id': result.data[0].get('id')
            })
        }

    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
