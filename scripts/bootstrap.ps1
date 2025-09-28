# CareFlow CDK Bootstrap Script for Windows
param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1"
)

Write-Host "CareFlow Infrastructure Bootstrap" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if AWS CLI is installed
try {
    $awsVersion = aws --version
    Write-Host "[SUCCESS] AWS CLI found: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] AWS CLI is not installed. Please install it first." -ForegroundColor Red
    Write-Host "        Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html" -ForegroundColor Yellow
    exit 1
}

# Check if CDK is installed
try {
    $cdkVersion = cdk --version
    Write-Host "[SUCCESS] AWS CDK found: $cdkVersion" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Installing AWS CDK globally..." -ForegroundColor Yellow
    npm install -g aws-cdk
}

# Verify AWS credentials
Write-Host "[INFO] Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    $accountId = $identity.Account
    Write-Host "[SUCCESS] AWS Account: $accountId" -ForegroundColor Green
    Write-Host "[SUCCESS] Region: $Region" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] AWS credentials not configured properly." -ForegroundColor Red
    Write-Host "        Run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Set environment variables
$env:CDK_DEFAULT_ACCOUNT = $accountId
$env:CDK_DEFAULT_REGION = $Region

# Navigate to infrastructure directory
if (-not (Test-Path "infrastructure")) {
    Write-Host "[ERROR] Infrastructure directory not found. Make sure you're in the project root." -ForegroundColor Red
    exit 1
}

Set-Location infrastructure

# Install dependencies
Write-Host "[INFO] Installing CDK dependencies..." -ForegroundColor Yellow
npm install

# Build TypeScript
Write-Host "[INFO] Building TypeScript..." -ForegroundColor Yellow
npm run build

# Bootstrap CDK (only needed once per account/region)
Write-Host "[INFO] Bootstrapping CDK..." -ForegroundColor Yellow
try {
    cdk bootstrap "aws://$accountId/$Region"
    Write-Host "[SUCCESS] Bootstrap complete!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Bootstrap failed. Check your AWS permissions." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[SUCCESS] Bootstrap successful!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the infrastructure code in infrastructure/lib/careflow-stack.ts"
Write-Host "2. Deploy with: .\scripts\deploy.ps1"
Write-Host "3. Access table names from AWS Parameter Store or CloudFormation outputs"

# Return to root directory
Set-Location ..