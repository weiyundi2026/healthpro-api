"""
便检分析器
根据粪便颜色、形状、均匀度判断消化系统健康状态
"""
from PIL import Image
import numpy as np

from .common import rgb_to_hsv, rgb_to_hsl, clamp, score_to_level


def analyze_stool(img: Image.Image) -> dict:
    """
    便检分析主函数
    采样粪便区域，分析颜色、均匀度、形态
    """
    iw, ih = img.size

    # 粪便主体区域
    crop = img.crop((
        int(iw * 0.20), int(ih * 0.20),
        int(iw * 0.80), int(ih * 0.80)
    ))
    arr = np.array(crop)

    r = int(arr[:, :, 0].mean())
    g = int(arr[:, :, 1].mean())
    b = int(arr[:, :, 2].mean())
    hsv = rgb_to_hsv(r, g, b)
    hsl = rgb_to_hsl(r, g, b)

    h, s, v = hsv
    l = hsl[2]

    # 计算均匀度（亮度方差）
    lightness_vals = arr[:, :, 0].astype(float) * 0.299 + \
                     arr[:, :, 1].astype(float) * 0.587 + \
                     arr[:, :, 2].astype(float) * 0.114
    l_mean = lightness_vals.mean()
    l_var = ((lightness_vals - l_mean) ** 2).mean()
    uniformity = clamp(100 - l_var * 0.5, 0, 100)

    # 粪便颜色分类
    if 10 <= h <= 40 and 20 <= l <= 50:
        stool_label = "黄褐色"
        stool_desc = "正常大便颜色，表明消化正常"
        stool_color_hex = "#8b6914"
        base_score = 88
        health_status = "消化正常"
        health_color = "#10b981"
    elif l > 60 and s < 15:
        stool_label = "灰白色"
        stool_desc = "可能提示胆道梗阻或肝胆问题，建议就医"
        stool_color_hex = "#d1d5db"
        base_score = 30
        health_status = "需警惕"
        health_color = "#dc2626"
    elif (h > 0 and h < 20) or (h > 340 and h <= 360):
        stool_label = "黑色/柏油便"
        stool_desc = "可能由消化道出血或食物引起，建议就医"
        stool_color_hex = "#1f2937"
        base_score = 25
        health_status = "需警惕"
        health_color = "#dc2626"
    elif 0 <= h < 60 and l > 50 and s < 40:
        stool_label = "绿色"
        stool_desc = "可能由食物色素或胆汁未充分分解引起，一般无害"
        stool_color_hex = "#22c55e"
        base_score = 72
        health_status = "轻度异常"
        health_color = "#f59e0b"
    elif l > 50 and s < 10:
        stool_label = "浅色/白陶土色"
        stool_desc = "可能提示胆汁分泌问题，建议就医检查"
        stool_color_hex = "#e5e7eb"
        base_score = 35
        health_status = "需关注"
        health_color = "#ef4444"
    else:
        stool_label = "其他颜色"
        stool_desc = "颜色异常可能由饮食或健康问题引起"
        stool_color_hex = "#9ca3af"
        base_score = 50
        health_status = "需观察"
        health_color = "#f59e0b"

    # 软硬程度（基于亮度：亮=软，暗=硬；结合饱和度）
    if l > 65:
        hardness_label = "偏软/腹泻"
        hardness_color = "#06b6d4"
        hardness_detail = "建议调整饮食，如持续请就医"
    elif l > 50:
        hardness_label = "正常"
        hardness_color = "#10b981"
        hardness_detail = "粪便形态正常"
    elif l > 35:
        hardness_label = "略干硬"
        hardness_color = "#f59e0b"
        hardness_detail = "建议增加膳食纤维和饮水"
    else:
        hardness_label = "干硬/便秘"
        hardness_color = "#ef4444"
        hardness_detail = "建议增加纤维摄入，多喝水，适度运动"

    # 均匀度
    uniformity_label = "均匀" if uniformity > 70 else "略有不均" if uniformity > 50 else "不均匀"
    uniformity_color = "#10b981" if uniformity > 70 else "#f59e0b" if uniformity > 50 else "#ef4444"

    score = int(clamp(base_score + uniformity * 0.1, 20, 95))
    status_text, status_color, status_icon = score_to_level(score)

    return {
        "mode": "stool",
        "title": "便检分析报告",
        "icon": "💩",
        "score": score,
        "color": stool_color_hex,
        "hasCloudAnalysis": True,
        "confidence": 0.80,
        "metrics": [
            {
                "icon": "🎨", "label": "粪便颜色", "value": stool_label,
                "detail": f"RGB({r},{g},{b}) | {stool_desc}", "color": stool_color_hex
            },
            {
                "icon": "💪", "label": "消化状态", "value": health_status,
                "detail": stool_desc, "color": health_color
            },
            {
                "icon": "🪵", "label": "软硬程度", "value": hardness_label,
                "detail": hardness_detail, "color": hardness_color
            },
            {
                "icon": "🔬", "label": "均匀度", "value": uniformity_label,
                "detail": f"均匀度评分 {int(uniformity)}%", "color": uniformity_color
            },
        ],
        "advice": [
            f"粪便呈{stool_label}，{stool_desc}。",
            "建议保持均衡饮食，增加膳食纤维（蔬菜、水果、全谷物）摄入。"
            if base_score >= 70 else "建议近期清淡饮食，观察排便情况，如有异常持续请就医。",
            "养成规律排便习惯，每天饮水 1500ml 以上。" if hardness_label in ["略干硬", "干硬/便秘"]
            else "保持当前饮食习惯，规律作息。",
        ]
    }
