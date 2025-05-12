import time

from ortools.sat.python import cp_model

from src.problem.strategy import get_cost, get_total_value, get_value, _normalize_value_weights, make_random_problem, \
    display_problem
from src.utils.utils import process_solution

CP_SAT_COEF = 100_000

def _init_cpsat_solver(num_item, action_dim, allow_zero_strategy=False):
    """
    CP-SAT 솔버를 초기화하고 변수를 설정합니다.

    Args:
        num_item: 아이템 수
        action_dim: 각 아이템에 대한 전략(액션) 수
        allow_zero_strategy: 아무것도 하지 않음 전략을 허용할지 여부. 현상유지 작전이 없을 경우 True로 설정해야 함.

    Returns:
        (model, x): CP-SAT 모델 객체와 변수 2차원 배열
    """
    model = cp_model.CpModel()

    # 변수 선언
    x = [[model.NewBoolVar(f'x[{i}][{j}]') for j in range(action_dim)] for i in range(num_item)]

    if allow_zero_strategy:
        # 전략 선택하지 않음으로 "현상유지" 전략을 구현
        for i in range(num_item):
            model.Add(sum(x[i][j] for j in range(action_dim)) <= 1)
    else:
        # 하나의 item은 하나의 전략만 선택할 수 있음
        for i in range(num_item):
            model.Add(sum(x[i][j] for j in range(action_dim)) == 1)

    return model, x

def _run_cpsat_solver(model):
    """
    CP-SAT 솔버를 실행하고 결과를 반환합니다.

    Args:
        model: CP-SAT 모델 객체

    Returns:
        (status, solver, float): 솔버 실행 상태와 솔버 객체 및 실행 시간
    """
    solver = cp_model.CpSolver()
    time_start = time.time()
    status = solver.Solve(model)
    time_end = time.time()

    if status == cp_model.OPTIMAL:
        print("Optimal solution found.")
    elif status == cp_model.FEASIBLE:
        print("Feasible solution found.")

    return status, solver, time_end - time_start

def _process_cpsat_result(status, solver, x, num_item, action_dim, costs, values, value_weights=None,
                          is_cost_constraint=True):
    """
    CP-SAT 솔버 결과를 처리합니다.

    Args:
        status: 솔버 실행 상태
        solver: CP-SAT 솔버 객체
        x: 변수 2차원 배열
        num_item: 아이템 수
        action_dim: 각 아이템에 대한 전략(액션) 수
        costs: 비용을 담은 데이터프레임
        values: 가치를 담은 데이터프레임 목록
        value_weights: 가치 차원에 대한 가중치. None인 경우 균등 분배
        is_cost_constraint: 비용 제약 문제 여부 (True: 비용 제약, False: 신뢰도 제약)

    Returns:
        (selected, cost, value): 선택된 전략, 총 비용, 총 가치/가치 리스트
        최적 해를 찾지 못한 경우 None
    """
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        selected = [[solver.Value(x[i][j]) for j in range(action_dim)] for i in range(num_item)]
        selected = process_solution(selected)

        if is_cost_constraint:
            return selected, get_cost(costs, selected), get_total_value(values, selected, value_weights)
        else:
            return selected, get_cost(costs, selected), get_value(values, selected)
    else:
        print("최적 해를 찾지 못했습니다.")
        raise ValueError("No optimal solution found.")

