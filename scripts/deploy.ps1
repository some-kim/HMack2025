# CareConnector CDK Deployment Script for Windows
param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-2",
    
    [Parameter(Mandatory=$false)]
    [switch]$AutoApprove = $false
)

Write-Host "CareConnector Infrastructure Deployment" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Check if bootstrap was run
try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    $accountId = $identity.Account
    
    # Set environment variables
    $env:CDK_DEFAULT_ACCOUNT = $accountId
    $env:CDK_DEFAULT_REGION = $Region
} catch {
    Write-Host "AWS credentials not configured. Run bootstrap.ps1 first." -ForegroundColor Red
    exit 1
}

# Navigate to infrastructure directory
if (-not (Test-Path "infrastructure")) {
    Write-Host "Infrastructure directory not found." -ForegroundColor Red
    exit 1
}

Set-Location infrastructure

# Build TypeScript
Write-Host "Building TypeScript..." -ForegroundColor Yellow
try {
    npm run build
} catch {
    Write-Host "TypeScript build failed." -ForegroundColor Red
    exit 1
}

# Show what will be deployed
Write-Host "Reviewing changes..." -ForegroundColor Yellow
cdk diff

if (-not $AutoApprove) {
    # Ask for confirmation
    $confirmation = Read-Host "Deploy these changes? (y/N)"
    if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
        Write-Host "Deployment cancelled." -ForegroundColor Red
        Set-Location ..
        exit 1
    }
}

# Deploy the stack
Write-Host "Deploying CareConnector infrastructure..." -ForegroundColor Yellow
try {
    if ($AutoApprove) {
        cdk deploy --require-approval never
    } else {
        cdk deploy
    }
} catch {
    Write-Host "Deployment failed." -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Infrastructure Summary:" -ForegroundColor Yellow
Write-Host "=========================" -ForegroundColor Yellow

# Get outputs from CloudFormation
try {
    $outputs = aws cloudformation describe-stacks --stack-name CareConnectorStack --query 'Stacks[0].Outputs[?OutputKey!=`CDKMetadata`].[OutputKey,OutputValue,Description]' --output table
    Write-Host $outputs
} catch {
    Write-Host "Could not retrieve stack outputs." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Environment Variables for Flask App:" -ForegroundColor Yellow
Write-Host "=======================================" -ForegroundColor Yellow

try {
    $patientsTable = aws ssm get-parameter --name /careflow/dynamodb/patients-table-name --query Parameter.Value --output text 2>$null
    $appRoleArn = aws ssm get-parameter --name /careflow/iam/app-role-arn --query Parameter.Value --output text 2>$null

    Write-Host "PATIENTS_TABLE_NAME=$patientsTable"
    Write-Host "APP_ROLE_ARN=$appRoleArn"
    Write-Host "AWS_DEFAULT_REGION=$Region"
} catch {
    Write-Host "Could not retrieve parameter store values." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Ready to connect your Flask application!" -ForegroundColor Green

# Return to root directory
Set-Location ..