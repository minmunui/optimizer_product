import random

import numpy as np
import pandas as pd

"""
이 모듈은 유지보수 전략 최적화 문제를 생성하고 해결하는 데 사용됩니다.
랜덤한 유지보수 전략 최적화 문제를 생성하고, SCIP, CP-SAT 솔버를 사용하여 문제를 해결합니다.

최적화 문제는 아래와 같이 정의됩니다.
각 아이템은 여러 개의 전략을 가질 수 있으며, 각 전략은 비용과 가치를 가집니다.

dict {
    "cost" : pandas.DataFrame
    "value" : list[pandas.DataFrame]
}

cost : 각 아이템에 대한 전략 비용을 나타내는 DataFrame입니다.
cost는 dataframe으로 정의되어 있으며, 각 record는 아이템을 나타내고, 각 column은 전략에 따른 비용을 나타냅니다.

ex)
Item 0 

value : 각 아이템에 대한 전략 가치를 나타내는 DataFrame입니다.
value는 dataframe의 리스트로 정의되어 있으며, 각 dataframe은 아이템에 대한 가치정보를 나타냅니다.
예를 들어 value[0]은 첫 번째 아이템에 대한 가치정보를 나타내고, value[1]은 두 번째 아이템에 대한 가치정보를 나타냅니다.
value의 각 dataframe은 record가 가치를 나타내며, column은 전략을 나타냅니다.

ex)
Item 0
         Strategy 0  Strategy 1  Strategy 2  Strategy 3
Value 0         0.0    4.197690    8.505370    8.964087
Value 1         0.0    0.822019    2.705443    8.792473
Value 2         0.0    0.393839    2.466825    7.622201

"""


def make_random_problem(num_items: int = 50,
                        item_label: list[str] = None,
                        strategy_count: int = 4,
                        strategy_label: list[str] = None,
                        cost_range: tuple[float, float] = (1000, 5000),
                        value_range: tuple[float, float] = (0, 10),
                        value_dimension: int = 3,
                        problem_cost: float = 1000,
                        cost_ratio: float = 2.0,
                        random_seed: int = 42,
                        allow_zero_strategy: bool = False,
                        ):
    """
    랜덤한 유지보수전략 최적화 문제를 생성합니다.

    Args:
        num_items: 문제에 포함될 아이템 수
        item_label: 아이템 레이블 목록. None인 경우 자동 생성
        strategy_count: 각 아이템에 대한 전략 수
        strategy_label: 전략 레이블 목록. None인 경우 자동 생성
        cost_range: (최소 비용, 최대 비용) 튜플
        value_range: (최소 가치, 최대 가치) 튜플
        value_dimension: 가치 차원 수
        problem_cost: 문제 총 비용 스케일링 기준값
        cost_ratio: 비용 비율 조정 계수
        random_seed: 랜덤 시드 값
        allow_zero_strategy: 아무것도 하지 않음 전략을 허용할지 여부. 현상유지 작전이 없을 경우 True로 설정해야 함.

    Returns:
        생성된 문제를 담은 딕셔너리 {"cost": DataFrame, "value": [DataFrame...]}

    Raises:
        ValueError: strategy_label 또는 item_label의 길이가 올바르지 않을 경우
    """
    random.seed(random_seed)

    if allow_zero_strategy:
        # 각 아이템에 대해 전략을 랜덤하게 생성, 비용과 가치는 내림차순으로 정렬
        costs = [sorted([random.uniform(*cost_range) for _ in range(strategy_count)], reverse=True) for _ in range(num_items)]
        values = [[sorted([random.uniform(*value_range) for _ in range(strategy_count)], reverse=True) for _ in
                   range(value_dimension)] for _ in range(num_items)]
    else:
        costs = [sorted([random.uniform(*cost_range) for _ in range(strategy_count - 1)] + [0], reverse=True) for _ in range(num_items)]
        values = [[sorted([random.uniform(*value_range) for _ in range(strategy_count - 1)] + [0], reverse=True) for _ in
                   range(value_dimension)] for _ in range(num_items)]

    values = np.array(values)

    strategy_label = [f"Strategy {i}" for i in range(strategy_count)] if strategy_label is None else strategy_label
    value_label = [f"Value {i}" for i in range(value_dimension)]
    item_label = [f"Item {i}" for i in range(num_items)] if item_label is None else item_label
    df_values = [pd.DataFrame(value, index=value_label, columns=strategy_label) for value in values]

    if len(strategy_label) != strategy_count:
        raise ValueError(
            f"len(strategy_label) must be equal to strategy_count. \n{len(strategy_label)} != {strategy_count}")

    if len(item_label) != num_items:
        raise ValueError(f"len(item_label) must be equal to num_items. \n{len(item_label)} != {num_items}")

    total_costs = sum(costs[i][strategy_count - 1] for i in range(num_items))

    # 비용의 비율을 조정
    costs = [
        [cost * problem_cost * cost_ratio / total_costs for cost in costs[i]]
        for i in range(num_items)
    ]

    costs = np.array(costs)
    df_cost = pd.DataFrame(costs, index=item_label, columns=strategy_label)

    return {
        "cost": df_cost,
        "value": df_values
    }


