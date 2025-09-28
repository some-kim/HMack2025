# Cleanup Script for Windows
param(
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

Write-Host "🧹 CareConnector Infrastructure Cleanup" -ForegroundColor Red
Write-Host "===================================" -ForegroundColor Red

if (-not $Force) {
    $confirmation = Read-Host "⚠️  This will DESTROY all CareConnector infrastructure and data. Continue? (type 'DELETE' to confirm)"
    if ($confirmation -ne 'DELETE') {
        Write-Host "❌ Cleanup cancelled." -ForegroundColor Green
        exit 0
    }
}

# Navigate to infrastructure directory
if (Test-Path "infrastructure") {
    Set-Location infrastructure
    
    Write-Host "🗑️  Destroying CDK stack..." -ForegroundColor Yellow
    try {
        cdk destroy --force
        Write-Host "✅ Stack destroyed successfully." -ForegroundColor Green
    } catch {
        Write-Host "❌ Error destroying stack." -ForegroundColor Red
    }
    
    Set-Location ..
} else {
    Write-Host "⚠️  Infrastructure directory not found." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🧹 Cleanup options:" -ForegroundColor Yellow
Write-Host "- CDK Bootstrap resources (S3 bucket, etc.) are preserved"
Write-Host "- To remove CDK bootstrap: aws s3 rm s3://cdktoolkit-stagingbucket-* --recursive"
Write-Host "- Then: aws cloudformation delete-stack --stack-name CDKToolkit"