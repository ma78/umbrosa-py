"""
Lambda 2: Get Conversation Context
Step Function Task: Fetch previous conversation context from Supabase
"""

import os
from src.secrets import get_credentials
from supabase import create_client

def lambda_handler(event, context):
    """
    Get conversation context for an interview series

    Event input:
    {
        "interviewSeriesId": "uuid"
    }

    Returns:
    {
        "context": "conversation context or null"
    }
    """
    interview_series_id = event.get('interviewSeriesId')

    # Get credentials from Secrets Manager
    creds = get_credentials()

    supabase = create_client(
        os.getenv("SUPABASE_URL", "https://your-project.supabase.co"),
        creds["SUPABASE_SERVICE_KEY"]
    )

    try:
        result = supabase.table('call_transcripts').select(
            'summary, key_insights, action_items, context_summary'
        ).eq(
            'interview_series_id', interview_series_id
        ).order(
            'created_at', desc=True
        ).limit(
            1
        ).maybe_single()

        if result.data:
            context = result.data.get('context_summary') or result.data.get('summary')
            print(f"✅ Found context for {interview_series_id}")
            return {
                "context": context,
                "interviewSeriesId": interview_series_id
            }

        print(f"ℹ️ No previous context for {interview_series_id}")
        return {
            "context": None,
            "interviewSeriesId": interview_series_id
        }

    except Exception as e:
        print(f"❌ Error fetching context: {e}")
        raise
