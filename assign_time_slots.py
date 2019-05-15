import time
import config
from ortools.sat.python import cp_model
from csv_input import readDoodlePreferences, readModMaxSectionPreferences, readSectionTimeInfo

DOODLE_PREFERRED_TIME = 'OK'
DOODLE_NOT_PREFERRED_TIME = '(OK)'
DOODLE_IMPOSSIBLE_TIME = ''
MIN_STUDENTS_PER_SECTION = 5
MAX_STUDENTS_PER_SECTION = 6

class PersonTimeVariableWrapper:
    """ Wrapper class around a CP variable that represents an assignment of a mod/student to a time """

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

    def isTimeAssignedToPerson(self, solver):
        """
            The output of this function should only be used after the linear programming solver
                has been run

            Returns:
                True if this person was assigned this time by the CP solver, false otherwise
        """
        return (solver.Value(self.variable) != 0)

def assignModeratorsAndStudents(mod_doodle_poll_csv_path, mod_max_section_csv_path, student_doodle_poll_csv_path,
                                section_times_csv_path=None):
    """
        Args:
            mod_doodle_poll_csv_path: The file path to the Doodle poll for the moderators in .csv format
            mod_max_section_csv_path: The file path to the max sections .csv file
            student_doodle_poll_csv_path: The file path to the Doodle poll for the students in .csv format
            section_times_csv_path: The file path to the .csv file containing info on section times and rooms
                                    available for each time. If None, 3 rooms per time is assumed

        Returns:
            mods_assigned_to_times: List of List of Strings, each entry is all net IDs of the moderators assigned
                                        to that time index
            students_assigned_to_times: List of List of Strings, each entry is all net IDs of the moderators assigned
                                        to that time index
    """
    (mod_net_ids, mod_time_preferences) = readDoodlePreferences(mod_doodle_poll_csv_path)
    max_sections_per_mod = readModMaxSectionPreferences(mod_max_section_csv_path, mod_net_ids)
    (student_net_ids, student_time_preferences) = readDoodlePreferences(student_doodle_poll_csv_path)
    assert len(mod_time_preferences[0]) == len(student_time_preferences[0])

    model = cp_model.CpModel()
    mod_time_variables = setupConstraintProgrammingVariables(model, mod_net_ids,
                                                             mod_time_preferences, True)
    student_time_variables = setupConstraintProgrammingVariables(model, student_net_ids,
                                                                 student_time_preferences, False)

    num_section_times = len(mod_time_variables[0])
    max_sections_per_time = [3] * num_section_times
    if section_times_csv_path != None:
        (_, max_sections_per_time) = readSectionTimeInfo(section_times_csv_path)

    var_count = 0
    num_mods = len(mod_net_ids)
    num_students = len(student_net_ids)
    num_section_times = len(mod_time_preferences[0])

    for mod_index in range(num_mods):
        for time_index in range(num_section_times):
            if mod_time_variables[mod_index][time_index] is not None:
                var_count += 1

    for student_index in range(num_students):
        for time_index in range(num_section_times):
            if student_time_variables[student_index][time_index] is not None:
                var_count += 1

    print('Num mods:', num_mods)
    print('Num students:', num_students)
    print('Num section times:', num_section_times)
    print('Num person/time variables:', var_count)

    addMaxSectionsPerModConstraint(model, mod_time_variables, max_sections_per_mod)
    addMaxSectionsPerSectionTimeConstraint(model, mod_time_variables, max_sections_per_time)
    addSectionsPerStudentConstraint(model, student_time_variables)
    addStudentsPerSectionTimeConstraint(model, mod_time_variables, student_time_variables, max_sections_per_time)
    addFunctionToMinimize(model, mod_time_variables, student_time_variables)

    # Kick off the solver, and verify an optimal solution exists
    solver = cp_model.CpSolver()
    solution_counter = SolutionCounter()
    status = solver.SolveWithSolutionCallback(model, solution_counter)
    print(solver.StatusName(status))
    print("Solutions considered:", solution_counter.solution_count)
    assert (status == cp_model.OPTIMAL) # or (status == cp_model.FEASIBLE)
    return extractModAndStudentAssignments(solver, mod_time_variables, student_time_variables)

