"""
Data Repack 공통 유틸리티
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from PyQt5.QtGui import QFont, QFontDatabase

# ── Colors
SK_RED = "#EA002C"
SK_MULTI = ["#EA002C", "#FBBC05", "#9BCF0A", "#009A93",
            "#0072C6", "#0E306D", "#68217A", "#000000"]
SK_ORANGE = "#F47725"
SK_BLUE = "#00A0E9"
SK_GRAY = "#777777"

# ── 프리셋 파일 경로
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent

PRESET_FILE = BASE_DIR / "specimen_presets.json"


def font_big():
    """큰 폰트 반환"""
    available_families = QFontDatabase().families()
    if "Pretendard" in available_families:
        return QFont("Pretendard", 13, QFont.DemiBold)
    else:
        return QFont("Arial", 13, QFont.Bold)


def font_small():
    """작은 폰트 반환"""
    available_families = QFontDatabase().families()
    if "Pretendard" in available_families:
        f = QFont("Pretendard", 9)
    else:
        f = QFont("Arial", 9)
    f.setWeight(QFont.Normal)
    return f


def safe_read_csv(path, **kw):
    """CSV 읽기 (UTF-8 실패 시 CP949로 재시도)"""
    try:
        return pd.read_csv(path, **kw)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949", **kw)


def calculate_yield_strength(strain, stress, offset_percent=0.2):
    """
    0.2% 오프셋 방법으로 항복강도 계산
    
    Args:
        strain: 변형률 배열 (절대값, 예: 0.01 = 1%)
        stress: 응력 배열 (MPa)
        offset_percent: 오프셋 (기본 0.2%)
        
    Returns:
        (항복강도, 항복 인덱스, 탄성계수)
    """
    if len(strain) < 10:
        return None, None, None
    
    offset_val = offset_percent / 100.0
    
    # 탄성 영역 감지 (0.05% ~ 0.25%)
    mask = (strain >= 0.0005) & (strain <= 0.0025)
    
    if np.sum(mask) < 3:
        mask = slice(0, min(len(strain), 20))
        
    x_linear = strain[mask]
    y_linear = stress[mask]
    
    if len(x_linear) < 2:
        return None, None, None

    try:
        slope, intercept = np.polyfit(x_linear, y_linear, 1)
        E_modulus = slope
    except Exception:
        return None, None, None
    
    # 오프셋 라인
    offset_line = E_modulus * (strain - offset_val)
    
    # 교차점 찾기
    start_idx = np.argmax(strain > offset_val)
    if start_idx == 0 and strain[0] <= offset_val:
         return None, None, E_modulus

    diff = stress - offset_line
    candidates = np.where(diff[start_idx:] < 0)[0]
    
    if len(candidates) > 0:
        idx_rel = candidates[0]
        yield_idx = start_idx + idx_rel
        yield_strength = stress[yield_idx]
        return yield_strength, yield_idx, E_modulus

    return None, None, E_modulus


def is_likely_strain_column(col_name):
    """컬럼명이 strain 데이터인지 확인"""
    col_lower = col_name.lower()
    strain_keywords = ["strain", "ε", "exx", "eyy", "e_", "epsilon", "변형"]
    return any(k in col_lower for k in strain_keywords)


def is_likely_load_column(col_name):
    """컬럼명이 load/force 데이터인지 확인"""
    col_lower = col_name.lower()
    load_keywords = ["load", "force", "f_", "하중", "힘"]
    return any(k in col_lower for k in load_keywords)
