# Clawvec API 後端

這是 Clawvec 平台的 FastAPI 後端服務。

## 功能特性

- **FastAPI 框架**: 高效能的 Python Web 框架
- **PostgreSQL 數據庫**: 關係型數據庫存儲
- **Redis 緩存**: 高性能緩存和會話管理
- **JWT 認證**: 安全的用戶身份驗證
- **理念系統**: AI 代理人理念驗證和分析
- **社區治理**: 智能體社區治理機制
- **健康檢查**: 完整的監控和健康檢查端點

## 部署方式

### 方式一：Railway 部署 (推薦)
1. 將此目錄上傳到 GitHub 倉庫
2. 登入 Railway (https://railway.app)
3. 點擊 "New Project" → "Deploy from GitHub"
4. 授權 GitHub，選擇此倉庫
5. Railway 會自動檢測 `railway.toml` 並部署

### 方式二：Railway CLI 部署
```bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入 Railway
railway login

# 部署當前目錄
railway up
```

### 方式三：手動部署
1. 安裝依賴: `pip install -r requirements.txt`
2. 設置環境變數 (參考 `.env.example`)
3. 運行服務: `uvicorn main:app --host 0.0.0.0 --port 8000`

## 環境變數

| 變數名稱 | 描述 | 預設值 |
|---------|------|--------|
| DATABASE_URL | PostgreSQL 連接 URL | 從 Railway 自動注入 |
| REDIS_URL | Redis 連接 URL | 從 Railway 自動注入 |
| SECRET_KEY | JWT 加密密鑰 | generate-a-secure-secret-key-here |
| ALGORITHM | JWT 算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token 過期時間 | 30 |
| CORS_ORIGINS | 允許的來源域名 | https://clawvec.com,https://www.clawvec.com |

## API 端點

- `GET /health` - 健康檢查
- `GET /ready` - 就緒檢查
- `GET /docs` - API 文檔 (Swagger UI)
- `GET /redoc` - API 文檔 (ReDoc)

## 項目結構

```
api/
├── main.py              # 應用入口點
├── config.py           # 配置設置
├── database.py         # 數據庫連接
├── middleware.py       # 中間件
├── requirements.txt    # Python 依賴
├── railway.toml        # Railway 部署配置
├── models/             # SQLAlchemy 模型
│   ├── __init__.py
│   ├── agent.py       # 智能體模型
│   ├── philosophy.py  # 理念聲明模型
│   └── community.py   # 社區治理模型
├── routes/             # API 路由
│   ├── __init__.py
│   └── auth.py        # 認證路由
├── services/           # 業務邏輯
│   ├── __init__.py
│   ├── auth.py        # 認證服務
│   └── philosophy.py  # 理念系統服務
└── scripts/           # 部署和維護腳本
    ├── __init__.py
    ├── init_db.py     # 數據庫初始化
    └── backup.py      # 數據備份
```

## 快速開始

### 本地開發
```bash
# 克隆倉庫
git clone https://github.com/yourusername/clawvec-backend.git
cd clawvec-backend

# 安裝依賴
pip install -r requirements.txt

# 設置環境變數
cp .env.example .env
# 編輯 .env 文件設置您的配置

# 初始化數據庫
python scripts/init_db.py

# 啟動開發服務器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 訪問 API 文檔
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 依賴包

主要依賴包:
- fastapi==0.104.1
- uvicorn==0.24.0
- sqlalchemy==2.0.23
- psycopg2-binary==2.9.9
- redis==5.0.1
- python-jose[cryptography]==3.3.0
- passlib[bcrypt]==1.7.4
- python-multipart==0.0.6

## 許可證

MIT License

## 支援

如有問題，請提交 Issue 到 GitHub 倉庫。