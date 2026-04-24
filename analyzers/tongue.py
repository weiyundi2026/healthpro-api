"""
舌诊分析器
分析舌质颜色、舌苔类型、湿润度，参考中医舌诊理论
"""
from PIL import Image
import numpy as np

from .common import rgb_to_hsv, rgb_to_hsl, clamp, score_to_level


def _avg_rgb(img: Image.Image, x: float, y: float, w: float, h: float) -> tuple[int, int, int]:
    iw, ih = img.size
    crop = img.crop((
        max(0, int(x * iw)), max(0, int(y * ih)),
        min(iw, int((x + w) * iw)), min(ih, int((y + h) * ih))
    ))
    arr = np.array(crop)
    return int(arr[:, :, 0].mean()), int(arr[:, :, 1].mean()), int(arr[:, :, 2].mean())


def _classify_tongue_body(h: float, s: float, l: float) -> tuple[str, int]:
    """舌质分类 + 基础评分"""
    if l > 60 and s < 20:
        return "淡红", 85
    elif l > 50 and 20 <= s < 40:
        return "淡红", 82
    elif 30 <= l <= 50 and 30 <= s < 50:
        return "红", 65
    elif 20 <= l <= 40 and s > 50:
        return "绛红", 50
    elif l < 30:
        return "紫暗", 45
    else:
        return "淡白", 60


def _classify_coating(h: float, s: float, l: float) -> tuple[str, int]:
    """舌苔分类"""
    if l > 75 and s < 15:
        return "薄白苔", 10
    elif l > 65 and 10 <= s < 30:
        return "白苔", 5
    elif 50 <= l <= 70 and 20 <= s < 50:
        return "黄苔", -5
    elif l < 50 and s > 30:
        return "黄腻苔", -10
    elif l < 40 and s < 20:
        return "灰黑苔", -15
    else:
        return "薄白苔", 0


def _classify_moisture(v: float) -> tuple[str, str]:
    """舌体湿润度"""
    if v > 55:
        return "湿润", "#06b6d4"
    elif v > 40:
        return "略干", "#f59e0b"
    else:
        return "干燥", "#ef4444"


def analyze_tongue(img: Image.Image) -> dict:
    """舌诊分析主函数"""
    # 舌体（舌头主体区域）
    body_r, body_g, body_b = _avg_rgb(img, 0.25, 0.25, 0.50, 0.50)
    body_hsv = rgb_to_hsv(body_r, body_g, body_b)
    body_hsl = rgb_to_hsl(body_r, body_g, body_b)

    # 舌苔（舌面中央偏上）
    coating_r, coating_g, coating_b = _avg_rgb(img, 0.30, 0.20, 0.40, 0.30)
    coating_hsv = rgb_to_hsv(coating_r, coating_g, coating_b)
    coating_hsl = rgb_to_hsl(coating_r, coating_g, coating_b)

    # 舌边（齿痕检测）
    edge_r, edge_g, edge_b = _avg_rgb(img, 0.20, 0.40, 0.15, 0.30)
    edge_hsv = rgb_to_hsv(edge_r, edge_g, edge_b)

    # 分类
    tongue_body, body_base = _classify_tongue_body(body_hsl[0], body_hsl[1], body_hsl[2])
    coating_type, coating_delta = _classify_coating(coating_hsl[0], coating_hsl[1], coating_hsl[2])
    moisture_label, moisture_color = _classify_moisture(body_hsv[2])

    # 齿痕（有齿痕说明脾虚）
    tooth_mark_score = clamp(100 - (edge_hsv[1] * 1.5 + abs(edge_hsv[0] - 30) * 0.5))
    tooth_mark_label = "无齿痕" if tooth_mark_score > 70 else "轻度齿痕" if tooth_mark_score > 50 else "明显齿痕"

    # 综合评分
    base_score = body_base + coating_delta
    score = int(clamp(base_score + (body_hsv[2] / 100) * 10 - tooth_mark_score * 0.1, 40, 95))
    status_text, status_color, status_icon = score_to_level(score)

    # 湿润度数值
    moisture_score = int(body_hsv[2])

    return {
        "mode": "tongue",
        "title": "舌诊分析报告",
        "icon": "👅",
        "score": score,
        "color": "#ef4444",
        "hasCloudAnalysis": True,
        "confidence": 0.82,
        "metrics": [
            {
                "icon": "🍣", "label": "舌质", "value": tongue_body,
                "detail": f"RGB({body_r},{body_g},{body_b})", "color": "#ef4444"
            },
            {
                "icon": "🥛", "label": "舌苔", "value": coating_type,
                "detail": "苔色偏白为寒/偏黄为热", "color": "#f59e0b"
            },
            {
                "icon": "💧", "label": "湿润度", "value": moisture_label,
                "detail": f"湿润评分 {moisture_score}%", "color": moisture_color
            },
            {
                "icon": "🦷", "label": "齿痕", "value": tooth_mark_label,
                "detail": "有齿痕提示可能脾虚湿盛", "color": "#8b5cf6"
            },
        ],
        "advice": [
            f"舌质呈{tongue_body}，提示"
            + ("气血充足" if tongue_body in ["淡红"] else "可能有热证" if tongue_body == "红" else "可能有瘀血或寒证" if tongue_body == "紫暗" else "气血偏虚"),
            f"舌苔{coating_type}，"
            + ("属正常舌苔。" if coating_type in ["薄白苔", "白苔"] else "提示湿热内蕴，建议清淡饮食，少食辛辣。"),
            f"舌体{moisture_label}，" + ("津液充盈，状态良好。" if moisture_label == "湿润" else "建议多饮水，清淡饮食。"),
        ]
    }
