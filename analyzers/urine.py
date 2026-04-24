"""
尿色分析器
根据尿液颜色判断水分状态、可能的健康问题
"""
from PIL import Image
import numpy as np

from .common import rgb_to_hsv, rgb_to_hsl, clamp, score_to_level


def analyze_urine(img: Image.Image) -> dict:
    """
    尿色分析主函数
    采样尿液中央区域，基于 HSV 颜色空间进行分类
    """
    iw, ih = img.size

    # 采样中心区域（排除边缘干扰）
    crop = img.crop((
        int(iw * 0.25), int(ih * 0.25),
        int(iw * 0.75), int(ih * 0.75)
    ))
    arr = np.array(crop)

    r = int(arr[:, :, 0].mean())
    g = int(arr[:, :, 1].mean())
    b = int(arr[:, :, 2].mean())
    hsv = rgb_to_hsv(r, g, b)
    hsl = rgb_to_hsl(r, g, b)

    h, s, v = hsv
    lightness = hsl[2]

    # 尿色分类
    if lightness > 85 and s < 10:
        urine_label = "清澈如水"
        urine_desc = "尿液非常清澈，可能饮水过多"
        urine_color_hex = "#e8f4fd"
        base_score = 70  # 太清澈也不是最佳
        health_status = "水分过多"
        health_color = "#06b6d4"
    elif lightness > 70 and s < 20:
        urine_label = "淡黄色"
        urine_desc = "正常健康的尿液颜色"
        urine_color_hex = "#ffffcc"
        base_score = 90
        health_status = "水分充足"
        health_color = "#10b981"
    elif lightness > 50 and h < 50:
        urine_label = "深黄色"
        urine_desc = "轻微浓缩，建议多喝水"
        urine_color_hex = "#ffd700"
        base_score = 72
        health_status = "轻度缺水"
        health_color = "#f59e0b"
    elif h < 50 and lightness > 30:
        urine_label = "琥珀色"
        urine_desc = "尿液浓缩，需补充水分"
        urine_color_hex = "#ffbf00"
        base_score = 55
        health_status = "水分不足"
        health_color = "#ef4444"
    elif 30 <= h < 80 and lightness > 40:
        urine_label = "橙黄色"
        urine_desc = "可能由饮食或药物引起"
        urine_color_hex = "#ffa500"
        base_score = 65
        health_status = "需观察"
        health_color = "#f59e0b"
    elif h > 300 or h < 30:
        urine_label = "偏红/粉色"
        urine_desc = "可能由食物（甜菜根等）或血尿引起，需注意"
        urine_color_hex = "#ff6b6b"
        base_score = 35
        health_status = "需警惕"
        health_color = "#dc2626"
    else:
        urine_label = "异常颜色"
        urine_desc = "建议就医检查"
        urine_color_hex = "#9ca3af"
        base_score = 30
        health_status = "异常"
        health_color = "#dc2626"

    # 泡沫评估（饱和度高通常意味着泡沫多）
    foam_score = clamp(s * 2, 0, 100)
    foam_label = "无泡沫" if foam_score < 20 else "少量泡沫" if foam_score < 50 else "较多泡沫" if foam_score < 80 else "大量泡沫"
    foam_color = "#10b981" if foam_score < 20 else "#f59e0b" if foam_score < 50 else "#ef4444"

    # 清澈度
    clarity = clamp(lightness * 1.0 + (100 - s) * 0.3, 0, 100)
    clarity_label = "清澈" if clarity > 75 else "略浊" if clarity > 50 else "浑浊"
    clarity_color = "#10b981" if clarity > 75 else "#f59e0b" if clarity > 50 else "#ef4444"

    score = int(base_score)
    status_text, status_color, status_icon = score_to_level(score)

    return {
        "mode": "urine",
        "title": "尿色分析报告",
        "icon": "💧",
        "score": score,
        "color": urine_color_hex,
        "hasCloudAnalysis": True,
        "confidence": 0.88,
        "metrics": [
            {
                "icon": "🎨", "label": "尿液颜色", "value": urine_label,
                "detail": f"RGB({r},{g},{b}) | {urine_desc}", "color": urine_color_hex
            },
            {
                "icon": "💦", "label": "水分状态", "value": health_status,
                "detail": urine_desc, "color": health_color
            },
            {
                "icon": "🫧", "label": "泡沫评估", "value": foam_label,
                "detail": "泡沫多可能提示蛋白尿或尿路感染", "color": foam_color
            },
            {
                "icon": "✨", "label": "清澈度", "value": clarity_label,
                "detail": f"清澈评分 {int(clarity)}%", "color": clarity_color
            },
        ],
        "advice": [
            f"您的尿液呈{urine_label}，{urine_desc}。",
            "建议每天饮水 1500-2000ml，保持规律排尿。" if base_score < 80
            else "当前水分摄入充足，请继续保持良好的饮水习惯。",
            "如尿液持续异常（血色/浓茶色），请及时就医检查。" if base_score < 50
            else "目前尿液状态良好，建议定期观察。",
        ]
    }
