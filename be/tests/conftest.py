"""Shared pytest fixtures for backend tests.

These fixtures simulate the AWS Lambda environment locally:

- ``mock_aws`` (moto) intercepts boto3 calls and emulates DynamoDB in memory.
- ``dynamodb_client`` is the mocked boto3 client.
- ``users_table`` provisions the ``users`` table to match the production schema.
- ``load_event`` loads sample Lambda events from ``tests/fixtures``.
"""
import json
import os
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
TABLE_NAME = "users"


@pytest.fixture
def dynamodb_client(monkeypatch):
    """A boto3 DynamoDB client pointed at a moto mock backend."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        yield client


@pytest.fixture
def users_table(dynamodb_client, monkeypatch):
    """Create the ``users`` table and expose the underlying client."""
    monkeypatch.setenv("USERS_TABLE", TABLE_NAME)

    dynamodb_client.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    yield dynamodb_client


@pytest.fixture
def load_event():
    """Return a loader for sample Lambda events stored in ``tests/fixtures``."""

    def _load(filename: str) -> dict:
        path = FIXTURES_DIR / filename
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    return _load