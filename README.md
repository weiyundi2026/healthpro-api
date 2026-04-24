# HealthPro v3.2.0 API 后端

> 基于 FastAPI 的真实 AI 健康分析后端服务

## 目录结构

```
health-api/
├── main.py              # FastAPI 入口，路由定义
├── models.py            # Pydantic 数据模型
├── analyzers/           # 分析引擎
│   ├── __init__.py
│   ├── face.py          # 面色/肤质分析
│   ├── tongue.py        # 舌诊分析
│   ├── urine.py         # 尿色分析
│   ├── stool.py         # 便检分析
│   └── common.py        # 通用工具（颜色转换、评分）
├── utils/
│   ├── __init__.py
│   └── image_utils.py   # Base64 图像处理
├── requirements.txt     # 依赖
├── Dockerfile           # Docker 部署
└── README.md            # 部署说明
```

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 或者用 Docker
docker build -t healthpro-api .
docker run -p 8000:8000 healthpro-api
```

## API 端点

### POST /health-analyze

**请求体：**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "mode": "face | tongue | urine | stool"
}
```

**响应体：**
```json
{
  "mode": "face",
  "title": "面色分析报告",
  "icon": "😊",
  "score": 78,
  "color": "#6366f1",
  "hasCloudAnalysis": true,
  "confidence": 0.92,
  "metrics": [
    {
      "icon": "🎨",
      "label": "肤色类型",
      "value": "白皙",
      "detail": "RGB(235, 215, 200)",
      "color": "#6366f1"
    }
  ],
  "advice": [
    { "text": "面色整体状态良好，建议保持规律作息。" },
    { "text": "检测到轻度疲劳迹象，建议保证充足睡眠。" }
  ]
}
```

### GET /health

健康检查端点。

### GET /modes

返回支持的检测模式列表。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `API_KEY` | API 访问密钥（Bearer Token） | `your-secret-api-key` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `MAX_IMAGE_SIZE_MB` | 最大图片大小（MB） | `10` |
| `TRUST_PROXY` | 信任代理（用于 HTTPS 反代） | `true` |

## 部署建议

- **生产环境**：使用 Gunicorn + Uvicorn Workers，Nginx 反代，启用 HTTPS
- **云平台**：可直接部署到阿里云函数计算、腾讯云 SCF、Railway、Render 等
- **密钥**：API_KEY 生产环境务必通过环境变量或密钥管理服务注入，不要硬编码

## 接口安全

- 所有请求需要携带 `Authorization: Bearer <API_KEY>` 头
- 图片数据建议启用 HTTPS 传输
- 可在 Nginx 层加限流防止滥用
