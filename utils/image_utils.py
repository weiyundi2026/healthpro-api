"""
图像处理工具
"""
import base64
import io
from PIL import Image


def decode_base64_image(data_url_or_raw: str) -> Image.Image:
    """
    将 Base64 字符串解码为 PIL Image 对象
    支持带 data:image/...;base64, 前缀的格式
    """
    raw = data_url_or_raw
    # 去掉 data:image/... 前缀
    if "," in raw:
        raw = raw.split(",", 1)[1]

    try:
        raw_bytes = base64.b64decode(raw)
    except Exception as e:
        raise ValueError(f"Base64 解码失败: {e}")

    try:
        img = Image.open(io.BytesIO(raw_bytes))
        # 统一转为 RGB（JPEG 不支持 RGBA）
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        return img
    except Exception as e:
        raise ValueError(f"图像格式无效或已损坏: {e}")


def encode_image_to_base64(img: Image.Image, format: str = "JPEG", quality: int = 85) -> str:
    """将 PIL Image 编码为 Base64 字符串"""
    buf = io.BytesIO()
    img.save(buf, format=format, quality=quality)
    return base64.b64encode(buf.getvalue()).decode("ascii")
