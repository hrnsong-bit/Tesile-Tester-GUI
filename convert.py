import csv

input_file = 'CF_18_6.txt'
output_file = 'CF_18_6_load.csv'

# 데이터 시작을 식별하는 헤더 키워드
start_marker = "Time (s)"

data_rows = []
is_data_section = False

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 빈 줄이나 불필요한 줄 건너뛰기
            if not line.strip():
                continue
            
            # 헤더 라인을 찾으면 데이터 섹션 시작으로 간주
            if start_marker in line:
                is_data_section = True
                continue # 헤더 라인 자체는 건너뜀 (직접 작성할 것이므로)

            if is_data_section:
                # 공백(탭 포함)을 기준으로 분리
                parts = line.split()
                
                # 데이터 형식이 맞는지 확인 (최소 4개 이상의 컬럼이 있어야 함)
                if len(parts) >= 4:
                    # 0: Time, 1: Encoder, 3: Load Cell Window (Index 2는 Load Cell Full Scale이므로 건너뜀)
                    time_val = parts[0]
                    encoder_val = parts[1]
                    load_cell_window_val = parts[3]
                    
                    data_rows.append([time_val, encoder_val, load_cell_window_val])

    # CSV 파일 쓰기
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # 헤더 작성
        writer.writerow(['Time (s)', 'Encoder Displacement (m)', 'Load Cell Window (N)'])
        # 데이터 작성
        writer.writerows(data_rows)

    print(f"변환 완료! '{output_file}' 파일이 생성되었습니다.")
    print(f"총 데이터 행 수: {len(data_rows)}")

except FileNotFoundError:
    print(f"오류: '{input_file}' 파일을 찾을 수 없습니다. 같은 폴더에 있는지 확인해주세요.")