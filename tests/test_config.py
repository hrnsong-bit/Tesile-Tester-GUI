# tests/test_config.py

from config import motor_cfg, loadcell_cfg, temp_cfg

class TestConfig:
    """설정값 검증 테스트"""
    
    def test_motor_config_validity(self):
        """모터 설정값 유효성 검사"""
        assert motor_cfg.LEAD_MM_PER_REV > 0
        assert motor_cfg.DEFAULT_SPEED_RPS > 0
        assert motor_cfg.MAX_SPEED_RPS >= motor_cfg.DEFAULT_SPEED_RPS
        
        # 주소값 충돌 검사
        addresses = [
            motor_cfg.ADDR_POSITION_HI,
            motor_cfg.ADDR_POSITION_LO,
            motor_cfg.ADDR_SPEED,
            motor_cfg.ADDR_COMMAND
        ]
        assert len(addresses) == len(set(addresses))  # 중복 없음
    
    def test_loadcell_config(self):
        """로드셀 설정값 검증"""
        assert loadcell_cfg.FULLSCALE > 0
        assert loadcell_cfg.DEFAULT_BAUDRATE in [9600, 19200, 38400]
        assert loadcell_cfg.DEFAULT_PARITY in ['E', 'O', 'N']
    
    def test_temp_channel_addresses(self):
        """온도 채널 주소 중복 검사"""
        all_addrs = []
        for ch in temp_cfg.CHANNEL_ADDRESSES.values():
            all_addrs.extend(ch.values())
        
        # 중복 검사
        assert len(all_addrs) == len(set(all_addrs))
