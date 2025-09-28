#!/bin/bash

# CareFlow CDK Deployment Script
set -e

echo "🏥 CareFlow Infrastructure Deployment"
echo "===================================="

# Navigate to infrastructure directory
cd infrastructure

# Build TypeScript
echo "🔨 Building TypeScript..."
npm run build

# Show what will be deployed
echo "📋 Reviewing changes..."
npx cdk diff

# Ask for confirmation
read -p "🚀 Deploy these changes? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 1
fi

# Deploy the stack
echo "🚀 Deploying CareFlow infrastructure..."
npx cdk deploy --require-approval never

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Infrastructure Summary:"
echo "========================="

# Get outputs from CloudFormation
STACK_NAME="CareFlowStack"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey!=`CDKMetadata`].[OutputKey,OutputValue,Description]' \
    --output table

echo ""
echo "🔑 Environment Variables for Flask App:"
echo "======================================="
echo "PATIENTS_TABLE_NAME=$(aws ssm get-parameter --name /careflow/dynamodb/patients-table-name --query Parameter.Value --output text)"
echo "APPOINTMENTS_TABLE_NAME=$(aws ssm get-parameter --name /careflow/dynamodb/appointments-table-name --query Parameter.Value --output text)"
echo "PROVIDERS_TABLE_NAME=$(aws ssm get-parameter --name /careflow/dynamodb/providers-table-name --query Parameter.Value --output text)"
echo "MESSAGES_TABLE_NAME=$(aws ssm get-parameter --name /careflow/dynamodb/messages-table-name --query Parameter.Value --output text)"
echo "APP_ROLE_ARN=$(aws ssm get-parameter --name /careflow/iam/app-role-arn --query Parameter.Value --output text)"
echo ""
echo "🎉 Ready to connect your Flask application!"