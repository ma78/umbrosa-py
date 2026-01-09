"""
Lambda 1: Get Scheduled Calls
Step Function Task: Fetch list of calls to execute for a batch
"""

import os
from secrets import get_config
import json
from typing import List, Dict, Any, Optional

def lambda_handler(event, context):
    """
    Get scheduled calls for a batch

    Event input:
    {
        "batch": "morning" | "afternoon" | null
    }

    Returns:
    {
        "calls": [...]
    }
    """
    batch = event.get('batch')

    # Get config from Secrets Manager
    config = get_config()

    calls = [
        {
            "id": "f024a1ed-343e-4363-8b2d-9daf6af31110-0900",
            "name": "Daily 9:00 AM call to +61467807718",
            "assistantId": os.getenv("MARIA_ASSISTANT_ID", "f024a1ed-343e-4363-8b2d-9daf6af31110"),
            "phoneNumberId": config.get("vapi_phone_number_id"),
            "customerNumber": "+61467807718",
            "interviewSeriesId": os.getenv("INTERVIEW_SERIES_MARCUS", "a6462580-007c-4e31-805a-acd5de1dfee3"),
            "promptName": "marcus-daily-checkin",
            "batch": "morning"
        },
        {
            "id": "43950926-3935-4853-8475-14da102748b5-1620",
            "name": "Daily 4:20 PM call to +61415874467",
            "assistantId": os.getenv("VI_ASSISTANT_ID", "43950926-3935-4853-8475-14da102748b5"),
            "phoneNumberId": config.get("vapi_phone_number_id"),
            "customerNumber": "+61415874467",
            "interviewSeriesId": os.getenv("INTERVIEW_SERIES_SUE", "70b87980-eae2-49b0-98cc-036867a6a1fd"),
            "promptName": "sue-daily-checkin",
            "batch": "afternoon"
        }
    ]

    # Filter by batch
    if batch:
        calls = [c for c in calls if c.get("batch") == batch]

    print(f"📋 Found {len(calls)} scheduled calls for batch: {batch}")

    return {
        "calls": calls
    }
