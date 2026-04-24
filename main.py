"""
HealthPro API - 健康分析后端服务
FastAPI + PIL 图像分析
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from analyzers import analyze_face, analyze_tongue, analyze_urine, analyze_stool
from utils.image_utils import decode_base64_image

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healthpro-api")


# ===================== 生命周期 =====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 HealthPro API 服务启动")
    yield
    logger.info("👋 HealthPro API 服务关闭")


# ===================== FastAPI 应用 =====================
app = FastAPI(
    title="HealthPro 健康分析 API",
    description="提供面色、舌诊、尿检、便检的 AI 图像分析",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置（允许移动端跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制为你的 App 包名/域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== 数据模型 =====================
class AnalyzeRequest(BaseModel):
    image: str = Field(..., description="Base64 编码的 JPEG 图片（不带 data:image/ 前缀）")
    mode: str = Field(..., description="分析模式：face / tongue / urine / stool")
    timestamp: str | None = Field(None, description="客户端时间戳")
    device: str | None = Field(None, description="设备信息")


class HealthMetric(BaseModel):
    icon: str
    label: str
    value: str
    detail: str = ""
    color: str = "#6366f1"


class AnalyzeResponse(BaseModel):
    mode: str
    title: str
    icon: str
    score: int = Field(..., ge=0, le=100)
    color: str
    hasCloudAnalysis: bool = True
    confidence: float
    metrics: list[HealthMetric]
    advice: list[str]


# ===================== 认证 =====================
API_KEY = os.getenv("API_KEY", "your-secret-api-key")
TRUST_PROXY = os.getenv("TRUST_PROXY", "true").lower() == "true"


def verify_auth(authorization: str | None) -> None:
    """验证 Bearer Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少 Authorization 头")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization 格式错误，应为 Bearer <token>")
    token = authorization[7:]
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="API 密钥无效")


# ===================== 路由 =====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "healthpro-api", "version": "1.0.0"}


@app.get("/modes")
async def get_modes():
    """支持的检测模式"""
    return {
        "modes": [
            {"id": "face",   "name": "面色检测",   "icon": "😊"},
            {"id": "tongue", "name": "舌尖检测",   "icon": "👅"},
            {"id": "urine",  "name": "尿色检测",   "icon": "💧"},
            {"id": "stool",  "name": "屎色检测",   "icon": "💩"},
        ]
    }


@app.post("/health-analyze", response_model=AnalyzeResponse)
async def analyze(
    request: Request,
    body: AnalyzeRequest,
    authorization: str | None = Header(None, alias="Authorization"),
):
    """
    核心分析接口
    接收 Base64 图像，执行 AI 分析，返回结构化结果
    """
    # 认证
    verify_auth(authorization)

    # 模式校验
    valid_modes = ["face", "tongue", "urine", "stool"]
    if body.mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模式: {body.mode}，支持的模式: {valid_modes}"
        )

    # 图片大小校验（Base64 约增 33%，10MB 图片 ≈ 13.3MB base64）
    size_mb = len(body.image) / 1024 / 1024 * 0.75  # 反推原始大小
    max_size = float(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
    if size_mb > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"图片过大（{size_mb:.1f}MB），最大支持 {max_size}MB"
        )

    try:
        # 解码图片
        image = decode_base64_image(body.image)
        logger.info(f"[{body.mode}] 收到分析请求，图片尺寸: {image.size}")
    except Exception as e:
        logger.error(f"图片解码失败: {e}")
        raise HTTPException(status_code=400, detail=f"图片格式错误: {e}")

    try:
        # 分发到对应分析器
        if body.mode == "face":
            result = analyze_face(image)
        elif body.mode == "tongue":
            result = analyze_tongue(image)
        elif body.mode == "urine":
            result = analyze_urine(image)
        else:
            result = analyze_stool(image)

        logger.info(f"[{body.mode}] 分析完成，评分: {result['score']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{body.mode}] 分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析服务内部错误: {e}")


# ===================== 入口 =====================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
