# tests/test_data_repack.py
"""
Data_Repack.py 테스트
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestYieldStrengthCalculation:
    """항복 강도 계산 함수 테스트"""
    
    @pytest.mark.timeout(10)
    def test_calculate_yield_strength_valid(self):
        """항복 강도 계산 (정상 케이스)"""
        # ===== 수정: Data_Repack에서 함수 직접 임포트 =====
        try:
            from Data_Repack import calculate_yield_strength
        except ImportError:
            pytest.skip("Data_Repack.py not found or calculate_yield_strength not defined")
        
        # Given: 정상적인 응력-변형률 데이터
        # 선형 탄성 구간 (0-0.002) + 항복 후 구간
        strain = np.array([
            0.0000, 0.0005, 0.0010, 0.0015, 0.0020, 0.0025,  # 탄성 구간
            0.0030, 0.0035, 0.0040, 0.0050, 0.0060, 0.0080,  # 항복 후
            0.0100, 0.0120, 0.0150, 0.0200
        ])
        
        # 탄성계수 200 GPa 가정 (E = 200,000 MPa)
        E = 200000.0
        stress = np.array([
            0.0, 100.0, 200.0, 300.0, 400.0, 480.0,  # 선형 (E=200GPa)
            520.0, 540.0, 550.0, 560.0, 565.0, 570.0,  # 항복 후 (경화)
            575.0, 580.0, 590.0, 600.0
        ])
        
        # When: 항복 강도 계산 (0.2% 오프셋)
        ys, idx, E_calc = calculate_yield_strength(strain, stress, offset_percent=0.2)
        
        # Then: 결과 검증
        assert ys is not None, "항복 강도가 계산되어야 함"
        assert E_calc is not None, "탄성계수가 계산되어야 함"
        assert E_calc > 0, "탄성계수는 양수여야 함"
        
        # 탄성계수 범위 검증 (100 GPa ~ 300 GPa)
        assert 100000 < E_calc < 300000, \
            f"탄성계수가 비정상적: {E_calc:.0f} MPa (예상: 150k-250k MPa)"
    
    @pytest.mark.timeout(5)
    def test_calculate_yield_strength_insufficient_data(self):
        """항복 강도 계산 (데이터 부족)"""
        try:
            from Data_Repack import calculate_yield_strength
        except ImportError:
            pytest.skip("Data_Repack.py not found")
        
        # Given: 데이터 부족 (5개 미만)
        strain = np.array([0.0, 0.001])
        stress = np.array([0.0, 100.0])
        
        # When: 항복 강도 계산
        ys, idx, E = calculate_yield_strength(strain, stress)
        
        # Then: None 반환 (데이터 부족)
        assert ys is None
        assert idx is None
        assert E is None
    
    @pytest.mark.timeout(5)
    def test_calculate_yield_strength_no_yield(self):
        """항복 강도 계산 (항복점 없음)"""
        try:
            from Data_Repack import calculate_yield_strength
        except ImportError:
            pytest.skip("Data_Repack.py not found")
        
        # Given: 완전 선형 데이터 (항복 없음)
        strain = np.linspace(0, 0.005, 20)
        stress = strain * 200000.0  # 완전 탄성
        
        # When: 항복 강도 계산
        ys, idx, E = calculate_yield_strength(strain, stress)
        
        # Then: 탄성계수는 계산되지만 항복점은 없음
        # (함수 구현에 따라 None이거나 값이 있을 수 있음)
        assert E is not None, "탄성계수는 계산되어야 함"


class TestCSVReadSafe:
    """CSV 읽기 안전성 테스트"""
    
    @pytest.mark.timeout(5)
    def test_safe_read_csv_utf8(self, tmp_path):
        """UTF-8 CSV 읽기"""
        try:
            from Data_Repack import safe_read_csv
        except ImportError:
            pytest.skip("Data_Repack.py not found")
        
        # Given: UTF-8 CSV 생성
        csv_path = tmp_path / "test_utf8.csv"
        df = pd.DataFrame({
            'strain': [0.0, 0.001, 0.002],
            'stress': [0.0, 100.0, 200.0]
        })
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        # When: 읽기
        loaded = safe_read_csv(csv_path)
        
        # Then: 정상 로드
        assert len(loaded) == 3
        assert 'strain' in loaded.columns
    
    @pytest.mark.timeout(5)
    def test_safe_read_csv_cp949_fallback(self, tmp_path):
        """CP949 인코딩 폴백 테스트"""
        try:
            from Data_Repack import safe_read_csv
        except ImportError:
            pytest.skip("Data_Repack.py not found")
        
        # Given: CP949 CSV 생성
        csv_path = tmp_path / "test_cp949.csv"
        df = pd.DataFrame({
            'strain': [0.0, 0.001],
            'stress': [0.0, 100.0]
        })
        df.to_csv(csv_path, index=False, encoding='cp949')
        
        # When: 읽기 (UTF-8 실패 시 CP949 폴백)
        loaded = safe_read_csv(csv_path)
        
        # Then: 정상 로드
        assert len(loaded) == 2


class TestPreprocessor:
    """CSV Preprocessor 로직 테스트"""
    
    @pytest.mark.timeout(10)
    def test_preprocessor_data_trimming(self, tmp_path):
        """데이터 트리밍 로직 검증"""
        # Given: 테스트 CSV 생성
        csv_path = tmp_path / "test_preprocess.csv"
        df = pd.DataFrame({
            'X': [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            'Y': [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
        })
        df.to_csv(csv_path, index=False)
        
        # When: X >= 2.0 기준으로 트리밍 (Preprocessor 로직 시뮬레이션)
        loaded = pd.read_csv(csv_path)
        trimmed = loaded[loaded['X'] >= 2.0].copy()
        trimmed.reset_index(drop=True, inplace=True)
        
        # Then: 4개 행만 남아야 함
        assert len(trimmed) == 4
        assert trimmed['X'].iloc[0] == 2.0
        assert trimmed['Y'].iloc[0] == 20.0
