DEFAULT_CONFIG = {
    "input": {
        # 문제를 읽어올 엑셀 파일 경로
        "file_path": "data/200528_SK 계통(표준모델 적용).xlsm",

        # 비용과 신뢰성 매개변수를 읽어올 범위
        "cost_sheet": "04. reliability parameter for 3",
        "cost_range": "Z3:AC49",
        "value_sheet": "05. results",
        "value_range": "A24:J71",

        # '아무것도 하지 않음' 전략을 추가할지 여부, 제공받은 Sheet에는 현상유지 전략이 없으므로 True로 설정했습니다.
        "add_nothing_strategy": True
    },

    "solver": {
        # 사용할 솔버의 종류 (SCIP 또는 CP-SAT)
        "type": "SCIP",
        # 문제의 종류 (비용 제약 -> "cost_constraint" 또는 신뢰도 제약 -> "reliability_constraint")
        "problem_type": "reliability_constraint",
        # 비용 제약문제일 경우 최대 비용 제약, 신뢰도 제약문제일 경우 사용되지 않음.
        "cost_constraint": 1000,
        # 비용 제약문제일 경우 가치 차원에 대한 가중치.
        "value_weights": [1.0, 1.0, 1.0],

        # 신뢰도 제약문제일 경우 각 가치 차원별 최소 요구 신뢰도
        "reliability_constraint": [0.03, 10, 1000]
    },
    "output": {
        # 솔루션을 저장할 엑셀 파일 경로
        "file_path": "data/output_rel.xlsx",
        # 솔루션을 저장할 시트 이름
        "sheet_name": "06. Maintenance Strategy"
    }
}