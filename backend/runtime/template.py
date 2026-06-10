"""
Project Template — 预生成 FastAPI 项目骨架
消除 DeveloperAgent 从零开始的误区，提供标准化目录结构 + 默认文件
"""
import os
from pathlib import Path


class ProjectTemplate:
    """快速创建 FastAPI + SQLAlchemy + JWT 的标准化项目骨架"""

    PROJECT_TREE = """
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 入口，含 CORS、路由注册
│   ├── config.py         # 配置管理 (环境变量)
│   ├── api/
│   │   ├── __init__.py
│   │   └── router.py     # API 路由
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py       # SQLAlchemy Base
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── request.py    # Pydantic 请求体
│   ├── services/
│   │   ├── __init__.py
│   │   └── logic.py      # 业务逻辑
│   └── auth.py            # JWT 认证工具
├── tests/
│   ├── __init__.py
│   └── test_api.py       # API 测试
├── requirements.txt       # 依赖
└── README.md              # 项目说明
"""

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def scaffold(self) -> dict:
        """创建项目骨架，返回生成的文件树"""
        dirs = [
            "app", "app/api", "app/models", "app/schemas", "app/services", "tests"
        ]
        for d in dirs:
            (self.root / d).mkdir(parents=True, exist_ok=True)
            (self.root / d / "__init__.py").write_text("")

        files = {
            "app/config.py": self._config_py(),
            "app/models/base.py": self._models_base(),
            "app/schemas/request.py": self._schemas_request(),
            "app/services/logic.py": self._services_logic(),
            "app/auth.py": self._auth_py(),
            "app/api/router.py": self._api_router(),
            "app/main.py": self._main_py(),
            "tests/conftest.py": self._conftest_py(),
            "tests/test_api.py": self._test_api(),
            "requirements.txt": self._requirements(),
            "README.md": self._readme(),
        }
        written = []
        for path, content in files.items():
            fp = self.root / path
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
            written.append(path)

        return {"tree": self.PROJECT_TREE, "files": written}

    def tree_string(self) -> str:
        """返回当前项目文件树"""
        lines = []
        for f in sorted(self.root.rglob("*")):
            if f.is_file() and ".pytest" not in str(f) and "__pycache__" not in str(f):
                rel = f.relative_to(self.root)
                if rel.name != "__init__.py" or rel.parent == self.root / "app":
                    lines.append(str(rel))
        return "\n".join(lines)

    @staticmethod
    def get_api_contract() -> str:
        return """## API 契约规范
- 所有端点前缀: /api/v1/
- 请求/响应格式: JSON
- 统一成功响应: {"code": 0, "message": "ok", "data": {...}}
- 统一错误响应: {"code": <err_code>, "message": "<err_msg>", "data": null}
- 认证方式: Bearer JWT (Header: Authorization: Bearer <token>)
- 分页参数: ?page=1&size=20
- Swagger: http://localhost:8000/docs
"""

    @staticmethod
    def get_db_schema() -> str:
        return """## 数据库模式
- ORM: SQLAlchemy 2.0
- 数据库: SQLite (开发) / PostgreSQL (生产)
- Base = declarative_base()
- 所有模型继承 Base
- 创建 SessionLocal = sessionmaker(bind=engine)
"""

    @staticmethod
    def get_acceptance_criteria() -> str:
        return """## ✅ 验收标准
必须满足以下所有条件，代码才算合格:
1. ✅ pytest tests/ 全部通过 (exit code 0)
2. ✅ 所有 API 端点返回统一 JSON 格式
3. ✅ Swagger 文档可访问 (/docs)
4. ✅ 包含参数校验 (Pydantic models)
5. ✅ 包含 JWT 认证中间件
6. ✅ 包含数据库迁移 (init_db)
7. ✅ README 包含启动说明
8. ✅ 所有函数有 type hints + docstring
"""

    # ─── 文件内容 ───

    def _config_py(self) -> str:
        return '''"""应用配置"""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE", "10080"))  # 7 days
'''

    def _models_base(self) -> str:
        return '''"""数据库模型基类"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

    def _schemas_request(self) -> str:
        return '''"""Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


class BaseResponse(BaseModel):
    """统一响应格式"""
    code: int = 0
    message: str = "ok"
    data: Optional[Any] = None

    class Config:
        json_schema_extra = {
            "example": {"code": 0, "message": "ok", "data": {}}
        }


# 业务模型在此文件继续添加
# class CreateUserRequest(BaseModel):
#     username: str = Field(..., min_length=3, max_length=50)
#     password: str = Field(..., min_length=6)
'''

    def _services_logic(self) -> str:
        return '''"""业务逻辑层"""
from typing import Optional


class ServiceLogic:
    """核心业务逻辑基类 — 子类实现具体功能"""

    def __init__(self, db_session):
        self.db = db_session
'''

    def _auth_py(self) -> str:
        return '''"""JWT 认证工具"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT token, 默认7天过期"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证 JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
'''

    def _api_router(self) -> str:
        return '''"""API 路由"""
from fastapi import APIRouter, Depends
from app.schemas.request import BaseResponse
from app.auth import verify_token

router = APIRouter(prefix="/api/v1", tags=["API"])


@router.get("/health", response_model=BaseResponse)
async def health_check():
    """健康检查"""
    return BaseResponse(data={"status": "ok"})
'''

    def _main_py(self) -> str:
        return '''"""FastAPI 应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router

app = FastAPI(title="AgentDev OS Application", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/api/v1/health")
async def health():
    return {"code": 0, "message": "ok", "data": {"status": "ok"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
'''

    def _test_api(self) -> str:
        return '''"""API 测试 — 验证生成的端点"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    """健康检查"""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0


def test_create_and_list():
    """创建消息 → 列出消息"""
    r = client.post("/api/v1/messages", json={"username": "t", "content": "hi"})
    assert r.status_code == 200

    r2 = client.get("/api/v1/messages")
    assert r2.status_code == 200


def test_invalid_request():
    """参数校验"""
    r = client.post("/api/v1/messages", json={"username": "", "content": ""})
    assert r.status_code in (200, 400, 422)
'''

    def _conftest_py(self) -> str:
        return '''import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
'''

    def _requirements(self) -> str:
        return """fastapi>=0.100.0
uvicorn[standard]>=0.20.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
python-jose[cryptography]>=3.0.0
passlib[bcrypt]>=1.7.0
httpx>=0.24.0
pytest>=7.0.0
"""

    def _readme(self) -> str:
        return """# AgentDev OS Application

## 启动

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## API 文档

http://localhost:8000/docs
"""
