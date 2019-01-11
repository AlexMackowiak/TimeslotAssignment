from preference_input import readDoodlePreferences, readModMaxSectionPreferences
from ortools.sat.python import cp_model

DOODLE_PREFERRED_TIME = 'OK'
DOODLE_NOT_PREFERRED_TIME = '(OK)'
DOODLE_IMPOSSIBLE_TIME = ''
MIN_STUDENTS_PER_SECTION = 5
MAX_STUDENTS_PER_SECTION = 6

class PersonAssignedToTimeVariableWrapper:
    def __init__(self, net_id, time_index, is_preferred_time, constraint_programming_var):
        """
            Args:
                net_id: String for the netID of the student or moderator this CP variable represents
                time_index: Integer for the time slot this CP variable represents
                is_preferred_time: True if this person marked this time as preferred
                constraint_programming_var: The OR-Tools IntVar object being wrapped with extra data
        """
        self.net_id = net_id
        self.time_index = time_index
        self.is_preferred_time = is_preferred_time
        self.variable = constraint_programming_var

    def isTimeAssignedToPerson(self):
        """
            The output of this function should only be used after the linear programming solver
                has been run

            Returns:
                True if this person was assigned this time by the LP solver, false otherwise
        """
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
    (mod_variables, student_variables) = setupConstraintProgrammingVariables(model, mod_net_ids, mod_time_preferences, 
                                                                             student_net_ids, student_time_preferences)
    var_count = 0
    num_mods = len(mod_net_ids)
    num_students = len(student_net_ids)
    num_section_times = len(mod_time_preferences[0])

    for mod_index in range(num_mods):
        for time_index in range(num_section_times):
            if mod_variables[mod_index][time_index] is not None:
                var_count += 1

    for student_index in range(num_students):
        for time_index in range(num_section_times):
            if student_variables[student_index][time_index] is not None:
                var_count += 1

    print('Num mods: ' + str(num_mods))
    print('Num students: ' + str(num_students))
    print('Num section times: ' + str(num_section_times))
    print('Num time variables: ' + str(var_count))

    # The sum of all mod/time variables for a mod over all times must be <= max sections for that mod
    for mod_index in range(num_mods):
        model.Add(sum([mod_variables[mod_index][time_index].variable
                       for time_index in range(num_section_times)
                       if mod_variables[mod_index][time_index] is not None]) <= max_sections_per_mod[mod_index])

    # The sum of all mod/time variables for a time over all mods must be <= num rooms at that time
    # Assumes that there are always 3 rooms for now
    for time_index in range(num_section_times):
        model.Add(sum([mod_variables[mod_index][time_index].variable
                       for mod_index in range(num_mods)
                       if mod_variables[mod_index][time_index] is not None]) <= 3)

    # The sum of all student/time variables for a student over all times must be exactly 1
    for student_index in range(num_students):
        model.Add(sum([student_variables[student_index][time_index].variable
                       for time_index in range(num_section_times)
                       if student_variables[student_index][time_index] is not None]) == 1)
    
    # The sum of all student/time variables for a time over all students must be a function of
    #  the number of mods assigned to that time (this is where things get non-linear and complicated)
    num_decision_vars = 0
    for time_index in range(num_section_times):
        max_sections_for_time = 3

        mods_in_time = [mod_variables[mod_index][time_index].variable
                            for mod_index in range(num_mods)
                            if mod_variables[mod_index][time_index] is not None]
        students_in_time = [student_variables[student_index][time_index].variable
                            for student_index in range(num_students)
                            if student_variables[student_index][time_index] is not None]

        if (len(mods_in_time) == 0) or (len(students_in_time) == 0):
            continue

        # Need to create decision variables for the possible number of mods in this time beforehand
        num_sections_decision_vars = []
        for _ in range(max_sections_for_time + 1):
            num_sections_decision_vars.append(model.NewBoolVar('decision' + str(num_decision_vars)))
            num_decision_vars += 1

        # End goal is to create if then logic
        # If sum(mods_in_time) == 0 then sum(students_in_time) == 0
        # If sum(mods_in_time) == 1 then sum(students_in_time) == 5 or sum(students_in_time) == 6
        # Etc. the tricky bit is allowing the "or" logic in the second part
        for possible_num_sections_in_time in range(max_sections_for_time + 1):
            model.Add(sum(mods_in_time) == possible_num_sections_in_time)\
                 .OnlyEnforceIf(num_sections_decision_vars[possible_num_sections_in_time])

            possible_sum_decision_vars = []
            for possible_student_sum in range(MIN_STUDENTS_PER_SECTION * possible_num_sections_in_time,
                                              (MAX_STUDENTS_PER_SECTION * possible_num_sections_in_time) + 1):
                possible_sum_decision_var = model.NewBoolVar('decision' + str(num_decision_vars))
                possible_sum_decision_vars.append(possible_sum_decision_var)
                num_decision_vars += 1

                model.Add(sum(students_in_time) == possible_student_sum)\
                     .OnlyEnforceIf(possible_sum_decision_var)\
                     .OnlyEnforceIf(num_sections_decision_vars[possible_num_sections_in_time])

            # The sum of all decision vars for sum(mods_in_time) EXCEPT the current one
            #  and the decision vars for sum(students_in_time) must be 1
            # This enforces that either a different sum(mods_in_time) var is active, or the current "or" logic is
            model.Add((sum([num_sections_decision_vars[i] 
                            for i in range(max_sections_for_time + 1)
                            if i != possible_num_sections_in_time]) + \
                       sum(possible_sum_decision_vars)) == 1)

        # Ensure that exactly one of the sum(mods_in_time) decision vars is active
        model.Add(sum(num_sections_decision_vars) == 1)

    print('Num decision variables: ' + str(num_decision_vars))

    not_preferred_variables = []
    for time_index in range(num_section_times):
        for mod_index in range(num_mods):
            mod_time_var_wrapper = mod_variables[mod_index][time_index]
            if mod_time_var_wrapper is not None and not mod_time_var_wrapper.is_preferred_time:
                not_preferred_variables.append(mod_time_var_wrapper.variable)

        for student_index in range(num_students):
            student_time_var_wrapper = student_variables[student_index][time_index]
            if student_time_var_wrapper is not None and not student_time_var_wrapper.is_preferred_time:
                not_preferred_variables.append(student_time_var_wrapper.variable)
    model.Minimize(sum(not_preferred_variables))

    # Kick off the solver, and verify an optimal solution exists
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.StatusName(status))
    assert (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE)

    for time_index in range(num_section_times):
        mods_in_time = []
        for mod_index in range(num_mods):
            mod_time_var_wrapper = mod_variables[mod_index][time_index]
            if mod_time_var_wrapper is not None and solver.Value(mod_time_var_wrapper.variable) == 1:
                mods_in_time.append(mod_time_var_wrapper.net_id)

        students_in_time = []
        for student_index in range(num_students):
            student_time_var_wrapper = student_variables[student_index][time_index]
            if student_time_var_wrapper is not None and solver.Value(student_time_var_wrapper.variable) == 1:
                students_in_time.append(student_time_var_wrapper.net_id)

        print('Time ' + str(time_index) + ': ' + str(mods_in_time) + ' ' + str(students_in_time))

