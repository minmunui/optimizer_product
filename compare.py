"""
시간을 측정하기 위한 코드
랜덤한 문제를 생성하여 SCIP와 CP-SAT의 성능을 비교하
"""

import pandas as pd

import src.solver.cpsat as cpsat
import src.solver.scip as scip
from src.problem.io import add_nothing_strategy
from src.problem.strategy import make_random_problem

for n_item in [1000, 1500, 2000]:

    total_elapsed_time = []
    total_obj = []

    strategy_label = ["change", "advanced check", "normal check"]
    problems = [make_random_problem(num_items=n_item,
                                    strategy_label=strategy_label,
                                    random_seed=999 + i,
                                    allow_zero_strategy=True,
                                    strategy_count=len(strategy_label)
                                    ) for i in range(5)]
    for i, problem in enumerate(problems):

        print(f"========================== PROBLEM {i} ==========================")

        problem_obj = []
        problem_values = []
        problem_elapsed_times = []

        for allow_zero_strategy in [True, False]:
            print(f"=========================== ALLOW ZERO STRATEGY {allow_zero_strategy} ==========================")
            print(problem["cost"])
            for value in problem["value"]:
                print(value)

            print(f" ------------------- SCIP Cost Constraint: {i} ------------------- ")
            sol_scip_cost, total_cost, total_value, elapsed_time = (
                scip.solve_cost_constraint(problem, cost_constraint=2 * n_item, value_weights=None,
                                           allow_zero_strategy=allow_zero_strategy))
            print(f"Selected: {sol_scip_cost}")
            print(f"Total Cost: {total_cost}")
            print(f"Value : {total_value}")

            problem_obj.append(total_value)
            problem_elapsed_times.append(elapsed_time)

            print(f" ------------------- CP-SAT Cost Constraint: {i} ------------------- ")
            sol_cpsat_cost, total_cost, total_value, elapsed_time = (
                cpsat.solve_cost_constraint(problem, cost_constraint=2 * n_item, value_weights=None,
                                            allow_zero_strategy=allow_zero_strategy))
            print(f"Selected: {sol_cpsat_cost}")
            print(f"Total Cost: {total_cost}")
            print(f"Value : {total_value}")

            problem_obj.append(total_value)
            problem_elapsed_times.append(elapsed_time)

            print(f" ------------------- SCIP Reliability Constraint: {i} ------------------- ")
            sol_scip_reliability, total_cost, total_value, elapsed_time = (
                scip.solve_reliability_constraint(problem,
                                                  reliability_constraint=[2.5 * n_item, 2.5 * n_item, 2.5 * n_item],
                                                  allow_zero_strategy=allow_zero_strategy))
            print(f"Selected: {sol_scip_reliability}")
            print(f"Total Cost: {total_cost}")
            print(f"Value : {total_value}")

            problem_obj.append(total_cost)
            problem_elapsed_times.append(elapsed_time)

            print(f" ------------------- CP-SAT Reliability Constraint: {i} ------------------- ")
            sol_cpsat_reliability, total_cost, total_value, elapsed_time = (
                cpsat.solve_reliability_constraint(problem,
                                                   reliability_constraint=[2.5 * n_item, 2.5 * n_item, 2.5 * n_item],
                                                   allow_zero_strategy=allow_zero_strategy))
            print(f"Selected: {sol_cpsat_reliability}")
            print(f"Total Cost: {total_cost}")
            print(f"Value : {total_value}")

            problem_obj.append(total_cost)
            problem_elapsed_times.append(elapsed_time)

            if allow_zero_strategy:
                problem = add_nothing_strategy(problem)

        total_elapsed_time.append(problem_elapsed_times)
        total_obj.append(problem_obj)

    time_output_name = f"data/elapsed_time_{n_item}.xlsx"
    costs_output_name = f"data/costs_n_values_{n_item}.xlsx"

    pd.DataFrame(total_elapsed_time,
                 columns=["scip_cost_zero",
                          "cpsat_cost_zero",
                          "scip_reliability_zero",
                          "cpsat_reliability_zero",
                          "scip_cost",
                          "cpsat_cost",
                          "scip_reliability",
                          "cpsat_reliability"
                          ]).to_excel(
        time_output_name, index=False)

    pd.DataFrame(total_obj,
                 columns=["scip_cost_zero",
                          "cpsat_cost_zero",
                          "scip_reliability_zero",
                          "cpsat_reliability_zero",
                          "scip_cost",
                          "cpsat_cost",
                          "scip_reliability",
                          "cpsat_reliability"
                          ]).to_excel(
        costs_output_name, index=False)
