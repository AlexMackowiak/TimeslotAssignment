from preference_input import readDoodlePreferences, readModMaxSectionPreferences
from ortools.sat.python import cp_model

DOODLE_PREFERRED_TIME = 'OK'
DOODLE_NOT_PREFERRED_TIME = '(OK)'
DOODLE_IMPOSSIBLE_TIME = ''
MIN_STUDENTS_PER_SECTION = 5
MAX_STUDENTS_PER_SECTION = 6

class ModStudentTimeVariableWrapper:
    def __init__(self, mod_net_id, student_net_id, time_index, 
                 is_preferred_mod_time, is_preferred_student_time, constraint_programming_var):
        self.mod_net_id = mod_net_id
        self.student_net_id = student_net_id
        self.time_index = time_index
        self.is_preferred_mod_time = is_preferred_mod_time
        self.is_preferred_student_time = is_preferred_student_time
        self.variable = constraint_programming_var

    def isTimeAssignedToModAndStudent(self):
        return (self.variable.solution_value() != 0)

def assignModeratorsAndStudents(mod_doodle_poll_csv_path, mod_max_section_csv_path, student_doodle_poll_csv_path):
    """
        Args:
            mod_doodle_poll_csv_path: The file path to the Doodle poll for the moderators in .csv format
            mod_max_section_csv_path: The file path to the max sections .csv file
            student_doodle_poll_csv_path: The file path to the Doodle poll for the students in .csv format
    """
    (mod_net_ids, mod_time_preferences) = readDoodlePreferences(mod_doodle_poll_csv_path)
    max_sections_per_mod = readModMaxSectionPreferences(mod_max_section_csv_path, mod_net_ids)
    (student_net_ids, student_time_preferences) = readDoodlePreferences(student_doodle_poll_csv_path)

    model = cp_model.CpModel()
    cp_variables = setupConstraintProgrammingVariables(model, mod_net_ids, mod_time_preferences, 
                                                       student_net_ids, student_time_preferences)

    var_count = 0
    num_mods = len(mod_net_ids)
    num_students = len(student_net_ids)
    num_section_times = len(mod_time_preferences[0])

    for mod_index in range(num_mods):
        for student_index in range(num_students):
            for time_index in range(num_section_times):
                if cp_variables[mod_index][student_index][time_index] is not None:
                    var_count += 1
    print('Mod/Student/TIme Variable count: ' + str(var_count))
 
    # Every student needs exactly one moderator at exactly one time
    # The sum of all mod/time variables for one specific student must be 1
    for student_index in range(num_students):
        constraint = model.Add(sum([sum([cp_variables[mod_index][student_index][time_index].variable 
                                    for time_index in range(num_section_times)
                                    if cp_variables[mod_index][student_index][time_index] != None])
                                for mod_index in range(num_mods)]) == 1)
        assert (constraint is not None)

    # Pick a moderator
    for mod_index in range(num_mods):
        # The sum of all times for a student with this moderator should be 0 or 1
        # It is 0 if the student was not assigned this moderator
        for student_index in range(num_students):
            student_time_vars = [cp_variables[mod_index][student_index][time_index].variable
                                 for time_index in range(num_section_times)
                                 if cp_variables[mod_index][student_index][time_index] != None]

            if len(student_time_vars) > 0:
                ensureVarSumIsOneOfPossible(model, student_time_vars, [0, 1])

        # The sum of all students in any given time for this moderator should be 0, 5, or 6
        for time_index in range(num_section_times):
            time_student_vars = [cp_variables[mod_index][student_index][time_index].variable
                                 for student_index in range(num_students)
                                 if cp_variables[mod_index][student_index][time_index] != None]

            if len(time_student_vars) > 0:
                ensureVarSumIsOneOfPossible(model, time_student_vars,
                                            [0, MIN_STUDENTS_PER_SECTION, MAX_STUDENTS_PER_SECTION])

        # The sum of all student/time variables for a moderator should be a function of
        #  the max section preference for the moderator
        max_sections_for_this_mod = max_sections_per_mod[mod_index]
        possible_student_sums = getPossibleStudentSums(max_sections_for_this_mod)
        student_time_vars = [sum([cp_variables[mod_index][student_index][time_index].variable
                                  for time_index in range(num_section_times)
                                  if cp_variables[mod_index][student_index][time_index] != None])
                                for student_index in range(num_students)]

        ensureVarSumIsOneOfPossible(model, student_time_vars, possible_student_sums)

    # Pick a section time
    for time_index in range(num_section_times):
        # The sum of all moderators for a student with this time should be 0 or 1
        for student_index in range(num_students):
            student_mod_vars = [cp_variables[mod_index][student_index][time_index].variable
                                for mod_index in range(num_mods)
                                if cp_variables[mod_index][student_index][time_index] != None]

            if len(student_mod_vars) > 0:
                ensureVarSumIsOneOfPossible(model, student_mod_vars, [0, 1])
            
        # The sum of all students for a moderator with this time should be 0, 5, or 6
        for mod_index in range(num_mods):
            mod_student_vars = [cp_variables[mod_index][student_index][time_index].variable
                                for student_index in range(num_students)
                                if cp_variables[mod_index][student_index][time_index] != None]

            if len(mod_student_vars) > 0:
                ensureVarSumIsOneOfPossible(model, mod_student_vars, 
                                            [0, MIN_STUDENTS_PER_SECTION, MAX_STUDENTS_PER_SECTION])

        # The sum of all mod/student variables for a time should be a function of the 
        #  number of rooms at that time
        # Assuming this is 3 for all times at the moment
        possible_student_sums = getPossibleStudentSums(3)
        student_mod_vars = [sum([cp_variables[mod_index][student_index][time_index].variable
                                 for mod_index in range(num_mods)
                                 if cp_variables[mod_index][student_index][time_index] != None])
                                for student_index in range(num_students)]

        ensureVarSumIsOneOfPossible(model, student_time_vars, possible_student_sums)

    print('Num decision variables: ' + str(ensureVarSumIsOneOfPossible.num_decision_vars))

    # Kick off the solver, and verify an optimal solution exists
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.StatusName(status))
    assert (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE)

    for mod_index in range(num_mods):
        for time_index in range(num_section_times):
            students_for_mod_in_time = []

            for student_index in range(num_students):
                mod_student_time_var_wrapper = cp_variables[mod_index][student_index][time_index]

                if mod_student_time_var_wrapper is not None:
                    if solver.Value(mod_student_time_var_wrapper.variable) == 1:
                        students_for_mod_in_time.append(mod_student_time_var_wrapper.student_net_id)

            if len(students_for_mod_in_time) > 0:
                print('Mod ' + mod_net_ids[mod_index] + ' has time ' + str(time_index) +\
                      ' with students ' + str(students_for_mod_in_time))
                    

