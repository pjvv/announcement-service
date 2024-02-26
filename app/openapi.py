import json

from dotenv import load_dotenv


def create_openapi_spec(file_name: str):
    with open(file_name, mode="w", encoding="utf-8") as fp:
        from main import app

        json.dump(app.openapi(), fp, indent=2)


if __name__ == "__main__":
    load_dotenv(".env")
    create_openapi_spec("openapi.json")
