"""Where sessions are saved: memory for local tests, DynamoDB in AWS."""
import copy
import os

import boto3


class MemoryStore:
    """A dict pretending to be a database. Used when TABLE_NAME is not set."""

    def __init__(self):
        self._items = {}

    def get(self, session_id):
        item = self._items.get(session_id)
        return copy.deepcopy(item) if item else None

    def put(self, item):
        self._items[item["session_id"]] = copy.deepcopy(item)


class DynamoStore:
    def __init__(self, table_name):
        self._table = boto3.resource("dynamodb").Table(table_name)

    def get(self, session_id):
        return self._table.get_item(Key={"session_id": session_id}).get("Item")

    def put(self, item):
        self._table.put_item(Item=item)


def get_store():
    table_name = os.environ.get("TABLE_NAME")
    return DynamoStore(table_name) if table_name else MemoryStore()
