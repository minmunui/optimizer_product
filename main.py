import time

import pandas as pd
from openpyxl.utils.datetime import time_to_days

import src.solver.cpsat as cpsat
import src.solver.scip as scip
from src.problem.io import read_problem_from_excel, write_solution_to_excel, add_nothing_strategy
from src.problem.strategy import display_problem, make_random_problem

# problem = read_problem_from_excel("data/data.xlsx", cost_range="N2:Q42", value_range="A1:J42")
# problem = add_nothing_strategy(problem)

elapsed_time = []
solver_error = []

for i in range(100):
    problem = make_random_problem(num_items=50, strategy_label=["nothing", "normal check", "advanced check", "change"],
                                  random_seed=1000 + i)

    # display_problem(problem)

    sol_scip_cost, total_cost, total_value, t_scip_cost = (
        scip.solve_cost_constraint(problem, cost_constraint=1000, value_weights=None))
    print(f"SCIP Cost Constraint: {i}")
    print(f"Selected: {sol_scip_cost}")
    print(f"Total Cost: {total_cost}")
    print(f"Value : {total_value}")

    sol_cpsat_cost, total_cost, total_value, t_cpsat_cost = (
        cpsat.solve_cost_constraint(problem, cost_constraint=1000, value_weights=None))
    print(f"CP-SAT Cost Constraint: {i}")
    print(f"Selected: {sol_cpsat_cost}")
    print(f"Total Cost: {total_cost}")
    print(f"Value : {total_value}")

    sol_scip_reliability, total_cost, total_value, t_scip_reliability = (
        scip.solve_reliability_constraint(problem, reliability_constraint=[250, 250, 250]))
    print(f"SCIP Reliability Constraint: {i}")
    print(f"Selected: {sol_scip_reliability}")
    print(f"Total Cost: {total_cost}")
    print(f"Value : {total_value}")

    sol_cpsat_reliability, total_cost, total_value, t_cpsat_reliability = (
        cpsat.solve_reliability_constraint(problem, reliability_constraint=[250, 250, 250]))
    print(f"CP-SAT Reliability Constraint: {i}")
    print(f"Selected: {sol_cpsat_reliability}")
    print(f"Total Cost: {total_cost}")
    print(f"Value : {total_value}")

    print(f"Elapsed Time: {t_scip_cost}, {t_scip_reliability}, {t_cpsat_cost}, {t_cpsat_reliability}")
    print()
    print()

    solver_error.append([sol_scip_cost == sol_cpsat_cost, sol_cpsat_reliability == sol_scip_reliability])

    elapsed_time.append([t_scip_cost, t_cpsat_cost, t_scip_reliability, t_cpsat_reliability])

    pd.DataFrame(elapsed_time, columns=["scip_cost", "cpsat_cost", "scip_reliability", "cpsat_reliability"]).to_excel(
        "data/elapsed_time.xlsx", index=False)
#
# write_solution_to_excel("data/solution.xlsx", sheet_name="cpsat_cost_constraint", problem=problem,
#                         solution=sol_cpsat_cost)
#
# write_solution_to_excel("data/solution.xlsx", sheet_name="cpsat_reliability_constraint", problem=problem,
#                         solution=sol_cpsat_reliability)
#
# write_solution_to_excel("data/solution.xlsx", sheet_name="scip_cost_constraint", problem=problem,
#                         solution=sol_scip_cost)
#
# write_solution_to_excel("data/solution.xlsx", sheet_name="scip_reliability_constraint", problem=problem,
#                         solution=sol_scip_reliability)
for i, times in enumerate(elapsed_time):
    print(f"{i}: {[f"{t:.4f}" for t in times]} sec : {solver_error[i]}")
