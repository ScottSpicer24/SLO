"""DynamoDB connection helpers.

Wraps boto3 so the rest of the application never touches boto3 directly.
"""
import os

import boto3


def get_dynamodb_resource():
    """Return a boto3 DynamoDB resource for the current region."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.resource("dynamodb", region_name=region)


def get_table(table_name: str):
    """Return a DynamoDB Table handle for the given table name."""
    return get_dynamodb_resource().Table(table_name)