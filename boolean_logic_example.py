from ortools.sat.python import cp_model

def main():
    model = cp_model.CpModel()
    variables = [model.NewIntVar(0, 1, 'var' + str(var_index)) for var_index in range(7)]
    ensureVarSumIsOneOfPossible(model, variables, [0, 1, 6, 7])

    solver = cp_model.CpSolver()
    solution_printer = VarArraySolutionPrinter(variables)
    status = solver.SearchForAllSolutions(model, solution_printer)
    print(solver.StatusName(status))

def ensureVarSumIsOneOfPossible(model, variables, possible_sums):
    """
        This function implements adding a disjunctive constraint to the model.
        Use it if there are a few known possible values for a sum of variables like
            (x0 + x1 + x2 + x3 + x4) == 3 OR
            (x0 + x1 + x2 + x3 + x4) == 4 OR
            (x0 + x1 + x2 + x3 + x4) == 5

        Args:
            model: The ORTools CpModel object for the constraint problem
            variables: The model variables in the constraint sum
            possible_sums: List of Integers for all possible values the 
    """
    decision_vars = []

    for possible_sum in possible_sums:
        decision_var = model.NewBoolVar('decisionVar' + \
                                        str(ensureVarSumIsOneOfPossible.num_decision_vars))
        decision_vars.append(decision_var)
        ensureVarSumIsOneOfPossible.num_decision_vars += 1

        # Add a sum constraint which is only active if the boolean decision variable is true
        model.Add(sum(variables) == possible_sum).OnlyEnforceIf(decision_var)

    # Add a constraint that only one boolean decision variable can be true at any given time
    model.Add(sum(decision_vars) == 1)

# Ensure unique decision variable names, although I don't think it actually matters
ensureVarSumIsOneOfPossible.num_decision_vars = 0

class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.variables = variables
        self.solution_count = 0

    def on_solution_callback(self):
        self.solution_count += 1
        print(str([self.Value(v) for v in self.variables]) + \
              ' ' + str(sum(self.Value(v) for v in self.variables)))

    def solution_count(self):
        return self.solution_count

def variableOnVariableConstraintExample():
    model = cp_model.CpModel()
    var1 = model.NewIntVar(0, 1, 'var1')
    var2 = model.NewIntVar(0, 1, 'var2')
    var3 = model.NewIntVar(0, 1, 'var3')
    var4 = model.NewIntVar(1, 2, 'var4')

    model.Add((var1 + var2) == (2 * var3 + var4))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    print(solver.StatusName(status))
    print(solver.Value(var1))
    print(solver.Value(var2))
    print(solver.Value(var3))
    print(solver.Value(var4))

if __name__ == '__main__':
    main()