def get_value_cost_constraint(problem: dict,
                              solution: list[int] | list[list[bool]],
                              cost_constraint: float = 100_000_000_000_000_000,
                              value_weights: list[float] = None,
                              penalty: bool = False,
                              ):
    """
    주어진 문제와 솔루션에 대해 비용 제약 조건을 고려한 가치를 계산합니다.

    Args:
        problem: 문제 딕셔너리 {"cost": DataFrame, "value": [DataFrame...]}
        solution: 각 아이템에 대해 선택된 전략 인덱스 또는 불리언 리스트
        cost_constraint: 비용 제약 값
        value_weights: 가치 차원에 대한 가중치. None인 경우 균등 분배
        penalty: 비용 제약을 초과할 경우 페널티 적용 여부

    Returns:
        가치 총합. 비용 제약 초과 시 0 또는 페널티 값
    """
    costs = problem["cost"]
    values = problem["value"]

    value_weights = [1.0 for _ in range(len(values[0].values.tolist()))] if value_weights is None else value_weights
    value_weights = (np.array(value_weights) / sum(value_weights)).tolist()

    total_cost = 0
    total_value = 0

    if type(solution[0]) is list:
        solution = [solution[i].index(True) for i in range(len(solution))]

    for i in range(len(solution)):
        total_cost += costs.iloc[i].to_numpy()[solution[i]]
        value = values[i].to_numpy()
        for j, value_weight in enumerate(value_weights):
            total_value += value[j][solution[i]] * value_weight

    if total_cost > cost_constraint:
        if penalty:
            return cost_constraint - total_cost
        else:
            return 0

    return total_value


def get_total_value(values: pd.DataFrame,
                    solution: list[int] | list[list[bool]],
                    value_weights: list[float] = None,
                    ) -> float:
    """
    주어진 문제와 솔루션에 대해 종합적인 가치를 계산합니다.

    Args:
        values: 가치를 담은 데이터프레임 목록
        solution: 각 아이템에 대해 선택된 전략 인덱스 또는 불리언 리스트
        value_weights: 가치 차원에 대한 가중치. None인 경우 균등 분배

    Returns:
        가중치가 적용된 가치 총합
    """
    if value_weights is None:
        value_weights = [1.0 for _ in range(len(values[0].values.tolist()))]

    return sum([value * value_weights[i] for i, value in enumerate(get_value(values, solution))])