def setupConstraintProgrammingVariables(model, mod_net_ids, mod_time_preferences, student_net_ids, student_time_preferences):
    assert len(mod_time_preferences[0]) == len(student_time_preferences[0])

    mod_variables = []
    student_variables = []
    num_mods = len(mod_net_ids)
    num_students = len(student_net_ids)
    num_section_times = len(mod_time_preferences[0])    
    
    for mod_index in range(num_mods):
        mod_variables.append([])

        for time_index in range(num_section_times):
            mod_preference_for_time = mod_time_preferences[mod_index][time_index]
            
            if mod_preference_for_time != DOODLE_IMPOSSIBLE_TIME:
                is_preferred_time = (mod_preference_for_time == DOODLE_PREFERRED_TIME)
                cp_var_name = ('mod_' + str(mod_index) + ':time_' + str(time_index))
                constraint_programming_var = model.NewIntVar(0, 1, cp_var_name)
                variable_wrapper = PersonAssignedToTimeVariableWrapper(mod_net_ids[mod_index], time_index,
                                                                      is_preferred_time, constraint_programming_var)

                mod_variables[mod_index].append(variable_wrapper)
            else:
                mod_variables[mod_index].append(None)

    for student_index in range(num_students):
        student_variables.append([])

        for time_index in range(num_section_times):
            student_preference_for_time = student_time_preferences[student_index][time_index]
            
            if student_preference_for_time != DOODLE_IMPOSSIBLE_TIME:
                is_preferred_time = (student_preference_for_time == DOODLE_PREFERRED_TIME)
                cp_var_name = ('student_' + str(student_index) + ':time_' + str(time_index))
                constraint_programming_var = model.NewIntVar(0, 1, cp_var_name)
                variable_wrapper = PersonAssignedToTimeVariableWrapper(student_net_ids[student_index], time_index,
                                                                      is_preferred_time, constraint_programming_var)

                student_variables[student_index].append(variable_wrapper)
            else:
                student_variables[student_index].append(None)

    return mod_variables, student_variables
