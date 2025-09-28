# Environment Setup Script for Windows
param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-2"
)

Write-Host "🔧 Setting up CareConnector environment variables..." -ForegroundColor Green

# Check if AWS CLI is available
try {
    aws --version | Out-Null
} catch {
    Write-Host "❌ AWS CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Get AWS account info
try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    $accountId = $identity.Account
} catch {
    Write-Host "❌ Unable to get AWS account info. Please configure AWS CLI." -ForegroundColor Red
    exit 1
}

Write-Host "✅ AWS Account: $accountId" -ForegroundColor Green
Write-Host "✅ Region: $Region" -ForegroundColor Green

# Update infrastructure .env
$infraEnvContent = @"
# AWS Configuration
AWS_PROFILE=default
AWS_DEFAULT_REGION=$Region
CDK_DEFAULT_ACCOUNT=$accountId
CDK_DEFAULT_REGION=$Region

# CDK Configuration
CDK_NEW_BOOTSTRAP=1
CDK_TOOLKIT_STACK_NAME=CDKToolkit

# Stack Configuration
STACK_NAME=CareConnectorStack
ENVIRONMENT=development
PROJECT_NAME=CareConnector
TEAM_NAME=Hackathon
"@

$infraEnvContent | Out-File -FilePath "infrastructure\.env" -Encoding UTF8
Write-Host "✅ Infrastructure .env updated" -ForegroundColor Green

# Try to get table names from Parameter Store (if stack is deployed)
Write-Host "🔍 Checking for deployed infrastructure..." -ForegroundColor Yellow

try {
    $patientsTable = aws ssm get-parameter --name /careconnector/dynamodb/patients-table-name --query Parameter.Value --output text 2>$null
    $appointmentsTable = aws ssm get-parameter --name /careconnector/dynamodb/appointments-table-name --query Parameter.Value --output text 2>$null
    $providersTable = aws ssm get-parameter --name /careconnector/dynamodb/providers-table-name --query Parameter.Value --output text 2>$null
    $messagesTable = aws ssm get-parameter --name /careconnector/dynamodb/messages-table-name --query Parameter.Value --output text 2>$null
    
    if ($patientsTable -and $patientsTable -ne "None") {
        Write-Host "✅ Found deployed tables" -ForegroundColor Green
    } else {
        $patientsTable = "careconnector-patients"
        $appointmentsTable = "careconnector-appointments"
        $providersTable = "careconnector-providers"
        $messagesTable = "careconnector-messages"
        Write-Host "⚠️  Using default table names (deploy infrastructure first)" -ForegroundColor Yellow
    }
} catch {
    $patientsTable = "careconnector-patients"
    $appointmentsTable = "careconnector-appointments"
    $providersTable = "careconnector-providers"
    $messagesTable = "careconnector-messages"
    Write-Host "⚠️  Using default table names" -ForegroundColor Yellow
}

# Update backend .env with actual table names
Write-Host "📝 Updating backend environment with table names..." -ForegroundColor Yellow

$backendEnvPath = "backend\.env"
if (-not (Test-Path $backendEnvPath)) {
    # Create backend .env if it doesn't exist
    $backendEnvContent = @"
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-super-secret-key-for-development

# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=https://your-api-identifier
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret

# AWS Configuration
AWS_DEFAULT_REGION=$Region

# DynamoDB Table Names
PATIENTS_TABLE_NAME=$patientsTable
APPOINTMENTS_TABLE_NAME=$appointmentsTable
PROVIDERS_TABLE_NAME=$providersTable
MESSAGES_TABLE_NAME=$messagesTable

# AgentMail Configuration
AGENTMAIL_API_KEY=your-agentmail-api-key
AGENTMAIL_BASE_URL=https://api.agentmail.com

# CORS Configuration
CORS_ORIGINS=http://localhost:3000
"@

    $backendEnvContent | Out-File -FilePath $backendEnvPath -Encoding UTF8
    Write-Host "✅ Created backend .env file" -ForegroundColor Green
} else {
    # Update existing .env file
    $content = Get-Content $backendEnvPath
    $content = $content -replace "PATIENTS_TABLE_NAME=.*", "PATIENTS_TABLE_NAME=$patientsTable"
    $content = $content -replace "APPOINTMENTS_TABLE_NAME=.*", "APPOINTMENTS_TABLE_NAME=$appointmentsTable"
    $content = $content -replace "PROVIDERS_TABLE_NAME=.*", "PROVIDERS_TABLE_NAME=$providersTable"
    $content = $content -replace "MESSAGES_TABLE_NAME=.*", "MESSAGES_TABLE_NAME=$messagesTable"
    $content = $content -replace "AWS_DEFAULT_REGION=.*", "AWS_DEFAULT_REGION=$Region"
    
    $content | Out-File -FilePath $backendEnvPath -Encoding UTF8
    Write-Host "✅ Updated backend .env file" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Yellow
Write-Host "===========" -ForegroundColor Yellow
Write-Host "Patients Table: $patientsTable"
Write-Host "Appointments Table: $appointmentsTable"
Write-Host "Providers Table: $providersTable"
Write-Host "Messages Table: $messagesTable"
Write-Host ""
Write-Host "🔧 Next steps:" -ForegroundColor Yellow
Write-Host "1. Update Auth0 credentials in frontend\.env and backend\.env"
Write-Host "2. Add AgentMail API key to backend\.env"
Write-Host "3. Run: .\scripts\generate-secrets.ps1"
Write-Host ""