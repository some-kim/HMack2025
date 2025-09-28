"""
DynamoDB CRUD utilities for CareConnector application.

This module provides comprehensive CRUD operations for the DynamoDB table
deployed via the CDK infrastructure. The table uses a single-table design
with partition key (PK) and sort key (SK) pattern.

Table Schema:
- Table Name: careconnector-main
- Partition Key: PK (String)
- Sort Key: SK (String)
- GSI1: GSI1PK (String), GSI1SK (String)
- GSI2: GSI2PK (String), GSI2SK (String)
"""

import boto3
import os
import logging
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDBUtils:
    """Utility class for DynamoDB operations."""

    def __init__(self, table_name: str = None, region_name: str = None):
        """
        Initialize DynamoDB client and table resource.

        Args:
            table_name: Name of the DynamoDB table. If None, reads from environment or uses default.
            region_name: AWS region. If None, uses default from environment.
        """
        self.region_name = region_name or os.getenv('AWS_DEFAULT_REGION', 'us-east-2')
        self.table_name = table_name or os.getenv('PATIENTS_TABLE_NAME', 'careconnector-main')

        # Initialize DynamoDB resources
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
        self.table = self.dynamodb.Table(self.table_name)

        logger.info(f"Initialized DynamoDB utils for table: {self.table_name} in region: {self.region_name}")

    def create_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new item in the table.

        Args:
            item: Dictionary containing the item data. Must include PK and SK.

        Returns:
            Dict containing the created item with metadata.

        Raises:
            ValueError: If PK or SK is missing.
            ClientError: If DynamoDB operation fails.
        """
        if 'PK' not in item or 'SK' not in item:
            raise ValueError("Item must contain both 'PK' and 'SK' keys")

        # Add metadata
        timestamp = datetime.utcnow().isoformat()
        item_with_metadata = {
            **item,
            'CreatedAt': timestamp,
            'UpdatedAt': timestamp,
            'ItemId': str(uuid.uuid4())
        }

        try:
            response = self.table.put_item(
                Item=item_with_metadata,
                ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
            )
            logger.info(f"Created item with PK: {item['PK']}, SK: {item['SK']}")
            return {
                'item': item_with_metadata,
                'response_metadata': response.get('ResponseMetadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Item with PK: {item['PK']}, SK: {item['SK']} already exists")
            logger.error(f"Error creating item: {e}")
            raise

    def get_item(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item by partition key and sort key.

        Args:
            pk: Partition key value.
            sk: Sort key value.

        Returns:
            Dictionary containing the item data, or None if not found.
        """
        try:
            response = self.table.get_item(
                Key={'PK': pk, 'SK': sk}
            )
            item = response.get('Item')
            if item:
                logger.info(f"Retrieved item with PK: {pk}, SK: {sk}")
            return item
        except ClientError as e:
            logger.error(f"Error retrieving item PK: {pk}, SK: {sk}: {e}")
            raise

    def update_item(self, pk: str, sk: str, updates: Dict[str, Any],
                   condition_expression: str = None) -> Dict[str, Any]:
        """
        Update an existing item.

        Args:
            pk: Partition key value.
            sk: Sort key value.
            updates: Dictionary of attributes to update.
            condition_expression: Optional condition for the update.

        Returns:
            Dictionary containing the updated item.
        """
        # Prepare update expression
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        # Add UpdatedAt timestamp
        updates['UpdatedAt'] = datetime.utcnow().isoformat()

        for key, value in updates.items():
            attr_name = f"#{key}"
            attr_value = f":{key}"
            update_expression_parts.append(f"{attr_name} = {attr_value}")
            expression_attribute_names[attr_name] = key
            expression_attribute_values[attr_value] = value

        update_expression = "SET " + ", ".join(update_expression_parts)

        try:
            kwargs = {
                'Key': {'PK': pk, 'SK': sk},
                'UpdateExpression': update_expression,
                'ExpressionAttributeNames': expression_attribute_names,
                'ExpressionAttributeValues': expression_attribute_values,
                'ReturnValues': 'ALL_NEW'
            }

            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = self.table.update_item(**kwargs)
            logger.info(f"Updated item with PK: {pk}, SK: {sk}")
            return response['Attributes']
        except ClientError as e:
            logger.error(f"Error updating item PK: {pk}, SK: {sk}: {e}")
            raise

    def delete_item(self, pk: str, sk: str, condition_expression: str = None) -> bool:
        """
        Delete an item from the table.

        Args:
            pk: Partition key value.
            sk: Sort key value.
            condition_expression: Optional condition for the deletion.

        Returns:
            True if the item was deleted, False if it didn't exist.
        """
        try:
            kwargs = {
                'Key': {'PK': pk, 'SK': sk},
                'ReturnValues': 'ALL_OLD'
            }

            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = self.table.delete_item(**kwargs)
            deleted_item = response.get('Attributes')

            if deleted_item:
                logger.info(f"Deleted item with PK: {pk}, SK: {sk}")
                return True
            else:
                logger.info(f"Item with PK: {pk}, SK: {sk} did not exist")
                return False
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Condition failed for deleting item PK: {pk}, SK: {sk}")
                return False
            logger.error(f"Error deleting item PK: {pk}, SK: {sk}: {e}")
            raise

    def query_items(self, pk: str, sk_condition: str = None,
                   index_name: str = None, limit: int = None,
                   scan_index_forward: bool = True) -> List[Dict[str, Any]]:
        """
        Query items by partition key and optional sort key condition.

        Args:
            pk: Partition key value.
            sk_condition: Optional sort key condition (e.g., "begins_with(SK, 'USER#')")
            index_name: Optional GSI name ('GSI1' or 'GSI2').
            limit: Maximum number of items to return.
            scan_index_forward: Sort order (True for ascending, False for descending).

        Returns:
            List of items matching the query.
        """
        try:
            # Determine which key to use based on index
            if index_name == 'GSI1':
                pk_name = 'GSI1PK'
                sk_name = 'GSI1SK'
            elif index_name == 'GSI2':
                pk_name = 'GSI2PK'
                sk_name = 'GSI2SK'
            else:
                pk_name = 'PK'
                sk_name = 'SK'

            # Build key condition expression
            key_condition = f"{pk_name} = :pk"
            expression_attribute_values = {':pk': pk}

            if sk_condition:
                key_condition += f" AND {sk_condition}"

            kwargs = {
                'KeyConditionExpression': key_condition,
                'ExpressionAttributeValues': expression_attribute_values,
                'ScanIndexForward': scan_index_forward
            }

            if index_name:
                kwargs['IndexName'] = index_name

            if limit:
                kwargs['Limit'] = limit

            response = self.table.query(**kwargs)
            items = response.get('Items', [])

            logger.info(f"Queried {len(items)} items with PK: {pk}")
            return items
        except ClientError as e:
            logger.error(f"Error querying items with PK: {pk}: {e}")
            raise

    def scan_items(self, filter_expression: str = None, limit: int = None,
                  index_name: str = None) -> List[Dict[str, Any]]:
        """
        Scan the entire table or index with optional filtering.

        Args:
            filter_expression: Optional filter expression.
            limit: Maximum number of items to return.
            index_name: Optional GSI name ('GSI1' or 'GSI2').

        Returns:
            List of items from the scan.

        Note:
            Use with caution on large tables as this operation can be expensive.
        """
        try:
            kwargs = {}

            if filter_expression:
                kwargs['FilterExpression'] = filter_expression

            if limit:
                kwargs['Limit'] = limit

            if index_name:
                kwargs['IndexName'] = index_name

            response = self.table.scan(**kwargs)
            items = response.get('Items', [])

            logger.info(f"Scanned {len(items)} items")
            return items
        except ClientError as e:
            logger.error(f"Error scanning table: {e}")
            raise

    def batch_get_items(self, keys: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Batch get multiple items by their keys.

        Args:
            keys: List of dictionaries containing PK and SK values.

        Returns:
            List of retrieved items.
        """
        if not keys:
            return []

        try:
            # DynamoDB batch_get_item has a limit of 100 items per request
            all_items = []

            for i in range(0, len(keys), 100):
                batch_keys = keys[i:i + 100]

                response = self.dynamodb.batch_get_item(
                    RequestItems={
                        self.table_name: {
                            'Keys': batch_keys
                        }
                    }
                )

                items = response.get('Responses', {}).get(self.table_name, [])
                all_items.extend(items)

                # Handle unprocessed keys
                unprocessed = response.get('UnprocessedKeys', {})
                while unprocessed:
                    response = self.dynamodb.batch_get_item(RequestItems=unprocessed)
                    items = response.get('Responses', {}).get(self.table_name, [])
                    all_items.extend(items)
                    unprocessed = response.get('UnprocessedKeys', {})

            logger.info(f"Batch retrieved {len(all_items)} items")
            return all_items
        except ClientError as e:
            logger.error(f"Error in batch get items: {e}")
            raise

    def batch_write_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch write multiple items to the table.

        Args:
            items: List of items to write. Each must contain PK and SK.

        Returns:
            Dictionary containing operation results and any unprocessed items.
        """
        if not items:
            return {'processed': 0, 'unprocessed': []}

        # Add metadata to items
        timestamp = datetime.utcnow().isoformat()
        items_with_metadata = []

        for item in items:
            if 'PK' not in item or 'SK' not in item:
                raise ValueError("All items must contain both 'PK' and 'SK' keys")

            item_with_metadata = {
                **item,
                'CreatedAt': item.get('CreatedAt', timestamp),
                'UpdatedAt': timestamp,
                'ItemId': item.get('ItemId', str(uuid.uuid4()))
            }
            items_with_metadata.append(item_with_metadata)

        try:
            processed_count = 0
            unprocessed_items = []

            # DynamoDB batch_write_item has a limit of 25 items per request
            for i in range(0, len(items_with_metadata), 25):
                batch_items = items_with_metadata[i:i + 25]

                request_items = {
                    self.table_name: [
                        {'PutRequest': {'Item': item}} for item in batch_items
                    ]
                }

                response = self.dynamodb.batch_write_item(RequestItems=request_items)
                processed_count += len(batch_items)

                # Handle unprocessed items
                unprocessed = response.get('UnprocessedItems', {})
                while unprocessed:
                    response = self.dynamodb.batch_write_item(RequestItems=unprocessed)
                    unprocessed = response.get('UnprocessedItems', {})

                # Collect any final unprocessed items
                if unprocessed:
                    unprocessed_requests = unprocessed.get(self.table_name, [])
                    for req in unprocessed_requests:
                        if 'PutRequest' in req:
                            unprocessed_items.append(req['PutRequest']['Item'])

            logger.info(f"Batch wrote {processed_count} items, {len(unprocessed_items)} unprocessed")

            return {
                'processed': processed_count,
                'unprocessed': unprocessed_items
            }
        except ClientError as e:
            logger.error(f"Error in batch write items: {e}")
            raise


# Convenience functions for common patterns
def get_db_client(table_name: str = None, region_name: str = None) -> DynamoDBUtils:
    """
    Get a DynamoDB utils client.

    Args:
        table_name: Optional table name override.
        region_name: Optional region name override.

    Returns:
        DynamoDBUtils instance.
    """
    return DynamoDBUtils(table_name=table_name, region_name=region_name)


# Example usage patterns for different entity types
class PatientRecord:
    """Helper class for patient record operations."""

    def __init__(self, db_client: DynamoDBUtils):
        self.db = db_client

    def create_patient(self, patient_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new patient record."""
        item = {
            'PK': f'PATIENT#{patient_id}',
            'SK': 'PROFILE',
            'EntityType': 'Patient',
            'PatientId': patient_id,
            **patient_data
        }
        return self.db.create_item(item)

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get a patient by ID."""
        return self.db.get_item(f'PATIENT#{patient_id}', 'PROFILE')

    def update_patient(self, patient_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a patient record."""
        return self.db.update_item(f'PATIENT#{patient_id}', 'PROFILE', updates)

    def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient record."""
        return self.db.delete_item(f'PATIENT#{patient_id}', 'PROFILE')


class MedicalRecord:
    """Helper class for medical record operations."""

    def __init__(self, db_client: DynamoDBUtils):
        self.db = db_client

    def create_medical_record(self, patient_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new medical record for a patient."""
        record_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        item = {
            'PK': f'PATIENT#{patient_id}',
            'SK': f'RECORD#{timestamp}#{record_id}',
            'EntityType': 'MedicalRecord',
            'PatientId': patient_id,
            'RecordId': record_id,
            'RecordDate': timestamp,
            **record_data
        }
        return self.db.create_item(item)

    def get_patient_records(self, patient_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get all medical records for a patient."""
        return self.db.query_items(
            pk=f'PATIENT#{patient_id}',
            sk_condition="begins_with(SK, 'RECORD#')",
            limit=limit,
            scan_index_forward=False  # Most recent first
        )