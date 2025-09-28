// lib/careconnector-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';

export class CareConnectorStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Single DynamoDB Table for All CareConnector Data
    const careConnectorTable = new dynamodb.Table(this, 'CareConnectorTable', {
      tableName: 'careconnector-main',
      partitionKey: {
        name: 'PK',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'SK',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For hackathon - change to RETAIN for production
    });

    // Add Global Secondary Indexes using the addGlobalSecondaryIndex method
    careConnectorTable.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: {
        name: 'GSI1PK',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'GSI1SK',
        type: dynamodb.AttributeType.STRING,
      },
    });

    careConnectorTable.addGlobalSecondaryIndex({
      indexName: 'GSI2',
      partitionKey: {
        name: 'GSI2PK',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'GSI2SK',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // IAM Role for Flask Application
    const careConnectorAppRole = new iam.Role(this, 'CareConnectorAppRole', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      description: 'IAM Role for CareConnector Flask Application',
      roleName: 'CareConnectorAppRole',
    });

    // IAM Policy for DynamoDB Access
    const dynamoDbPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'dynamodb:GetItem',
        'dynamodb:PutItem',
        'dynamodb:UpdateItem',
        'dynamodb:DeleteItem',
        'dynamodb:Query',
        'dynamodb:Scan',
        'dynamodb:BatchGetItem',
        'dynamodb:BatchWriteItem',
      ],
      resources: [
        careConnectorTable.tableArn,
        `${careConnectorTable.tableArn}/index/*`,
      ],
    });

    careConnectorAppRole.addToPolicy(dynamoDbPolicy);

    // Store configuration in Parameter Store for easy access
    new ssm.StringParameter(this, 'CareConnectorTableName', {
      parameterName: '/careflow/dynamodb/patients-table-name',
      stringValue: careConnectorTable.tableName,
    });

    new ssm.StringParameter(this, 'AppRoleArn', {
      parameterName: '/careflow/iam/app-role-arn',
      stringValue: careConnectorAppRole.roleArn,
    });

    // Outputs for easy reference
    new cdk.CfnOutput(this, 'CareConnectorTableOutput', {
      value: careConnectorTable.tableName,
      description: 'DynamoDB CareConnector Main Table Name',
      exportName: 'CareConnector-MainTable',
    });

    new cdk.CfnOutput(this, 'AppRoleOutput', {
      value: careConnectorAppRole.roleArn,
      description: 'IAM Role ARN for CareConnector Application',
      exportName: 'CareConnector-AppRole',
    });
  }
}