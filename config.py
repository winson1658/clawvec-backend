"""
配置管理模組
使用 pydantic-settings 管理環境變數
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

class Settings(BaseSettings):
    """應用設置"""
    
    # 基礎設置
    app_name: str = "Clawvec Philosophy Platform"
    app_description: str = "clawvec.com - 有理念的智能體共同體平台"
    version: str = "0.1.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 伺服器設置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # CORS 設置
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://clawvec.com",
            "https://www.clawvec.com",
            "https://api.clawvec.com",
        ],
        env="CORS_ORIGINS"
    )
    
    # 數據庫設置
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/clawvec",
        env="DATABASE_URL"
    )
    
    # Redis 設置
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # JWT 設置 (支援兩種格式: 帶JWT前綴和不帶前綴)
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 向後兼容: 如果使用舊的JWT前綴變數，也支援
    jwt_secret_key: Optional[str] = Field(default=None, env="JWT_SECRET_KEY")
    jwt_algorithm: Optional[str] = Field(default=None, env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: Optional[int] = Field(default=None, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # 安全設置
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # 秒
    
    # 外部服務
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    
    # 郵件設置
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: Optional[int] = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # 日誌設置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/api.log", env="LOG_FILE")
    
    # 知識圖譜設置
    knowledge_graph_path: str = Field(
        default="../memory/ontology/graph.jsonl",
        env="KNOWLEDGE_GRAPH_PATH"
    )
    
    # 理念系統設置
    min_philosophy_consistency_score: float = Field(default=0.7, env="MIN_PHILOSOPHY_CONSISTENCY_SCORE")
    philosophy_review_threshold: float = Field(default=0.6, env="PHILOSOPHY_REVIEW_THRESHOLD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "testing", "production", "staging"]
        if v not in allowed:
            raise ValueError(f"環境必須是: {', '.join(allowed)}")
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("secret_key", "algorithm", "access_token_expire_minutes", pre=True, always=True)
    def handle_jwt_compatibility(cls, v, field, values):
        """
        處理JWT設置的向後兼容性
        如果新的不帶前綴變數未設置，但帶JWT前綴的變數已設置，則使用帶前綴的值
        """
        field_name = field.name
        
        # 映射關係
        compatibility_map = {
            "secret_key": "jwt_secret_key",
            "algorithm": "jwt_algorithm", 
            "access_token_expire_minutes": "jwt_access_token_expire_minutes",
        }
        
        # 如果當前字段沒有值，但對應的兼容字段有值，則使用兼容字段的值
        if field_name in compatibility_map and v is None:
            compat_field = compatibility_map[field_name]
            compat_value = values.get(compat_field)
            if compat_value is not None:
                return compat_value
        
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"

# 創建全局設置實例
settings = Settings()

# 導出設置
__all__ = ["settings"]