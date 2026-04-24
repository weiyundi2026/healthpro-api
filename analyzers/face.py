"""
面色 / 肤质分析器
基于图像像素颜色采样，计算肤色类型、气色、疲劳指数等指标
"""
from PIL import Image
import numpy as np

from .common import (
    rgb_to_hsv, rgb_to_hsl, rgb_to_hsv, rgb_to_hsl,
    clamp, score_to_level, classify_skin_tone,
    classify_saturation, classify_lightness,
)


def _sample_region(img: Image.Image, x: float, y: float, w: float, h: float) -> tuple[int, int, int]:
    """采样图像指定区域，返回平均 RGB"""
    iw, ih = img.size
    px, py = int(x * iw), int(y * ih)
    pw, ph = max(1, int(w * iw)), max(1, int(h * ih))
    crop = img.crop((px, py, min(px + pw, iw), min(py + ph, ih)))
    arr = np.array(crop)
    return int(arr[:, :, 0].mean()), int(arr[:, :, 1].mean()), int(arr[:, :, 2].mean())


def analyze_face(img: Image.Image) -> dict:
    """
    面色分析主函数
    采样前额、左右脸颊、下巴区域的肤色，计算综合评分
    """
    # 采样关键区域
    forehead = _sample_region(img, 0.35, 0.12, 0.30, 0.15)  # 前额
    left_cheek = _sample_region(img, 0.18, 0.35, 0.18, 0.15)  # 左颊
    right_cheek = _sample_region(img, 0.64, 0.35, 0.18, 0.15)  # 右颊
    chin = _sample_region(img, 0.38, 0.60, 0.24, 0.12)  # 下巴
    under_eye_l = _sample_region(img, 0.28, 0.38, 0.12, 0.06)  # 左眼下
    under_eye_r = _sample_region(img, 0.60, 0.38, 0.12, 0.06)  # 右眼下

    # 综合肤色
    avg_r = (forehead[0] + left_cheek[0] + right_cheek[0] + chin[0]) // 4
    avg_g = (forehead[1] + left_cheek[1] + right_cheek[1] + chin[1]) // 4
    avg_b = (forehead[2] + left_cheek[2] + right_cheek[2] + chin[2]) // 4
    avg_hsv = rgb_to_hsv(avg_r, avg_g, avg_b)
    avg_hsl = rgb_to_hsl(avg_r, avg_g, avg_b)

    # 肤色分类
    skin_tone_label, _ = classify_skin_tone(avg_hsl[0], avg_hsl[1], avg_hsl[2])

    # 气色（饱和度）
    qi_se_label, qi_se_color = classify_saturation(avg_hsv[1])

    # 疲劳指数（眼下亮度越低=越疲劳）
    under_eye_avg = (under_eye_l[0] + under_eye_l[1] + under_eye_l[2] +
                     under_eye_r[0] + under_eye_r[1] + under_eye_r[2]) / 6
    under_eye_lightness = under_eye_avg / 255 * 100
    fatigue_score = clamp(100 - under_eye_lightness * 1.2)
    if fatigue_score < 20:
        fatigue_label = "精神饱满"
        fatigue_color = "#10b981"
    elif fatigue_score < 40:
        fatigue_label = "轻度疲劳"
        fatigue_color = "#f59e0b"
    elif fatigue_score < 60:
        fatigue_label = "中度疲劳"
        fatigue_color = "#ef4444"
    else:
        fatigue_label = "明显疲劳"
        fatigue_color = "#dc2626"

    # 综合评分
    score = int(clamp((100 - fatigue_score * 0.6) + avg_hsv[1] * 0.3, 50, 98))
    status_text, status_color, status_icon = score_to_level(score)

    # 水分状态
    moisture_label, moisture_color = classify_lightness(avg_hsl[2])

    # 皮肤温度估算（基于血流红色分量）
    redness = (left_cheek[0] + right_cheek[0]) / 2 - avg_g
    temp_c = round(35.5 + redness * 0.01, 1)

    # 光线条件
    light_cond_label = "充足" if avg_hsv[1] > 20 else "偏暗"
    light_cond_color = "#10b981" if avg_hsv[1] > 20 else "#f59e0b"

    return {
        "mode": "face",
        "title": "面色分析报告",
        "icon": "😊",
        "score": score,
        "color": "#6366f1",
        "hasCloudAnalysis": True,
        "confidence": round(0.75 + avg_hsv[1] / 200, 2),
        "metrics": [
            {
                "icon": "🎨", "label": "肤色类型", "value": skin_tone_label,
                "detail": f"RGB({avg_r},{avg_g},{avg_b})", "color": "#6366f1"
            },
            {
                "icon": "✨", "label": "气色评估", "value": qi_se_label,
                "detail": "血色充足，光泽度好" if avg_hsv[1] > 25 else "建议多休息，调理气血",
                "color": qi_se_color
            },
            {
                "icon": "😴", "label": "疲劳指数", "value": fatigue_label,
                "detail": f"疲劳程度 {int(fatigue_score)}%", "color": fatigue_color
            },
            {
                "icon": "🌡️", "label": "皮肤温度", "value": f"{temp_c}°C",
                "detail": "基于面部血流估算", "color": "#06b6d4"
            },
            {
                "icon": "💧", "label": "水分状态", "value": moisture_label,
                "detail": "建议多饮水", "color": moisture_color
            },
            {
                "icon": "☀️", "label": "光线条件", "value": light_cond_label,
                "detail": "建议在明亮环境下检测", "color": light_cond_color
            },
        ],
        "advice": [
            f"您的面色为{skin_tone_label}，{qi_se_label}，"
            + ("整体状态良好。" if fatigue_score < 30 else "建议适当休息。"),
            "检测到轻度疲劳迹象，建议保证7-8小时睡眠，减少熬夜。" if fatigue_score > 40
            else "当前精神状态良好，继续保持规律作息。",
            "面部血色充足，建议保持适度运动。" if avg_hsv[1] > 20
            else "面色略显暗沉，可适当补充维生素C和铁元素。",
        ]
    }
