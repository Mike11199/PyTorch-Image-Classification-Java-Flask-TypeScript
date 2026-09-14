"""AWS job records with conditional version checks."""

import json


class DynamoDbRecords:
    """Keep the existing DynamoDB record format and TTL fields."""

    def __init__(self, table_name):
        """Connect to the configured job table."""
        import boto3

        self.table = boto3.resource("dynamodb").Table(table_name)

    def get(self, key):
        item = self.table.get_item(Key={"id": key}, ConsistentRead=True).get("Item")
        return json.loads(item["body"]) if item else None

    def save_request(self, record, expected):
        """Build a conditional write with an optional expiry."""
        item = {
            "id": record["id"],
            "body": json.dumps(record),
            "version": record["version"],
        }
        if record.get("expiresAt") is not None:
            item["expiresAt"] = record["expiresAt"]
        if expected is None:
            return {"Item": item, "ConditionExpression": "attribute_not_exists(id)"}
        return {
            "Item": item,
            "ConditionExpression": "#v = :v",
            "ExpressionAttributeNames": {"#v": "version"},
            "ExpressionAttributeValues": {":v": expected},
        }

    def save(self, record, expected):
        """Return None if another writer changed the record first."""
        try:
            self.table.put_item(**self.save_request(record, expected))
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return None
        return record

    def all(self):
        """Read every scan page before selecting queued jobs."""
        records = []
        arguments = {}
        while True:
            page = self.table.scan(**arguments)
            records.extend(json.loads(item["body"]) for item in page["Items"])
            if "LastEvaluatedKey" not in page:
                return records
            arguments["ExclusiveStartKey"] = page["LastEvaluatedKey"]
