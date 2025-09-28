// lib/careflow-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';

export class CareFlowStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB Table for Patient Records
    const patientsTable = new dynamodb.Table(this, 'PatientsTable', {
      tableName: 'careflow-patients',
      partitionKey: {
        name: 'user_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For hackathon - change to RETAIN for production
      
      // Global Secondary Indexes for querying
      globalSecondaryIndexes: [
        {
          indexName: 'email-index',
          partitionKey: {
            name: 'email',
            type: dynamodb.AttributeType.STRING,
          },
        },
        {
          indexName: 'provider-index',
          partitionKey: {
            name: 'primary_provider_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'created_at',
            type: dynamodb.AttributeType.STRING,
          },
        },
      ],
    });

    // DynamoDB Table for Appointments
    const appointmentsTable = new dynamodb.Table(this, 'AppointmentsTable', {
      tableName: 'careflow-appointments',
      partitionKey: {
        name: 'appointment_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'patient_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      
      globalSecondaryIndexes: [
        {
          indexName: 'patient-appointments',
          partitionKey: {
            name: 'patient_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'appointment_date',
            type: dynamodb.AttributeType.STRING,
          },
        },
        {
          indexName: 'provider-schedule',
          partitionKey: {
            name: 'provider_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'appointment_date',
            type: dynamodb.AttributeType.STRING,
          },
        },
      ],
    });

    // DynamoDB Table for Providers/Hospitals
    const providersTable = new dynamodb.Table(this, 'ProvidersTable', {
      tableName: 'careflow-providers',
      partitionKey: {
        name: 'provider_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      
      globalSecondaryIndexes: [
        {
          indexName: 'location-index',
          partitionKey: {
            name: 'location',
            type: dynamodb.AttributeType.STRING,
          },
        },
        {
          indexName: 'specialty-index',
          partitionKey: {
            name: 'specialty',
            type: dynamodb.AttributeType.STRING,
          },
        },
      ],
    });

    // DynamoDB Table for Messages/Communications
    const messagesTable = new dynamodb.Table(this, 'MessagesTable', {
      tableName: 'careflow-messages',
      partitionKey: {
        name: 'conversation_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'timestamp',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      
      globalSecondaryIndexes: [
        {
          indexName: 'patient-messages',
          partitionKey: {
            name: 'patient_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'timestamp',
            type: dynamodb.AttributeType.STRING,
          },
        },
      ],
    });

    // IAM Role for Flask Application
    const flaskAppRole = new iam.Role(this, 'CareFlowAppRole', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      description: 'IAM Role for CareFlow Flask Application',
      roleName: 'CareFlowAppRole',
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
        patientsTable.tableArn,
        `${patientsTable.tableArn}/index/*`,
        appointmentsTable.tableArn,
        `${appointmentsTable.tableArn}/index/*`,
        providersTable.tableArn,
        `${providersTable.tableArn}/index/*`,
        messagesTable.tableArn,
        `${messagesTable.tableArn}/index/*`,
      ],
    });

    flaskAppRole.addToPolicy(dynamoDbPolicy);

    // Store configuration in Parameter Store for easy access
    new ssm.StringParameter(this, 'PatientsTableName', {
      parameterName: '/careflow/dynamodb/patients-table-name',
      stringValue: patientsTable.tableName,
    });

    new ssm.StringParameter(this, 'AppointmentsTableName', {
      parameterName: '/careflow/dynamodb/appointments-table-name',
      stringValue: appointmentsTable.tableName,
    });

    new ssm.StringParameter(this, 'ProvidersTableName', {
      parameterName: '/careflow/dynamodb/providers-table-name',
      stringValue: providersTable.tableName,
    });

    new ssm.StringParameter(this, 'MessagesTableName', {
      parameterName: '/careflow/dynamodb/messages-table-name',
      stringValue: messagesTable.tableName,
    });

    new ssm.StringParameter(this, 'AppRoleArn', {
      parameterName: '/careflow/iam/app-role-arn',
      stringValue: flaskAppRole.roleArn,
    });

    // Outputs for easy reference
    new cdk.CfnOutput(this, 'PatientsTableOutput', {
      value: patientsTable.tableName,
      description: 'DynamoDB Patients Table Name',
      exportName: 'CareFlow-PatientsTable',
    });

    new cdk.CfnOutput(this, 'AppointmentsTableOutput', {
      value: appointmentsTable.tableName,
      description: 'DynamoDB Appointments Table Name',
      exportName: 'CareFlow-AppointmentsTable',
    });

    new cdk.CfnOutput(this, 'ProvidersTableOutput', {
      value: providersTable.tableName,
      description: 'DynamoDB Providers Table Name',
      exportName: 'CareFlow-ProvidersTable',
    });

    new cdk.CfnOutput(this, 'MessagesTableOutput', {
      value: messagesTable.tableName,
      description: 'DynamoDB Messages Table Name',
      exportName: 'CareFlow-MessagesTable',
    });

    new cdk.CfnOutput(this, 'AppRoleOutput', {
      value: flaskAppRole.roleArn,
      description: 'IAM Role ARN for CareFlow Application',
      exportName: 'CareFlow-AppRole',
    });
  }
}