def setupConstraintProgrammingVariables(model, net_ids, time_preferences, is_mod_data):
    """
        Creates the constraint programming variables for the model of the moderator/student assignment problem

        Args:
            model: The CpModel object that represents the constraints of the problem
            net_ids: List of Strings for each person's net ID
            time_preferences: List where each entry is all the time preferences for one person
    """
    num_people = len(net_ids)
    num_section_times = len(time_preferences[0])
    person_time_variables = []

    for person_index in range(num_people):
        person_time_variables.append([])

        for time_index in range(num_section_times):
            preference_for_time = time_preferences[person_index][time_index]

            if preference_for_time != DOODLE_IMPOSSIBLE_TIME:
                is_preferred_time = (preference_for_time == DOODLE_PREFERRED_TIME)
                cp_var_prefix = 'mod' if is_mod_data else 'student'
                cp_var_name = (cp_var_prefix + str(person_index) + ':time_' + str(time_index))

                constraint_programming_var = model.NewIntVar(0, 1, cp_var_name)
                variable_wrapper = PersonTimeVariableWrapper(net_ids[person_index], time_index,
                                                             is_preferred_time, constraint_programming_var)

                person_time_variables[person_index].append(variable_wrapper)
            else:
                person_time_variables[person_index].append(None)

    return person_time_variables

def addMaxSectionsPerModConstraint(model, mod_time_variables, max_sections_per_mod):
    """
        Adds the constraint that the total number of section times a mod is assigned must be
            less than or equal to their preferred maximum number of sections

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            max_sections_per_mod: List of Integer, each entry is the max sections for that mod_index
    """
    num_mods = len(mod_time_variables)
    num_section_times = len(mod_time_variables[0])

    for mod_index in range(num_mods):
        all_time_vars_for_mod = sum([mod_time_variables[mod_index][time_index].variable
                                     for time_index in range(num_section_times)
                                     if mod_time_variables[mod_index][time_index] is not None])

        if config.assign_exact_max_sections:
            model.Add(all_time_vars_for_mod == max_sections_per_mod[mod_index])
        else:
            model.Add(1 <= all_time_vars_for_mod)
            model.Add(all_time_vars_for_mod <= max_sections_per_mod[mod_index])

def addMaxSectionsPerSectionTimeConstraint(model, mod_time_variables, max_sections_per_time):
    """
        Adds the constraint that the number of moderators assigned to a section time must be
            less than or equal to the maximum sections that can happen at that time. This is
            usually bounded by the number of rooms available (3 for every time by default)

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            max_sections_per_time: List of Integer where each index represents the number of rooms
                                    available at that time index
    """
    num_mods = len(mod_time_variables)
    num_section_times = len(mod_time_variables[0])

    for time_index in range(num_section_times):
        all_mod_vars_for_time = sum([mod_time_variables[mod_index][time_index].variable
                                     for mod_index in range(num_mods)
                                     if mod_time_variables[mod_index][time_index] is not None])

        model.Add(all_mod_vars_for_time <= max_sections_per_time[time_index])

def addSectionsPerStudentConstraint(model, student_time_variables):
    """
        Adds the constraint that the number of sections assigned to a student must be exactly 1

        Args:
            model: The CpModel object that represents the constraints of the problem
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student
    """
    num_students = len(student_time_variables)
    num_section_times = len(student_time_variables[0])

    for student_index in range(num_students):
        all_student_vars_for_time = sum([student_time_variables[student_index][time_index].variable
                                         for time_index in range(num_section_times)
                                         if student_time_variables[student_index][time_index] is not None])

        model.Add(all_student_vars_for_time == 1)

def addStudentsPerSectionTimeConstraint(model, mod_time_variables, student_time_variables, max_sections_for_times):
    """
        This is where things get complicated and why linear programming cannot solve the system as a whole
        A little about constraint programming: It's an NP hard problem, so on some level it is just trying
        every possible solution

        Consider the mod and student vars in one specific section time, and call the current solution
        being tried curr_sol, this function does 3 things:
        1. If sum(mod_vars) in curr_sol = X then it forces sum(student_vars) in curr_sol to be Y or Z
            where Y or Z is an appropriate student count for the number of mods
            (i.e. 1 mod -> (5 or 6 students), 2 mods -> (10, 11, or 12 students))

        2. Bidirectional implication
           if sum(student_vars) in curr_sol is Y or Z it forces sum(mod_vars) in curr_sol to be X

        3. Adds the constraint that one of these paths must be taken, that is it will not consider
            solutions that do not match either of the above criteria

        This is repeated for every time index, and adds ~14 more variables to the system per section time

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student
            max_sections_for_times: List of Integer where each index represents the number of rooms
                                    available at that time index
    """
    num_mods = len(mod_time_variables)
    num_students = len(student_time_variables)
    num_section_times = len(mod_time_variables[0])
    num_decision_vars = 0

    for time_index in range(num_section_times):
        max_sections_for_time = max_sections_for_times[time_index]

        mods_in_time = [mod_time_variables[mod_index][time_index].variable
                            for mod_index in range(num_mods)
                            if mod_time_variables[mod_index][time_index] is not None]
        students_in_time = [student_time_variables[student_index][time_index].variable
                            for student_index in range(num_students)
                            if student_time_variables[student_index][time_index] is not None]

        if (len(mods_in_time) == 0) or (len(students_in_time) == 0):
            continue # This time index will never have a section

        # Need to create decision variables for the possible number of mods in this time beforehand
        # A decision variable can take two values: 0 or 1, where 1 indicates the "decision" was taken
        #  corresponding to whatever path of other variable constraints the decision variable represents
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

