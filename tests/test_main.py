import boto3
import moto
import pytest
import responses
from fastapi.testclient import TestClient
from freezegun import freeze_time
from main import app
from models import AnnouncementModel


@pytest.fixture
def mock_dynamodb():
    with moto.mock_dynamodb():
        yield


@pytest.fixture
def mock_sqs():
    with moto.mock_sqs():
        yield boto3.client("sqs", region_name="us-west-2")


@pytest.fixture
def test_client():
    return TestClient(app)


@responses.activate
def test_send_announcement_immediately(mock_dynamodb, mock_sqs, test_client):
    # Create DynamoDB table
    AnnouncementModel.create_table()

    queue_url = mock_sqs.create_queue(QueueName="test-queue")["QueueUrl"]

    # Mock response from the employers service
    responses.add(
        responses.GET,
        "http://localhost/employees?employerId=123",
        json={"employees": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]},
        status=200,
    )

    # Make request for sending immediately
    response_immediate = test_client.post(
        "/send_announcement/",
        json={
            "employer_id": "123",
            "message": "Test announcement",
            "send_immediately": True,
            "send_at": None,
        },
    )

    # Check if the request was successful
    assert response_immediate.status_code == 200

    # Check if the announcement was saved in DynamoDB
    announcements = list(AnnouncementModel.scan())
    assert len(announcements) == 1

    # Check if announcement attributes match
    announcement = announcements[0]
    assert announcement.employer_id == "123"
    assert announcement.message == "Test announcement"
    assert announcement.send_immediately == True
    assert announcement.send_at == None

    # Check if the announcement is sent to the queue
    messages = mock_sqs.receive_message(QueueUrl=queue_url)
    assert len(messages["Messages"]) == 1


@responses.activate
@freeze_time("2012-01-14 03:21:34")
def test_send_scheduled_announcement(mock_dynamodb, mock_sqs, test_client):
    # Create DynamoDB table
    AnnouncementModel.create_table()

    queue_url = mock_sqs.create_queue(QueueName="test-queue")["QueueUrl"]

    # Make request for sending immediately
    response_immediate = test_client.post(
        "/send_announcement/",
        json={
            "employer_id": "123",
            "message": "Test announcement",
            "send_immediately": False,
            "send_at": "1708977438",
        },
    )

    # Check if the request was successful
    assert response_immediate.status_code == 200

    # Check if the announcement was saved in DynamoDB
    announcements = list(AnnouncementModel.scan())
    assert len(announcements) == 1

    # Check if announcement attributes match
    announcement = announcements[0]
    assert announcement.employer_id == "123"
    assert announcement.message == "Test announcement"
    assert announcement.send_immediately == False
    assert announcement.send_at == "1708977438"

    # Check if the announcement is sent to the queue
    messages = mock_sqs.receive_message(QueueUrl=queue_url)
    assert "Messsages" not in messages
