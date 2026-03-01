#!/bin/bash
# Railway 部署腳本
# 使用方式: ./deploy_railway.sh railway_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

set -e  # 遇到錯誤時退出

TOKEN=$1

if [ -z "$TOKEN" ]; then
    echo "❌ 錯誤: 請提供 Railway token 作為參數"
    echo "使用方式: $0 railway_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    exit 1
fi

echo "🚀 開始 Clawvec 後端部署到 Railway..."

# 設置環境變數
export RAILWAY_TOKEN=$TOKEN

# 檢查 Railway CLI 是否安裝
echo "檢查 Railway CLI..."
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI 未安裝，正在安裝..."
    npm install -g @railway/cli
fi

# 測試 token
echo "測試 Railway token..."
railway whoami
if [ $? -ne 0 ]; then
    echo "❌ Token 無效，請檢查 token 格式和權限"
    exit 1
fi

echo "✅ Token 驗證成功"

# 檢查當前目錄
echo "當前目錄: $(pwd)"

# 檢查 railway.toml 是否存在
if [ ! -f "railway.toml" ]; then
    echo "❌ railway.toml 未找到"
    exit 1
fi

echo "✅ railway.toml 配置找到"

# 檢查 requirements.txt 是否存在
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 未找到"
    exit 1
fi

echo "✅ requirements.txt 找到"

# 檢查 main.py 是否存在
if [ ! -f "main.py" ]; then
    echo "❌ main.py 未找到"
    exit 1
fi

echo "✅ main.py 找到"

# 部署到 Railway
echo "開始部署到 Railway..."
railway up --service app --detach

if [ $? -ne 0 ]; then
    echo "❌ 部署失敗"
    exit 1
fi

echo "✅ 部署成功啟動"

# 獲取部署狀態
echo "獲取部署狀態..."
sleep 10
railway status

echo "部署完成！"
echo "下一步: 在 Railway Dashboard 中配置 api.clawvec.com 域名"