def setupConstraintProgrammingVariables(model, mod_net_ids, mod_time_preferences, student_net_ids, student_time_preferences):
    num_mods = len(mod_net_ids)
    num_students = len(student_net_ids)
    num_section_times = len(mod_time_preferences[0])

    cp_variables = []

    for mod_index in range(num_mods):
        cp_variables.append([])

        for student_index in range(num_students):
            cp_variables[mod_index].append([])

            for time_index in range(num_section_times):
                mod_preference_for_time = mod_time_preferences[mod_index][time_index]
                student_preference_for_time = student_time_preferences[student_index][time_index]
                
                if mod_preference_for_time != DOODLE_IMPOSSIBLE_TIME and \
                    student_preference_for_time != DOODLE_IMPOSSIBLE_TIME:
                    
                    is_preferred_mod_time = (mod_preference_for_time == DOODLE_PREFERRED_TIME)
                    is_preferred_student_time = (student_preference_for_time == DOODLE_PREFERRED_TIME)
                    cp_var_name = ('mod_' + str(mod_index) + ':student_' + str(student_index) + 'time_' + str(time_index))
                    constraint_programming_var = model.NewIntVar(0, 1, cp_var_name)
                    variable_wrapper = ModStudentTimeVariableWrapper(mod_net_ids[mod_index], student_net_ids[student_index],
                                                                     time_index, is_preferred_mod_time, is_preferred_student_time,
                                                                     constraint_programming_var)

                    cp_variables[mod_index][student_index].append(variable_wrapper)
                else:
                    cp_variables[mod_index][student_index].append(None)

    return cp_variables

def addNotPreferredTimeFunction(lp_solver, variables_for_each_person):
    """
        Adds the function to minimize to the LP solver, mathematically this function is specified as
            minimize f where f = (the sum of all person/time assignment variables where the time is not preferred)
        This means the LP solver can pick preferred times for free, but choosing not preferred times incurs a cost

        Args:
            lp_solver: The pywraplp.Solver object which will solve the linear programming assignment problem
            variables_for_each_persono: List where each entry is a List of type PersonAssignedToTimeVariableWrapper
                                            which represents all person/time variables for a single person
    """
    lp_objective_function = lp_solver.Objective()
    lp_objective_function.SetMinimization()

    for times_that_work_for_person in variables_for_each_person:
        for person_section_time_var_wrapper in times_that_work_for_person:
            is_preferred_time = (person_section_time_var_wrapper.is_preferred_time)

            if not is_preferred_time:
                lp_objective_function.SetCoefficient(person_section_time_var_wrapper.variable, 1)

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


def getPossibleStudentSums(max_num_sections):
    """
        Returns all possible numbers of students for every number of sections from 
            0 to max_num_sections to be filled

        Args:
            max_num_sections: The maximum number of sections to be filled

        Returns:
            Set of Integers for all valid student sums in a section time with up to max_num_sections
    """
    possible_sums = set()

    for num_sections in range(max_num_sections + 1):
        for possible_student_sum in range(MIN_STUDENTS_PER_SECTION * num_sections,
                                          (MAX_STUDENTS_PER_SECTION * num_sections) + 1):
            possible_sums.add(possible_student_sum)

    return possible_sums
