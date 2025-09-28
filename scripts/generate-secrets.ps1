# Generate Secure Secrets Script for Windows

Write-Host "🔐 Generating secure secrets for CareConnector..." -ForegroundColor Green

# Generate Flask secret key using Python
try {
    $flaskSecret = python -c "import secrets; print(secrets.token_urlsafe(32))"
    
    Write-Host "🔑 Generated Flask SECRET_KEY:" -ForegroundColor Yellow
    Write-Host "SECRET_KEY=$flaskSecret" -ForegroundColor Cyan
    Write-Host ""
    
    # Update backend .env with generated secret
    $backendEnvPath = "backend\.env"
    if (Test-Path $backendEnvPath) {
        $content = Get-Content $backendEnvPath
        $content = $content -replace "SECRET_KEY=.*", "SECRET_KEY=$flaskSecret"
        $content | Out-File -FilePath $backendEnvPath -Encoding UTF8
        Write-Host "✅ Updated backend\.env with new SECRET_KEY" -ForegroundColor Green
    } else {
        Write-Host "⚠️  backend\.env not found. Please create it first." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Python not found. Please install Python to generate secrets." -ForegroundColor Red
    Write-Host "   Manual SECRET_KEY: $(New-Guid)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Manual setup required:" -ForegroundColor Yellow
Write-Host "========================" -ForegroundColor Yellow
Write-Host "1. Auth0 Domain: Get from Auth0 Dashboard > Applications > Your App"
Write-Host "2. Auth0 Client ID: Get from Auth0 Dashboard > Applications > Your App"
Write-Host "3. Auth0 Client Secret: Get from Auth0 Dashboard > Applications > Your App"
Write-Host "4. AgentMail API Key: Get from AgentMail Dashboard > API Keys"
Write-Host ""
Write-Host "5. Update these values in:" -ForegroundColor Yellow
Write-Host "   - frontend\.env (REACT_APP_AUTH0_*)"
Write-Host "   - backend\.env (AUTH0_* and AGENTMAIL_*)"