def get_value(values: pd.DataFrame, solution: list[int] | list[list[bool]]) -> list[float]:
    """
    주어진 문제와 솔루션에 대해 각 가치 차원별 가치를 계산합니다.

    Args:
        values: 가치를 담은 데이터프레임 목록
        solution: 각 아이템에 대해 선택된 전략 인덱스 또는 불리언 리스트

    Returns:
        각 가치 차원별 가치 총합 리스트

    Raises:
        ValueError: 가치 차원이 일치하지 않거나 솔루션 길이가 올바르지 않을 경우
    """
    value_dim = values[0].shape[0]
    if value_dim != values[0].shape[0]:
        raise ValueError(f"values[0].shape[0] must be equal to value_dim. \n{value_dim} != {values[0].shape[0]}")

    if len(solution) != len(values):
        raise ValueError(f"len(solution) must be equal to num_item of values. \n{len(solution)} != {len(values)}")

    if type(solution[0]) is list:
        solution = [solution[i].index(True) for i in range(len(solution))]

    total_value = [0 for _ in range(value_dim)]
    for i in range(len(solution)):
        value = values[i].to_numpy()
        for j in range(value_dim):
            total_value[j] += value[j][solution[i]]

    return total_value


def get_cost(costs: pd.DataFrame, solution: list[int] | list[list[bool]]):
    """
    주어진 문제와 솔루션에 대해 총 비용을 계산합니다.

    Args:
        costs: 비용을 담은 데이터프레임
        solution: 각 아이템에 대해 선택된 전략 인덱스 또는 불리언 리스트

    Returns:
        비용 총합

    Raises:
        ValueError: 솔루션 길이가 올바르지 않을 경우
    """
    if len(solution) != costs.shape[0]:
        raise ValueError(f"len(solution) must be equal to num_item of costs. \n{len(solution)} != {costs.shape[0]}")

    if type(solution[0]) is list:
        solution = [solution[i].index(True) for i in range(len(solution))]

    return sum(costs.iloc[i, solution[i]] if solution[i] != -1 else 0 for i in range(len(solution)))


def display_solution(problem: dict, solution: list[int] | list[list[bool]], weights: list[float] = None):
    """
    주어진 문제와 솔루션을 출력합니다.

    Args:
        problem: 문제 딕셔너리 {"cost": DataFrame, "value": [DataFrame...]}
        solution: 각 아이템에 대해 선택된 전략 인덱스 또는 불리언 리스트
        weights: 가치 차원에 대한 가중치. None인 경우 균등 분배

    Raises:
        ValueError: 가중치 길이가 가치 차원과 일치하지 않을 경우
    """
    if type(solution[0]) is list:
        solution = [solution[i].index(True) for i in range(len(solution))]

    if weights is None:
        weights = [1.0 for _ in range(len(problem["value"][0].values.tolist()))]

    value_dim = problem["value"][0].shape[0]
    if value_dim != len(weights):
        raise ValueError(f"len(weights) must be equal to value_dim. \n{len(weights)} != {value_dim}")

    print("Solution:")
    for i in range(len(solution)):
        print(f"{problem['cost'].index[i]} -> {problem['cost'].columns[solution[i]]}")
        print(f"Cost: {problem['cost'].iloc[i][solution[i]]}")
        print(f"Value: ")
        for value in problem["value"][i].iloc[:, solution[i]]:
            print(f"\t{value}")
        print()

    total_cost = get_cost(problem["cost"], solution)
    total_value = get_total_value(problem["value"], solution, value_weights=weights)

    print(f"Total Cost: {total_cost}")
    print(f"Total Value: {total_value}")


def display_problem(problem: dict):
    """
    주어진 문제를 출력합니다.

    Args:
        problem: 문제 딕셔너리 {"cost": DataFrame, "value": [DataFrame...]}
    """
    print(f"Problem:")
    print(problem["cost"])

    for i in range(len(problem["value"])):
        print(problem["cost"].index[i])
        print(problem["value"][i])
        print()


def _normalize_value_weights(values, value_weights=None):
    """
    가치 가중치를 표준화합니다.

    Args:
        values: 가치를 담은 데이터프레임 목록
        value_weights: 가치 차원에 대한 가중치. None인 경우 균등 분배

    Returns:
        표준화된 가중치 리스트 (합이 1이 되도록)
    """
    value_dim = values[0].shape[0]
    value_weights = [1.0 for _ in range(value_dim)] if value_weights is None else value_weights
    return (np.array(value_weights) / sum(value_weights)).tolist()
