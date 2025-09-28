#!/bin/bash

# CareFlow CDK Bootstrap Script
set -e

echo "🏥 CareFlow Infrastructure Bootstrap"
echo "=================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    echo "   Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if CDK is installed globally
if ! command -v cdk &> /dev/null; then
    echo "📦 Installing AWS CDK globally..."
    npm install -g aws-cdk
fi

# Verify AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured properly."
    echo "   Run: aws configure"
    exit 1
fi

# Get account and region info
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
REGION=${REGION:-us-east-1}

echo "✅ AWS Account: $ACCOUNT_ID"
echo "✅ Region: $REGION"

# Navigate to infrastructure directory
cd ../infrastructure

# Install dependencies
echo "📦 Installing CDK dependencies..."
npm install

# Bootstrap CDK (only needed once per account/region)
echo "🚀 Bootstrapping CDK..."
npx cdk bootstrap aws://$ACCOUNT_ID/$REGION

echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "Next steps:"
echo "1. Review the infrastructure code in infrastructure/lib/careconnector-stack.ts"
echo "2. Deploy with: ./scripts/deploy.sh"
echo "3. Access table names from AWS Parameter Store or CloudFormation outputs"