# Railway 部署腳本
# 使用方式: .\deploy_railway.ps1 -Token "railway_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

param(
    [Parameter(Mandatory=$true)]
    [string]$Token
)

Write-Host "🚀 開始 Clawvec 後端部署到 Railway..." -ForegroundColor Green

# 設置環境變數
$env:RAILWAY_TOKEN = $Token

# 檢查 Railway CLI 是否安裝
Write-Host "檢查 Railway CLI..." -ForegroundColor Yellow
railway --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Railway CLI 未安裝，正在安裝..." -ForegroundColor Red
    npm install -g @railway/cli
}

# 測試 token
Write-Host "測試 Railway token..." -ForegroundColor Yellow
railway whoami
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Token 無效，請檢查 token 格式和權限" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Token 驗證成功" -ForegroundColor Green

# 檢查當前目錄
$currentDir = Get-Location
Write-Host "當前目錄: $currentDir" -ForegroundColor Cyan

# 檢查 railway.toml 是否存在
if (-not (Test-Path "railway.toml")) {
    Write-Host "❌ railway.toml 未找到" -ForegroundColor Red
    exit 1
}

Write-Host "✅ railway.toml 配置找到" -ForegroundColor Green

# 檢查 requirements.txt 是否存在
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ requirements.txt 未找到" -ForegroundColor Red
    exit 1
}

Write-Host "✅ requirements.txt 找到" -ForegroundColor Green

# 檢查 main.py 是否存在
if (-not (Test-Path "main.py")) {
    Write-Host "❌ main.py 未找到" -ForegroundColor Red
    exit 1
}

Write-Host "✅ main.py 找到" -ForegroundColor Green

# 部署到 Railway
Write-Host "開始部署到 Railway..." -ForegroundColor Yellow
railway up --service app --detach

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 部署失敗" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 部署成功啟動" -ForegroundColor Green

# 獲取部署狀態
Write-Host "獲取部署狀態..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
railway status

Write-Host "部署完成！" -ForegroundColor Green
Write-Host "下一步: 在 Railway Dashboard 中配置 api.clawvec.com 域名" -ForegroundColor Cyan