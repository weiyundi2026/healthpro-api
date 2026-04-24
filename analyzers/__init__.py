"""
HealthPro API - 数据模型定义
"""

from .face import analyze_face
from .tongue import analyze_tongue
from .urine import analyze_urine
from .stool import analyze_stool

__all__ = ["analyze_face", "analyze_tongue", "analyze_urine", "analyze_stool"]
