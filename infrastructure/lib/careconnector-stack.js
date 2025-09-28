"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CareConnectorStack = void 0;
// lib/careconnector-stack.ts
const cdk = require("aws-cdk-lib");
const dynamodb = require("aws-cdk-lib/aws-dynamodb");
const iam = require("aws-cdk-lib/aws-iam");
const ssm = require("aws-cdk-lib/aws-ssm");
class CareConnectorStack extends cdk.Stack {
    constructor(scope, id, props) {
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
exports.CareConnectorStack = CareConnectorStack;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY2FyZWNvbm5lY3Rvci1zdGFjay5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbImNhcmVjb25uZWN0b3Itc3RhY2sudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQUEsNkJBQTZCO0FBQzdCLG1DQUFtQztBQUNuQyxxREFBcUQ7QUFDckQsMkNBQTJDO0FBQzNDLDJDQUEyQztBQUczQyxNQUFhLGtCQUFtQixTQUFRLEdBQUcsQ0FBQyxLQUFLO0lBQy9DLFlBQVksS0FBZ0IsRUFBRSxFQUFVLEVBQUUsS0FBc0I7UUFDOUQsS0FBSyxDQUFDLEtBQUssRUFBRSxFQUFFLEVBQUUsS0FBSyxDQUFDLENBQUM7UUFFeEIsbURBQW1EO1FBQ25ELE1BQU0sa0JBQWtCLEdBQUcsSUFBSSxRQUFRLENBQUMsS0FBSyxDQUFDLElBQUksRUFBRSxvQkFBb0IsRUFBRTtZQUN4RSxTQUFTLEVBQUUsb0JBQW9CO1lBQy9CLFlBQVksRUFBRTtnQkFDWixJQUFJLEVBQUUsSUFBSTtnQkFDVixJQUFJLEVBQUUsUUFBUSxDQUFDLGFBQWEsQ0FBQyxNQUFNO2FBQ3BDO1lBQ0QsT0FBTyxFQUFFO2dCQUNQLElBQUksRUFBRSxJQUFJO2dCQUNWLElBQUksRUFBRSxRQUFRLENBQUMsYUFBYSxDQUFDLE1BQU07YUFDcEM7WUFDRCxXQUFXLEVBQUUsUUFBUSxDQUFDLFdBQVcsQ0FBQyxlQUFlO1lBQ2pELG1CQUFtQixFQUFFLElBQUk7WUFDekIsVUFBVSxFQUFFLFFBQVEsQ0FBQyxlQUFlLENBQUMsV0FBVztZQUNoRCxhQUFhLEVBQUUsR0FBRyxDQUFDLGFBQWEsQ0FBQyxPQUFPLEVBQUUsa0RBQWtEO1NBQzdGLENBQUMsQ0FBQztRQUVILHdFQUF3RTtRQUN4RSxrQkFBa0IsQ0FBQyx1QkFBdUIsQ0FBQztZQUN6QyxTQUFTLEVBQUUsTUFBTTtZQUNqQixZQUFZLEVBQUU7Z0JBQ1osSUFBSSxFQUFFLFFBQVE7Z0JBQ2QsSUFBSSxFQUFFLFFBQVEsQ0FBQyxhQUFhLENBQUMsTUFBTTthQUNwQztZQUNELE9BQU8sRUFBRTtnQkFDUCxJQUFJLEVBQUUsUUFBUTtnQkFDZCxJQUFJLEVBQUUsUUFBUSxDQUFDLGFBQWEsQ0FBQyxNQUFNO2FBQ3BDO1NBQ0YsQ0FBQyxDQUFDO1FBRUgsa0JBQWtCLENBQUMsdUJBQXVCLENBQUM7WUFDekMsU0FBUyxFQUFFLE1BQU07WUFDakIsWUFBWSxFQUFFO2dCQUNaLElBQUksRUFBRSxRQUFRO2dCQUNkLElBQUksRUFBRSxRQUFRLENBQUMsYUFBYSxDQUFDLE1BQU07YUFDcEM7WUFDRCxPQUFPLEVBQUU7Z0JBQ1AsSUFBSSxFQUFFLFFBQVE7Z0JBQ2QsSUFBSSxFQUFFLFFBQVEsQ0FBQyxhQUFhLENBQUMsTUFBTTthQUNwQztTQUNGLENBQUMsQ0FBQztRQUVILGlDQUFpQztRQUNqQyxNQUFNLG9CQUFvQixHQUFHLElBQUksR0FBRyxDQUFDLElBQUksQ0FBQyxJQUFJLEVBQUUsc0JBQXNCLEVBQUU7WUFDdEUsU0FBUyxFQUFFLElBQUksR0FBRyxDQUFDLGdCQUFnQixDQUFDLG1CQUFtQixDQUFDO1lBQ3hELFdBQVcsRUFBRSw4Q0FBOEM7WUFDM0QsUUFBUSxFQUFFLHNCQUFzQjtTQUNqQyxDQUFDLENBQUM7UUFFSCxpQ0FBaUM7UUFDakMsTUFBTSxjQUFjLEdBQUcsSUFBSSxHQUFHLENBQUMsZUFBZSxDQUFDO1lBQzdDLE1BQU0sRUFBRSxHQUFHLENBQUMsTUFBTSxDQUFDLEtBQUs7WUFDeEIsT0FBTyxFQUFFO2dCQUNQLGtCQUFrQjtnQkFDbEIsa0JBQWtCO2dCQUNsQixxQkFBcUI7Z0JBQ3JCLHFCQUFxQjtnQkFDckIsZ0JBQWdCO2dCQUNoQixlQUFlO2dCQUNmLHVCQUF1QjtnQkFDdkIseUJBQXlCO2FBQzFCO1lBQ0QsU0FBUyxFQUFFO2dCQUNULGtCQUFrQixDQUFDLFFBQVE7Z0JBQzNCLEdBQUcsa0JBQWtCLENBQUMsUUFBUSxVQUFVO2FBQ3pDO1NBQ0YsQ0FBQyxDQUFDO1FBRUgsb0JBQW9CLENBQUMsV0FBVyxDQUFDLGNBQWMsQ0FBQyxDQUFDO1FBRWpELHlEQUF5RDtRQUN6RCxJQUFJLEdBQUcsQ0FBQyxlQUFlLENBQUMsSUFBSSxFQUFFLHdCQUF3QixFQUFFO1lBQ3RELGFBQWEsRUFBRSx3Q0FBd0M7WUFDdkQsV0FBVyxFQUFFLGtCQUFrQixDQUFDLFNBQVM7U0FDMUMsQ0FBQyxDQUFDO1FBRUgsSUFBSSxHQUFHLENBQUMsZUFBZSxDQUFDLElBQUksRUFBRSxZQUFZLEVBQUU7WUFDMUMsYUFBYSxFQUFFLDRCQUE0QjtZQUMzQyxXQUFXLEVBQUUsb0JBQW9CLENBQUMsT0FBTztTQUMxQyxDQUFDLENBQUM7UUFFSCw2QkFBNkI7UUFDN0IsSUFBSSxHQUFHLENBQUMsU0FBUyxDQUFDLElBQUksRUFBRSwwQkFBMEIsRUFBRTtZQUNsRCxLQUFLLEVBQUUsa0JBQWtCLENBQUMsU0FBUztZQUNuQyxXQUFXLEVBQUUsd0NBQXdDO1lBQ3JELFVBQVUsRUFBRSx5QkFBeUI7U0FDdEMsQ0FBQyxDQUFDO1FBRUgsSUFBSSxHQUFHLENBQUMsU0FBUyxDQUFDLElBQUksRUFBRSxlQUFlLEVBQUU7WUFDdkMsS0FBSyxFQUFFLG9CQUFvQixDQUFDLE9BQU87WUFDbkMsV0FBVyxFQUFFLDRDQUE0QztZQUN6RCxVQUFVLEVBQUUsdUJBQXVCO1NBQ3BDLENBQUMsQ0FBQztJQUNMLENBQUM7Q0FDRjtBQWxHRCxnREFrR0MiLCJzb3VyY2VzQ29udGVudCI6WyIvLyBsaWIvY2FyZWNvbm5lY3Rvci1zdGFjay50c1xyXG5pbXBvcnQgKiBhcyBjZGsgZnJvbSAnYXdzLWNkay1saWInO1xyXG5pbXBvcnQgKiBhcyBkeW5hbW9kYiBmcm9tICdhd3MtY2RrLWxpYi9hd3MtZHluYW1vZGInO1xyXG5pbXBvcnQgKiBhcyBpYW0gZnJvbSAnYXdzLWNkay1saWIvYXdzLWlhbSc7XHJcbmltcG9ydCAqIGFzIHNzbSBmcm9tICdhd3MtY2RrLWxpYi9hd3Mtc3NtJztcclxuaW1wb3J0IHsgQ29uc3RydWN0IH0gZnJvbSAnY29uc3RydWN0cyc7XHJcblxyXG5leHBvcnQgY2xhc3MgQ2FyZUNvbm5lY3RvclN0YWNrIGV4dGVuZHMgY2RrLlN0YWNrIHtcclxuICBjb25zdHJ1Y3RvcihzY29wZTogQ29uc3RydWN0LCBpZDogc3RyaW5nLCBwcm9wcz86IGNkay5TdGFja1Byb3BzKSB7XHJcbiAgICBzdXBlcihzY29wZSwgaWQsIHByb3BzKTtcclxuXHJcbiAgICAvLyBTaW5nbGUgRHluYW1vREIgVGFibGUgZm9yIEFsbCBDYXJlQ29ubmVjdG9yIERhdGFcclxuICAgIGNvbnN0IGNhcmVDb25uZWN0b3JUYWJsZSA9IG5ldyBkeW5hbW9kYi5UYWJsZSh0aGlzLCAnQ2FyZUNvbm5lY3RvclRhYmxlJywge1xyXG4gICAgICB0YWJsZU5hbWU6ICdjYXJlY29ubmVjdG9yLW1haW4nLFxyXG4gICAgICBwYXJ0aXRpb25LZXk6IHtcclxuICAgICAgICBuYW1lOiAnUEsnLFxyXG4gICAgICAgIHR5cGU6IGR5bmFtb2RiLkF0dHJpYnV0ZVR5cGUuU1RSSU5HLFxyXG4gICAgICB9LFxyXG4gICAgICBzb3J0S2V5OiB7XHJcbiAgICAgICAgbmFtZTogJ1NLJyxcclxuICAgICAgICB0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyxcclxuICAgICAgfSxcclxuICAgICAgYmlsbGluZ01vZGU6IGR5bmFtb2RiLkJpbGxpbmdNb2RlLlBBWV9QRVJfUkVRVUVTVCxcclxuICAgICAgcG9pbnRJblRpbWVSZWNvdmVyeTogdHJ1ZSxcclxuICAgICAgZW5jcnlwdGlvbjogZHluYW1vZGIuVGFibGVFbmNyeXB0aW9uLkFXU19NQU5BR0VELFxyXG4gICAgICByZW1vdmFsUG9saWN5OiBjZGsuUmVtb3ZhbFBvbGljeS5ERVNUUk9ZLCAvLyBGb3IgaGFja2F0aG9uIC0gY2hhbmdlIHRvIFJFVEFJTiBmb3IgcHJvZHVjdGlvblxyXG4gICAgfSk7XHJcblxyXG4gICAgLy8gQWRkIEdsb2JhbCBTZWNvbmRhcnkgSW5kZXhlcyB1c2luZyB0aGUgYWRkR2xvYmFsU2Vjb25kYXJ5SW5kZXggbWV0aG9kXHJcbiAgICBjYXJlQ29ubmVjdG9yVGFibGUuYWRkR2xvYmFsU2Vjb25kYXJ5SW5kZXgoe1xyXG4gICAgICBpbmRleE5hbWU6ICdHU0kxJyxcclxuICAgICAgcGFydGl0aW9uS2V5OiB7XHJcbiAgICAgICAgbmFtZTogJ0dTSTFQSycsXHJcbiAgICAgICAgdHlwZTogZHluYW1vZGIuQXR0cmlidXRlVHlwZS5TVFJJTkcsXHJcbiAgICAgIH0sXHJcbiAgICAgIHNvcnRLZXk6IHtcclxuICAgICAgICBuYW1lOiAnR1NJMVNLJyxcclxuICAgICAgICB0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyxcclxuICAgICAgfSxcclxuICAgIH0pO1xyXG5cclxuICAgIGNhcmVDb25uZWN0b3JUYWJsZS5hZGRHbG9iYWxTZWNvbmRhcnlJbmRleCh7XHJcbiAgICAgIGluZGV4TmFtZTogJ0dTSTInLFxyXG4gICAgICBwYXJ0aXRpb25LZXk6IHtcclxuICAgICAgICBuYW1lOiAnR1NJMlBLJyxcclxuICAgICAgICB0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyxcclxuICAgICAgfSxcclxuICAgICAgc29ydEtleToge1xyXG4gICAgICAgIG5hbWU6ICdHU0kyU0snLFxyXG4gICAgICAgIHR5cGU6IGR5bmFtb2RiLkF0dHJpYnV0ZVR5cGUuU1RSSU5HLFxyXG4gICAgICB9LFxyXG4gICAgfSk7XHJcblxyXG4gICAgLy8gSUFNIFJvbGUgZm9yIEZsYXNrIEFwcGxpY2F0aW9uXHJcbiAgICBjb25zdCBjYXJlQ29ubmVjdG9yQXBwUm9sZSA9IG5ldyBpYW0uUm9sZSh0aGlzLCAnQ2FyZUNvbm5lY3RvckFwcFJvbGUnLCB7XHJcbiAgICAgIGFzc3VtZWRCeTogbmV3IGlhbS5TZXJ2aWNlUHJpbmNpcGFsKCdlYzIuYW1hem9uYXdzLmNvbScpLFxyXG4gICAgICBkZXNjcmlwdGlvbjogJ0lBTSBSb2xlIGZvciBDYXJlQ29ubmVjdG9yIEZsYXNrIEFwcGxpY2F0aW9uJyxcclxuICAgICAgcm9sZU5hbWU6ICdDYXJlQ29ubmVjdG9yQXBwUm9sZScsXHJcbiAgICB9KTtcclxuXHJcbiAgICAvLyBJQU0gUG9saWN5IGZvciBEeW5hbW9EQiBBY2Nlc3NcclxuICAgIGNvbnN0IGR5bmFtb0RiUG9saWN5ID0gbmV3IGlhbS5Qb2xpY3lTdGF0ZW1lbnQoe1xyXG4gICAgICBlZmZlY3Q6IGlhbS5FZmZlY3QuQUxMT1csXHJcbiAgICAgIGFjdGlvbnM6IFtcclxuICAgICAgICAnZHluYW1vZGI6R2V0SXRlbScsXHJcbiAgICAgICAgJ2R5bmFtb2RiOlB1dEl0ZW0nLFxyXG4gICAgICAgICdkeW5hbW9kYjpVcGRhdGVJdGVtJyxcclxuICAgICAgICAnZHluYW1vZGI6RGVsZXRlSXRlbScsXHJcbiAgICAgICAgJ2R5bmFtb2RiOlF1ZXJ5JyxcclxuICAgICAgICAnZHluYW1vZGI6U2NhbicsXHJcbiAgICAgICAgJ2R5bmFtb2RiOkJhdGNoR2V0SXRlbScsXHJcbiAgICAgICAgJ2R5bmFtb2RiOkJhdGNoV3JpdGVJdGVtJyxcclxuICAgICAgXSxcclxuICAgICAgcmVzb3VyY2VzOiBbXHJcbiAgICAgICAgY2FyZUNvbm5lY3RvclRhYmxlLnRhYmxlQXJuLFxyXG4gICAgICAgIGAke2NhcmVDb25uZWN0b3JUYWJsZS50YWJsZUFybn0vaW5kZXgvKmAsXHJcbiAgICAgIF0sXHJcbiAgICB9KTtcclxuXHJcbiAgICBjYXJlQ29ubmVjdG9yQXBwUm9sZS5hZGRUb1BvbGljeShkeW5hbW9EYlBvbGljeSk7XHJcblxyXG4gICAgLy8gU3RvcmUgY29uZmlndXJhdGlvbiBpbiBQYXJhbWV0ZXIgU3RvcmUgZm9yIGVhc3kgYWNjZXNzXHJcbiAgICBuZXcgc3NtLlN0cmluZ1BhcmFtZXRlcih0aGlzLCAnQ2FyZUNvbm5lY3RvclRhYmxlTmFtZScsIHtcclxuICAgICAgcGFyYW1ldGVyTmFtZTogJy9jYXJlZmxvdy9keW5hbW9kYi9wYXRpZW50cy10YWJsZS1uYW1lJyxcclxuICAgICAgc3RyaW5nVmFsdWU6IGNhcmVDb25uZWN0b3JUYWJsZS50YWJsZU5hbWUsXHJcbiAgICB9KTtcclxuXHJcbiAgICBuZXcgc3NtLlN0cmluZ1BhcmFtZXRlcih0aGlzLCAnQXBwUm9sZUFybicsIHtcclxuICAgICAgcGFyYW1ldGVyTmFtZTogJy9jYXJlZmxvdy9pYW0vYXBwLXJvbGUtYXJuJyxcclxuICAgICAgc3RyaW5nVmFsdWU6IGNhcmVDb25uZWN0b3JBcHBSb2xlLnJvbGVBcm4sXHJcbiAgICB9KTtcclxuXHJcbiAgICAvLyBPdXRwdXRzIGZvciBlYXN5IHJlZmVyZW5jZVxyXG4gICAgbmV3IGNkay5DZm5PdXRwdXQodGhpcywgJ0NhcmVDb25uZWN0b3JUYWJsZU91dHB1dCcsIHtcclxuICAgICAgdmFsdWU6IGNhcmVDb25uZWN0b3JUYWJsZS50YWJsZU5hbWUsXHJcbiAgICAgIGRlc2NyaXB0aW9uOiAnRHluYW1vREIgQ2FyZUNvbm5lY3RvciBNYWluIFRhYmxlIE5hbWUnLFxyXG4gICAgICBleHBvcnROYW1lOiAnQ2FyZUNvbm5lY3Rvci1NYWluVGFibGUnLFxyXG4gICAgfSk7XHJcblxyXG4gICAgbmV3IGNkay5DZm5PdXRwdXQodGhpcywgJ0FwcFJvbGVPdXRwdXQnLCB7XHJcbiAgICAgIHZhbHVlOiBjYXJlQ29ubmVjdG9yQXBwUm9sZS5yb2xlQXJuLFxyXG4gICAgICBkZXNjcmlwdGlvbjogJ0lBTSBSb2xlIEFSTiBmb3IgQ2FyZUNvbm5lY3RvciBBcHBsaWNhdGlvbicsXHJcbiAgICAgIGV4cG9ydE5hbWU6ICdDYXJlQ29ubmVjdG9yLUFwcFJvbGUnLFxyXG4gICAgfSk7XHJcbiAgfVxyXG59Il19