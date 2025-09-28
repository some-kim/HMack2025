// lib/careconnector-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';

export class CareConnectorStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB Table for Patient Records
    const patientsTable = new dynamodb.Table(this, 'PatientsTable', {
      tableName: 'careconnector-patients',
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
      tableName: 'careconnector-appointments',
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
      tableName: 'careconnector-providers',
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
      tableName: 'careconnector-messages',
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
    const flaskAppRole = new iam.Role(this, 'CareConnectorAppRole', {
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
      parameterName: '/careconnector/dynamodb/patients-table-name',
      stringValue: patientsTable.tableName,
    });

    new ssm.StringParameter(this, 'AppointmentsTableName', {
      parameterName: '/careconnector/dynamodb/appointments-table-name',
      stringValue: appointmentsTable.tableName,
    });

    new ssm.StringParameter(this, 'ProvidersTableName', {
      parameterName: '/careconnector/dynamodb/providers-table-name',
      stringValue: providersTable.tableName,
    });

    new ssm.StringParameter(this, 'MessagesTableName', {
      parameterName: '/careconnector/dynamodb/messages-table-name',
      stringValue: messagesTable.tableName,
    });

    new ssm.StringParameter(this, 'AppRoleArn', {
      parameterName: '/careconnector/iam/app-role-arn',
      stringValue: flaskAppRole.roleArn,
    });

    // Outputs for easy reference
    new cdk.CfnOutput(this, 'PatientsTableOutput', {
      value: patientsTable.tableName,
      description: 'DynamoDB Patients Table Name',
      exportName: 'CareConnector-PatientsTable',
    });

    new cdk.CfnOutput(this, 'AppointmentsTableOutput', {
      value: appointmentsTable.tableName,
      description: 'DynamoDB Appointments Table Name',
      exportName: 'CareConnector-AppointmentsTable',
    });

    new cdk.CfnOutput(this, 'ProvidersTableOutput', {
      value: providersTable.tableName,
      description: 'DynamoDB Providers Table Name',
      exportName: 'CareConnector-ProvidersTable',
    });

    new cdk.CfnOutput(this, 'MessagesTableOutput', {
      value: messagesTable.tableName,
      description: 'DynamoDB Messages Table Name',
      exportName: 'CareConnector-MessagesTable',
    });

    new cdk.CfnOutput(this, 'AppRoleOutput', {
      value: flaskAppRole.roleArn,
      description: 'IAM Role ARN for CareConnector Application',
      exportName: 'CareConnector-AppRole',
    });
  }
}