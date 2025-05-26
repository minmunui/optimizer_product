from src.problem.strategy import get_cost, get_total_value
import src.solver.cpsat as cpsat
import src.solver.scip as scip


def get_next_solution(problem: dict,
                      solution: list[int],
                      solver_type: str = "SCIP",
                      allow_zero_strategy: bool = False
                      ) -> list[int]:
    """
    특정 문제와 solution을 입력으로 받아, 해당 solution보다 더 많은 민감도를 획득하면서도 비용이 가장 적은 솔루션을 찾습니다.

    :param problem: 문제 딕셔너리 {"cost": DataFrame, "value": [DataFrame...]}
    :param solution: 기준으로 설정할 솔루션
    :param solver_type: 솔버 유형 "SCIP" 또는 "CP-SAT"
    :param allow_zero_strategy: True인 경우, 모든 전략을 선택하지 않는 솔루션도 허용합니다.
    :return: 다음 솔루션
    """
    costs = problem["cost"]
    values = problem["value"]

    # 현재 솔루션의 비용과 가치를 계산
    current_cost = get_cost(costs, solution)
    current_value = get_total_value(values, solution)

    print(f"현재 솔루션 비용: {current_cost}, 가치: {current_value}")

    if solver_type == "SCIP":
        solver = scip
    elif solver_type == "CP-SAT":
        solver = cpsat
    else:
        raise ValueError(f"지원하지 않는 솔버 유형입니다: {solver_type}. 지원되는 솔버는 'SCIP'와 'CP-SAT'입니다.")

    solution, _, _, _ = solver.solve_reliability_constraint(problem, current_value, allow_zero_strategy=allow_zero_strategy)
    return solution