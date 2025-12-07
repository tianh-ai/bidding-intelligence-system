"""
Authentication Router
提供用户认证相关的 API 端点（登录、注册、token 刷新等）

注意：这是一个简化的认证实现，用于快速启动项目。
生产环境建议使用更完善的认证系统（如 FastAPI-Users）。
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import jwt

from core.config import get_settings
from core.logger import logger

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()
settings = get_settings()

# ========== Pydantic Models ==========

class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    """认证响应"""
    token: str
    token_type: str = "bearer"
    user: "UserInfo"

class UserInfo(BaseModel):
    """用户信息"""
    id: str
    username: str
    email: str
    role: str = "user"  # admin 或 user
    created_at: datetime

class TokenRefreshResponse(BaseModel):
    """Token 刷新响应"""
    token: str

# ========== Helper Functions ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证 JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# ========== API Endpoints ==========

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    用户登录
    
    简化版本：直接返回测试用户的 token
    生产环境应验证数据库中的用户凭据
    """
    # TODO: 验证用户名和密码（当前为演示模式，接受任何凭据）
    if not request.username or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    
    # 创建测试用户信息
    # 为admin用户分配管理员角色
    role = "admin" if request.username.lower() == "admin" else "user"
    
    user_data = {
        "id": "admin-001" if request.username.lower() == "admin" else f"user-{request.username}",
        "username": request.username,
        "email": f"{request.username}@example.com",
        "role": role
    }
    
    # 生成 JWT token，包含角色信息
    token = create_access_token(data={
        "sub": user_data["id"], 
        "username": user_data["username"],
        "role": role
    })
    
    logger.info(f"User logged in: {request.username} (role: {role})")
    
    return AuthResponse(
        token=token,
        user=UserInfo(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            role=role,  # 添加角色信息
            created_at=datetime.utcnow()
        )
    )

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """
    用户注册
    
    简化版本：直接返回新用户的 token
    生产环境应将用户保存到数据库
    """
    # TODO: 检查用户名/邮箱是否已存在，保存到数据库
    
    role = "user"  # 注册用户默认为普通用户
    user_data = {
        "id": f"user-{request.username}",
        "username": request.username,
        "email": request.email,
        "role": role
    }
    
    token = create_access_token(data={
        "sub": user_data["id"], 
        "username": user_data["username"],
        "role": role
    })
    
    logger.info(f"New user registered: {request.username}")
    
    return AuthResponse(
        token=token,
        user=UserInfo(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            role=role,
            created_at=datetime.utcnow()
        )
    )

@router.get("/me", response_model=UserInfo)
async def get_current_user(token_data: dict = Depends(verify_token)):
    """
    获取当前用户信息
    
    需要在 Authorization header 中提供有效的 Bearer token
    """
    user_id = token_data.get("sub")
    username = token_data.get("username")
    role = token_data.get("role", "user")  # 从 token 中获取角色
    
    # TODO: 从数据库获取完整用户信息
    return UserInfo(
        id=user_id,
        username=username,
        email=f"{username}@example.com",
        role=role,
        created_at=datetime.utcnow()
    )

@router.post("/logout")
async def logout(token_data: dict = Depends(verify_token)):
    """
    用户登出
    
    简化版本：客户端删除 token 即可
    生产环境可能需要 token 黑名单机制
    """
    username = token_data.get("username")
    logger.info(f"User logged out: {username}")
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(token_data: dict = Depends(verify_token)):
    """
    刷新 JWT token
    
    使用当前有效的 token 获取新的 token
    """
    # 创建新的 token（延长过期时间）
    new_token = create_access_token(
        data={"sub": token_data["sub"], "username": token_data.get("username")},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenRefreshResponse(token=new_token)

@router.get("/health")
async def auth_health():
    """认证服务健康检查"""
    return {
        "status": "healthy",
        "service": "auth",
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "token_expire_minutes": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    }