def addFunctionToMinimize(model, mod_time_variables, student_time_variables):
    """
        Adds the objective function to minimize to the model
        This is currently just a basic implementation weighting all not preferred times the same

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student
    """
    num_mods = len(mod_time_variables)
    num_students = len(student_time_variables)
    num_section_times = len(mod_time_variables[0])
    not_preferred_variables = []

    for time_index in range(num_section_times):
        for mod_index in range(num_mods):
            mod_time_var_wrapper = mod_time_variables[mod_index][time_index]
            if mod_time_var_wrapper is not None and not mod_time_var_wrapper.is_preferred_time:
                #coefficient = ((MAX_STUDENTS_PER_SECTION + 1) * num_students) + (num_mods - mod_index)
                coefficient = 1
                not_preferred_variables.append(coefficient * mod_time_var_wrapper.variable)

        for student_index in range(num_students):
            student_time_var_wrapper = student_time_variables[student_index][time_index]
            if student_time_var_wrapper is not None and not student_time_var_wrapper.is_preferred_time:
                #coefficient = (num_students - student_index)
                coefficient = 1
                not_preferred_variables.append(coefficient * student_time_var_wrapper.variable)

    model.Minimize(sum(not_preferred_variables))

def extractModAndStudentAssignments(solver, mod_time_variables, student_time_variables):
    """
        Args:
            solver: The cp_model.CpSolver object which previously solved the constraint problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student

        Returns:
            mods_assigned_to_times: List of List of Strings, each entry is all net IDs of the moderators assigned
                                        to that time index
            students_assigned_to_times: List of List of Strings, each entry is all net IDs of the moderators assigned
                                        to that time index
    """
    num_mods = len(mod_time_variables)
    num_students = len(student_time_variables)
    num_section_times = len(mod_time_variables[0])
    mods_assigned_to_times = []
    students_assigned_to_times = []
    num_not_preferred_mod_times = 0
    num_not_preferred_student_times = 0

    for time_index in range(num_section_times):
        mods_assigned_to_times.append([])
        for mod_index in range(num_mods):
            mod_time_var_wrapper = mod_time_variables[mod_index][time_index]
            if mod_time_var_wrapper is not None and mod_time_var_wrapper.isTimeAssignedToPerson(solver):
                if not mod_time_var_wrapper.is_preferred_time:
                    num_not_preferred_mod_times += 1
                mods_assigned_to_times[time_index].append(mod_time_var_wrapper.net_id)

        students_assigned_to_times.append([])
        for student_index in range(num_students):
            student_time_var_wrapper = student_time_variables[student_index][time_index]
            if student_time_var_wrapper is not None and student_time_var_wrapper.isTimeAssignedToPerson(solver):
                if not student_time_var_wrapper.is_preferred_time:
                    num_not_preferred_student_times += 1
                students_assigned_to_times[time_index].append(student_time_var_wrapper.net_id)

    print('Mods assigned to not preferred time: ' + str(num_not_preferred_mod_times))
    print('Students assigned to not preferred time: ' + str(num_not_preferred_student_times))

    return mods_assigned_to_times, students_assigned_to_times

def currentMillis():
    return int(round(time.time() * 1000))

class SolutionCounter(cp_model.CpSolverSolutionCallback):
    """ Simple callback class to count the number of solutions considered """

    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.solution_count = 0
        self.millis_at_last_solution = currentMillis()

    def on_solution_callback(self):
        self.solution_count += 1
        millis_since_last_solution = (currentMillis() - self.millis_at_last_solution)
        seconds_since_last_solution = (millis_since_last_solution / 1000.0)
        print('Solution found, time since last: ' + str(seconds_since_last_solution) + ' seconds')
        self.millis_at_last_solution = currentMillis()
