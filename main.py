import src.solver.cpsat as cpsat
import src.solver.scip as scip
from src.problem.io import read_problem_from_excel, write_solution_to_excel, add_nothing_strategy
from src.problem.strategy import display_problem

problem = read_problem_from_excel("data/data.xlsx", cost_range="N2:Q42", value_range="A1:J42")
problem = add_nothing_strategy(problem)

display_problem(problem)

sol_scip_cost, total_cost, total_value = scip.solve_cost_constraint_with_scip(problem, cost_constraint=40_000,
                                                                              value_weights=None)
print(f"Selected: {sol_scip_cost}")
print(f"Total Cost: {total_cost}")
print(f"Value : {total_value}")

sol_scip_reliability, total_cost, total_value = scip.solve_reliability_constraint_with_scip(problem,
                                                                                            reliability_constraint=[
                                                                                                0.2, 2000,
                                                                                                44500])
print(f"Selected: {sol_scip_reliability}")
print(f"Total Cost: {total_cost}")
print(f"Value : {total_value}")

sol_cpsat_cost, total_cost, total_value = cpsat.solve_cost_constraint_with_cpsat(problem,
                                                                                 cost_constraint=40_000,
                                                                                 value_weights=None)
print(f"Selected: {sol_cpsat_cost}")
print(f"Total Cost: {total_cost}")
print(f"Value : {total_value}")

sol_cpsat_reliability, total_cost, total_value = cpsat.solve_reliability_constraint_with_cpsat(problem,
                                                                                               reliability_constraint=[
                                                                                                0.2, 2000,
                                                                                                44500])
print(f"Selected: {sol_cpsat_reliability}")
print(f"Total Cost: {total_cost}")
print(f"Value : {total_value}")



write_solution_to_excel("data/solution.xlsx", sheet_name="cpsat_cost_constraint", problem= problem, solution = sol_cpsat_cost)

write_solution_to_excel("data/solution.xlsx", sheet_name="cpsat_reliability_constraint", problem= problem, solution = sol_cpsat_reliability)

write_solution_to_excel("data/solution.xlsx", sheet_name="scip_cost_constraint", problem= problem, solution = sol_scip_cost)

write_solution_to_excel("data/solution.xlsx", sheet_name="scip_reliability_constraint",problem= problem, solution = sol_scip_reliability)