def solve_cost_constraint(problem, cost_constraint, value_weights=None, allow_zero_strategy=False):
    """
    CP-SAT 솔버를 사용하여 비용 제약 문제를 해결합니다.

    Args:
        problem: 문제 딕셔너리 {"cost": DataFrame, "value": [DataFrame...]}
        cost_constraint: 최대 비용 제약
        value_weights: 가치 차원에 대한 가중치. None인 경우 균등 분배
        allow_zero_strategy: 아무것도 하지 않음 전략을 허용할지 여부. 현상유지 작전이 없을 경우 True로 설정해야 함.

    Returns:
        (selected, cost, value, elapsed_time): 선택된 전략, 총 비용, 총 가치, 경과 시간
        최적 해를 찾지 못한 경우 None
    """
    values = problem["value"]
    costs = problem["cost"]
    num_item, action_dim = costs.shape

    # 솔버 초기화 및 변수 설정
    model, x = _init_cpsat_solver(num_item, action_dim, allow_zero_strategy)

    # 비용 제약 조건
    model.Add(
        sum(int(costs.iloc[i, j] * CP_SAT_COEF) * x[i][j] for i in range(num_item) for j in range(action_dim))
        <= int(cost_constraint * CP_SAT_COEF)
    )

    # 가중치 표준화
    value_weights = _normalize_value_weights(values, value_weights)

    # 가치를 최대화하는 목적 함수
    try:
        objective_expr = sum(
            int(values[i].iloc[k, j] * weight * CP_SAT_COEF) * x[i][j]
            for i in range(num_item) for j in range(action_dim)
            for k, weight in enumerate(value_weights)
        )
    except IndexError as e:
        raise IndexError(f"{e}"
                         f"비용테이블과 가치테이블에 존재하는 장치의 수가 일치하지 않을 수 있습니다.\n"
                         f"비용테이블의 장치: {len(costs.index.tolist())}\n"
                         f"가치테이블의 장치: {len([values[i].index.tolist() for i in range(len(values))])}\n"
                         f"위 두 값이 일정하지 않을 경우, 입력 테이블의 범위가 잘못 설정되었을 수 있습니다.\n")


    model.Maximize(objective_expr)

    # 솔버 실행
    status, solver, elapsed_time = _run_cpsat_solver(model)

    # 결과 처리
    return *_process_cpsat_result(status, solver, x, num_item, action_dim, costs, values, value_weights, True), elapsed_time

def solve_reliability_constraint(problem, reliability_constraint, allow_zero_strategy=False):
    """
    CP-SAT 솔버를 사용하여 신뢰도 제약 문제를 해결합니다.

    Args:
        problem: 문제 딕셔너리 {"cost": DataFrame, "value": [DataFrame...]}
        reliability_constraint: 각 가치 차원별 최소 요구 신뢰도
        allow_zero_strategy: 아무것도 하지 않음 전략을 허용할지 여부. 현상유지 작전이 없을 경우 True로 설정해야 함.

    Returns:
        (selected, cost, value, elapsed_time): 선택된 전략, 총 비용, 가치 리스트, 경과 시간
        최적 해를 찾지 못한 경우 None

    Raises:
        ValueError: 신뢰도 제약 길이가 가치 차원과 일치하지 않을 경우
    """
    values = problem["value"]
    costs = problem["cost"]
    num_item, action_dim = costs.shape

    # 솔버 초기화 및 변수 설정
    model, x = _init_cpsat_solver(num_item, action_dim, allow_zero_strategy)

    # 신뢰도 제약 조건
    if len(reliability_constraint) != values[0].shape[0]:
        raise ValueError(
            f"len(reliability_constraint) must be equal to value_dim. \n{len(reliability_constraint)} != {values[0].shape[0]}")

    try:
        for k in range(len(reliability_constraint)):
            model.Add(
                sum(int(values[i].iloc[k, j] * CP_SAT_COEF) * x[i][j] for i in range(num_item) for j in range(action_dim))
                >= int(reliability_constraint[k] * CP_SAT_COEF)
            )
    except IndexError as e:
        raise IndexError(f"{e}"
                         f"비용테이블과 가치테이블에 존재하는 장치의 수가 일치하지 않을 수 있습니다.\n"
                         f"비용테이블의 장치: {len(costs.index.tolist())}\n"
                         f"가치테이블의 장치: {len([values[i].index.tolist() for i in range(len(values))])}\n"
                         f"위 두 값이 일정하지 않을 경우, 입력 테이블의 범위가 잘못 설정되었을 수 있습니다.\n")

    # 비용을 최소화하는 목적 함수
    objective_expr = sum(
        int(costs.iloc[i, j] * CP_SAT_COEF) * x[i][j] for i in range(num_item) for j in range(action_dim))
    model.Minimize(objective_expr)

    # 솔버 실행
    status, solver, elapsed_time = _run_cpsat_solver(model)

    # 결과 처리
    return *_process_cpsat_result(status, solver, x, num_item, action_dim, costs, values, None, False), elapsed_time

def main():
    problem = make_random_problem(random_seed=4)
    display_problem(problem)

    selected_cost_constraint, total_cost, total_value = solve_cost_constraint(problem, cost_constraint=500,
                                                                              value_weights=None)
    print(f"Selected: {selected_cost_constraint}")
    print(f"Total Cost: {total_cost}")
    print(f"Value : {total_value}")

    selected_reliability_constraint, total_cost, total_value = solve_reliability_constraint(problem,
                                                                                            reliability_constraint=[150, 0.5, 0.5])
    print(f"Selected: {selected_reliability_constraint}")
    print(f"Total Cost: {total_cost}")
    print(f"Value : {total_value}")

    return selected_cost_constraint, selected_reliability_constraint