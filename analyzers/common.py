"""
通用工具函数：颜色转换、评分算法
"""
from __future__ import annotations
import math


def rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    """RGB (0-255) → HSV (h: 0-360, s: 0-100, v: 0-100)"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn

    if df == 0:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    else:
        h = (60 * ((r - g) / df) + 240) % 360

    s = 0.0 if mx == 0 else (df / mx) * 100
    v = mx * 100
    return h, s, v


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """RGB (0-255) → HSL (h: 0-360, s: 0-100, l: 0-100)"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    l = (mx + mn) / 2
    df = mx - mn

    if df == 0:
        h, s = 0.0, 0.0
    else:
        s = df / (1 - abs(2 * l - 1)) * 100
        if mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        else:
            h = (60 * ((r - g) / df) + 240) % 360

    return h, s, l * 100


def clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def score_to_level(score: int) -> tuple[str, str, str]:
    """将 0-100 评分转为状态标签、颜色、图标"""
    if score >= 80:
        return ("健康", "#10b981", "✅")
    elif score >= 60:
        return ("正常", "#f59e0b", "⚠️")
    else:
        return ("需关注", "#ef4444", "🔴")


def classify_skin_tone(h: float, s: float, l: float) -> tuple[str, str]:
    """基于 HSL 分类肤色类型"""
    if l > 65:
        return "白皙", "#ffe4c4"
    elif l > 50:
        return "偏白", "#f5deb3"
    elif l > 35:
        return "自然", "#deb887"
    elif l > 20:
        return "偏黄", "#d2b48c"
    else:
        return "健康肤色", "#8b4513"


def classify_saturation(s: float) -> tuple[str, str]:
    """基于饱和度判断气色"""
    if s > 25:
        return "红润有光泽", "#10b981"
    elif s > 15:
        return "气色尚可", "#f59e0b"
    else:
        return "气色欠佳", "#ef4444"


def classify_lightness(l: float) -> tuple[str, str]:
    """基于亮度判断水分状态"""
    if l > 50:
        return "良好", "#06b6d4"
    elif l > 35:
        return "略干", "#f59e0b"
    else:
        return "干燥", "#ef4444"
