import pandas as pd

import src.solver.cpsat as cpsat
import src.solver.scip as scip
from src.problem.strategy import make_random_problem

ALLOW_ZERO_STRATEGY = True

for n_item in [30, 50, 70, 100, 300, 500, 1000]:

    elapsed_time = []
    solver_error = []

    for i in range(10):
        if ALLOW_ZERO_STRATEGY:
            strategy_label = ["normal check", "advanced check", "change"]
            problem = make_random_problem(num_items=n_item,
                                          strategy_label=strategy_label,
                                          random_seed=1000 + i,
                                          allow_zero_strategy=True,
                                          strategy_count=len(strategy_label)
                                          )
        else:
            strategy_label = ["nothing", "normal check", "advanced check", "change"]
            problem = make_random_problem(num_items=n_item,
                                          strategy_label=strategy_label,
                                          random_seed=1000 + i,
                                          allow_zero_strategy=False,
                                          strategy_count=len(strategy_label)
                                          )

        sol_scip_cost, total_cost, total_value, t_scip_cost = (
            scip.solve_cost_constraint(problem, cost_constraint=1000, value_weights=None, allow_zero_strategy=ALLOW_ZERO_STRATEGY))
        print(f"SCIP Cost Constraint: {i}")
        print(f"Selected: {sol_scip_cost}")
        print(f"Total Cost: {total_cost}")
        print(f"Value : {total_value}")

        sol_cpsat_cost, total_cost, total_value, t_cpsat_cost = (
            cpsat.solve_cost_constraint(problem, cost_constraint=1000, value_weights=None, allow_zero_strategy=ALLOW_ZERO_STRATEGY))
        print(f"CP-SAT Cost Constraint: {i}")
        print(f"Selected: {sol_cpsat_cost}")
        print(f"Total Cost: {total_cost}")
        print(f"Value : {total_value}")

        sol_scip_reliability, total_cost, total_value, t_scip_reliability = (
            scip.solve_reliability_constraint(problem, reliability_constraint=[5 * n_item, 5 * n_item, 5 * n_item], allow_zero_strategy=ALLOW_ZERO_STRATEGY))
        print(f"SCIP Reliability Constraint: {i}")
        print(f"Selected: {sol_scip_reliability}")
        print(f"Total Cost: {total_cost}")
        print(f"Value : {total_value}")

        sol_cpsat_reliability, total_cost, total_value, t_cpsat_reliability = (
            cpsat.solve_reliability_constraint(problem, reliability_constraint=[5 * n_item, 5 * n_item, 5 * n_item], allow_zero_strategy=ALLOW_ZERO_STRATEGY))
        print(f"CP-SAT Reliability Constraint: {i}")
        print(f"Selected: {sol_cpsat_reliability}")
        print(f"Total Cost: {total_cost}")
        print(f"Value : {total_value}")

        print(f"Elapsed Time: {t_scip_cost}, {t_scip_reliability}, {t_cpsat_cost}, {t_cpsat_reliability}")
        print()
        print()

        solver_error.append([sol_scip_cost == sol_cpsat_cost, sol_cpsat_reliability == sol_scip_reliability])

        elapsed_time.append([t_scip_cost, t_cpsat_cost, t_scip_reliability, t_cpsat_reliability])

        if ALLOW_ZERO_STRATEGY:
            output_name = f"data/elapsed_time_{n_item}_zero.xlsx"
        else:
            output_name = f"data/elapsed_time_{n_item}.xlsx"

        pd.DataFrame(elapsed_time,
                     columns=["scip_cost", "cpsat_cost", "scip_reliability", "cpsat_reliability"]).to_excel(
            output_name, index=False)

        for i, times in enumerate(elapsed_time):
            print(f"{i}: {[f"{t:.4f}" for t in times]} sec : {solver_error[i]}")
