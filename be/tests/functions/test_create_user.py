"""Tests for the create_user Lambda handler."""
import json

from functions.create_user.handler import handler
from shared.db import tables


def test_create_user_success(users_table, load_event):
    event = load_event("api_gateway_create_user.json")

    response = handler(event, None)

    assert response["statusCode"] == 201
    assert response["headers"]["Content-Type"] == "application/json"

    body = json.loads(response["body"])
    assert body["name"] == "Scott"
    assert body["email"] == "scott@example.com"
    assert body["status"] == "active"
    assert body["user_id"]

    # Confirm the user was actually persisted to the (mocked) table.
    stored = users_table.get_item(
        TableName=tables.get_users_table_name(),
        Key={"user_id": {"S": body["user_id"]}},
    )
    assert stored["Item"]["name"]["S"] == "Scott"
    assert stored["Item"]["email"]["S"] == "scott@example.com"
    assert stored["Item"]["status"]["S"] == "active"


def test_create_user_without_name(users_table, load_event):
    event = load_event("api_gateway_create_user.json")
    event["body"] = json.dumps({"email": "scott@example.com"})

    response = handler(event, None)

    assert response["statusCode"] == 400
    assert "name" in json.loads(response["body"])["error"]


def test_create_user_without_email(users_table, load_event):
    event = load_event("api_gateway_create_user.json")
    event["body"] = json.dumps({"name": "Scott"})

    response = handler(event, None)

    assert response["statusCode"] == 400
    assert "email" in json.loads(response["body"])["error"]


def test_create_user_empty_body(users_table, load_event):
    event = load_event("api_gateway_create_user.json")
    event["body"] = json.dumps({})

    response = handler(event, None)

    assert response["statusCode"] == 400


def test_create_user_invalid_json(users_table, load_event):
    event = load_event("api_gateway_create_user.json")
    event["body"] = "not valid json {"

    response = handler(event, None)

    assert response["statusCode"] == 400