import logging
from datetime import datetime, timedelta, timezone

import boto3
import requests
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException
from models import AnnouncementModel
from pydantic import BaseModel
from settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Initialize SQS client
sqs = boto3.client("sqs", region_name=settings.aws_region)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)

table = dynamodb.Table(settings.dynamodb_table_name)


class Announcement(BaseModel):
    employer_id: str
    message: str
    send_immediately: bool
    send_at: int | None = None


@router.post("/send_announcement")
async def send_announcement(announcement: Announcement):
    try:
        logger.info("Received request to send announcement.")

        # Save announcement to DynamoDB
        save_to_dynamodb(announcement)

        # If the announcement is for now or scheduled within the next 5 minutes
        if announcement.send_immediately or (
            announcement.send_at
            and datetime.fromtimestamp(announcement.send_at) <= datetime.now() + timedelta(minutes=5)
        ):
            # Call another service to retrieve employees for the employer_id
            employees_response = requests.get(
                settings.get_all_employees_url(announcement.employer_id),
                timeout=settings.requests_timeout_secs,
            )
            employees = employees_response.json()["employees"]

            for _ in employees:
                send_announcement_to_queue(announcement)

    except requests.RequestException as e:
        logger.error(f"Error sending announcement: {e}")

        raise HTTPException(status_code=500, detail="Failed to send announcement")


def send_announcement_to_queue(announcement: Announcement):
    try:
        delay_seconds = 0
        if announcement.send_at:
            delay_seconds = max(0, int((announcement.send_at - datetime.utcnow()).total_seconds()))

        response = sqs.send_message(
            QueueUrl=settings.sqs_queue_url,
            MessageBody=announcement.model_dump_json(),
            DelaySeconds=delay_seconds,
        )
        print("Announcement sent to SQS:", response.get("MessageId"))
    except ClientError as e:
        print("Error sending announcement to SQS:", e)
        raise HTTPException(status_code=500, detail="Failed to send announcement to SQS")


def save_to_dynamodb(announcement: Announcement):
    try:
        # Save announcement to DynamoDB
        announcement_item = AnnouncementModel(
            employer_id=announcement.employer_id,
            message=announcement.message,
            send_immediately=announcement.send_immediately,
            send_at=str(announcement.send_at) if announcement.send_at else None,
        )
        announcement_item.save()
        logger.info("Announcement saved to DynamoDB.")
    except Exception as e:
        logger.error(f"Error saving announcement to DynamoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to save announcement to DynamoDB")
