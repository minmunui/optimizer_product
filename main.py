import time
from config import DEFAULT_CONFIG

import src.solver.cpsat as cpsat
import src.solver.scip as scip
from src.problem.io import read_problem_from_excel, write_solution_to_excel, add_nothing_strategy

def main():
    config = DEFAULT_CONFIG

    # 입력 설정 가져오기
    input_config = config.get('input', {})
    file_path = input_config.get('file_path', "data/200528_SK 계통(표준모델 적용).xlsm")
    cost_range = input_config.get('cost_range', "Z3:AC49")
    cost_sheet = input_config.get('cost_sheet', "04. reliability parameter for 3")
    value_range = input_config.get('value_range', "A24:J71")
    value_sheet = input_config.get('value_sheet', "05. results")
    add_nothing = input_config.get('add_nothing_strategy', True)

    # 솔버 설정 가져오기
    solver_config = config.get('solver', {})
    solver_type = solver_config.get('type', 'SCIP')
    problem_type = solver_config.get('problem_type', 'cost_constraint')
    cost_constraint = solver_config.get('cost_constraint', 1000)
    value_weights = solver_config.get('value_weights', [1.0, 1.0, 1.0])
    reliability_constraint = solver_config.get('reliability_constraint', [150, 0.5, 0.5])

    # 출력 설정 가져오기
    output_config = config.get('output', {})
    output_file = output_config.get('file_path', 'data/solution.xlsx')
    output_sheet = output_config.get('sheet_name', f"{solver_type.lower()}_{problem_type}")

    # 문제 읽기
    print(f"Excel 파일 {file_path}에서 문제를 읽는 중...")
    problem = read_problem_from_excel(
        file_path,
        cost_range=cost_range,
        cost_sheet=cost_sheet,
        value_range=value_range,
        value_sheet=value_sheet
    )

    # 현상유지 전략 추가
    if add_nothing:
        print("'현상유지' 전략을 추가합니다.")
        problem = add_nothing_strategy(problem)

    else:
        print("'현상유지' 전략을 추가하지 않습니다.")
        print("아무 전략도 선택하지 않은 경우, 비용과 가치가 0인 '현상유지' 전략으로 취급합니다.")

    # 솔버 실행
    print(f"{solver_type} 솔버로 {problem_type} 문제를 해결합니다...")
    start_time = time.time()

    if solver_type.upper() == 'SCIP':
        if problem_type == 'cost_constraint':
            solution, total_cost, total_value, solve_time = scip.solve_cost_constraint(
                problem,
                cost_constraint=cost_constraint,
                value_weights=value_weights
            )
        else:  # reliability_constraint
            solution, total_cost, total_value, solve_time = scip.solve_reliability_constraint(
                problem,
                reliability_constraint=reliability_constraint
            )
    else:  # CP-SAT
        if problem_type == 'cost_constraint':
            solution, total_cost, total_value, solve_time = cpsat.solve_cost_constraint(
                problem,
                cost_constraint=cost_constraint,
                value_weights=value_weights
            )
        else:  # reliability_constraint
            solution, total_cost, total_value, solve_time = cpsat.solve_reliability_constraint(
                problem,
                reliability_constraint=reliability_constraint
            )

    # 결과 출력
    print("\n== 최적화 결과 ==")
    print(f"선택된 전략: {solution}")
    print(f"총 비용: {total_cost}")
    print(f"총 가치: {total_value}")
    print(f"해결 시간: {solve_time:.4f}초")
    print(f"총 실행 시간: {time.time() - start_time:.4f}초")

    # 결과 저장
    print(f"\n결과를 {output_file} 파일의 {output_sheet} 시트에 저장합니다.")
    write_solution_to_excel(output_file, sheet_name=output_sheet, problem=problem, solution=solution)

if __name__ == "__main__":
    main()