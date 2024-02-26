from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    aws_region: str = "us-west-2"

    # Your SQS queue URL
    sqs_queue_url: str = "test-queue"

    dynamodb_table_name: str = "AnnouncementsTable"

    employees_service_base_url: str = "http://localhost"

    requests_timeout_secs: int = 30

    def get_all_employees_url(self, employer_id) -> str:
        # URL of the service to retrieve employees for a given employer_id
        return f"{self.employees_service_base_url}/employees?employerId={employer_id}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
