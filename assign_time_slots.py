import config
import random
import time
from csv_input import readDoodlePreferences, readModMaxSectionPreferences, readSectionTimeInfo
from constraints import addMaxSectionsPerModConstraint, addMaxSectionsPerSectionTimeConstraint,\
                        addSectionsPerStudentConstraint, addStudentsPerSectionTimeConstraint
from greedy_preselect import greedyPreselectSections
from objective_functions import addFunctionToMinimize
from ortools.sat.python import cp_model

DOODLE_PREFERRED_TIME = 'OK'
DOODLE_NOT_PREFERRED_TIME = '(OK)'
DOODLE_IMPOSSIBLE_TIME = ''

class PersonTimeVariableWrapper:
    """ Wrapper class around a CP variable that represents an assignment of a mod/student to a time """

    def __init__(self, net_id, time_index, is_preferred_time, is_impossible_time, constraint_programming_var):
        """
            Args:
                net_id: String for the netID of the student or moderator this CP variable represents
                time_index: Integer for the time slot this CP variable represents
                is_preferred_time: True if this person marked this time as preferred
                is_impossible_time: True if this person marked this time as impossible
                constraint_programming_var: The OR-Tools IntVar object being wrapped with extra data
        """
        self.net_id = net_id
        self.time_index = time_index
        self.is_preferred_time = is_preferred_time
        self.is_impossible_time = is_impossible_time
        self.variable = constraint_programming_var

    def isTimeAssignedToPerson(self, solver):
        """
            The output of this function should only be used after the constraint programming solver
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
    # Read in all of the input files and get the constraint programming model
    (model, mod_time_variables, student_time_variables,
     max_sections_per_mod, max_sections_per_time) = getModelFromInputFiles(**locals())

    # Attempt to greedy preselect some sections if specified in config and then add CP constraints
    num_greedy_sections = greedyPreselectSections(model, mod_time_variables, student_time_variables,
                                                  max_sections_per_time, max_sections_per_mod)
    print(f"Greedy selected {num_greedy_sections} sections")
    addMaxSectionsPerModConstraint(model, mod_time_variables, max_sections_per_mod)
    addMaxSectionsPerSectionTimeConstraint(model, mod_time_variables, max_sections_per_time)
    addSectionsPerStudentConstraint(model, student_time_variables)
    addStudentsPerSectionTimeConstraint(model, mod_time_variables, student_time_variables, max_sections_per_time)
    addFunctionToMinimize(model, mod_time_variables, student_time_variables, sum(max_sections_per_mod))

    # Kick off the solver, and verify an optimal solution exists
    solver = cp_model.CpSolver()
    solution_counter = SolutionCounter()
    status = solver.SolveWithSolutionCallback(model, solution_counter)

    # Print and verify properties of the found solution
    print(solver.StatusName(status))
    print("Num solutions considered:", solution_counter.solution_count)
    print("Objective value:", round(solver.ObjectiveValue(), 3))

    assert (status != cp_model.INFEASIBLE)
    if config.only_allow_optimal_solutions:
        if (status != cp_model.OPTIMAL):
            print("Run with config.only_allow_optimal_solutions=False to allow terminating early")
            assert (status == cp_model.OPTIMAL)
    elif status == cp_model.FEASIBLE:
        for _ in range(10):
            print("WARNING: CPSolver terminated early, solution is not optimal")

    return extractModAndStudentAssignments(solver, mod_time_variables, student_time_variables)

def getModelFromInputFiles(mod_doodle_poll_csv_path, mod_max_section_csv_path, student_doodle_poll_csv_path,
                           section_times_csv_path):
    """
        Reads in the .csv files to create all PersonTimeVariable objects needed in the CP solver

        Args:
            mod_doodle_poll_csv_path: The file path to the Doodle poll for the moderators in .csv format
            mod_max_section_csv_path: The file path to the max sections .csv file
            student_doodle_poll_csv_path: The file path to the Doodle poll for the students in .csv format
            section_times_csv_path: The file path to the .csv file containing info on section times and rooms
                                    available for each time. If None, 3 rooms per time is assumed

        Returns:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student
            max_sections_per_time: List of Integer where each index represents the number of rooms
                                    available at that time index
            max_sections_per_mod: List of Integer, each entry is the max sections for that mod_index
    """
    (mod_net_ids, mod_time_preferences) = readDoodlePreferences(mod_doodle_poll_csv_path)
    max_sections_per_mod = readModMaxSectionPreferences(mod_max_section_csv_path, mod_net_ids)
    (student_net_ids, student_time_preferences) = readDoodlePreferences(student_doodle_poll_csv_path)
    assert len(mod_time_preferences[0]) == len(student_time_preferences[0])

    # Set up the constraint programming model for each student/moderator at the times that work for them
    model = cp_model.CpModel()
    mod_time_variables = setupConstraintProgrammingVariables(model, mod_net_ids,
                                                             mod_time_preferences, True)
    student_time_variables = setupConstraintProgrammingVariables(model, student_net_ids,
                                                                 student_time_preferences, False)
    num_section_times = len(mod_time_variables[0])
    max_sections_per_time = [3] * num_section_times
    if section_times_csv_path != None:
        (_, rooms_in_each_time) = readSectionTimeInfo(section_times_csv_path)
        max_sections_per_time = [sum(room_at_time.max_sections for room_at_time in rooms_in_each_time[time_index])
                                 for time_index in range(num_section_times)]

    printProblemInfo(mod_net_ids, student_net_ids, mod_time_preferences, student_time_variables, mod_time_variables)
    return (model, mod_time_variables, student_time_variables, max_sections_per_mod, max_sections_per_time)

def printProblemInfo(mod_net_ids, student_net_ids, mod_time_preferences,
                     student_time_variables, mod_time_variables):
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

def setupConstraintProgrammingVariables(model, net_ids, time_preferences, is_mod_data):
    """
        Creates the constraint programming variables for the model of the moderator/student assignment problem

        Args:
            model: The CpModel object that represents the constraints of the problem
            net_ids: List of Strings for each person's net ID
            time_preferences: List where each entry is all the time preferences for one person

        Returns:
            2D List of PersonTimeVariableWrapper
    """
    random.seed('Creatively Titled Impossible Time Selection Seed') # Ensure deterministic behavior
    num_people = len(net_ids)
    num_section_times = len(time_preferences[0])
    person_time_variables = []

    for person_index in range(num_people):
        person_time_variables.append([])

        for time_index in range(num_section_times):
            preference_for_time = time_preferences[person_index][time_index]
            is_impossible_time = (preference_for_time == DOODLE_IMPOSSIBLE_TIME)
            is_randomly_selected = (random.random() < config.impossible_time_percentage)
            is_impossible_but_selected = (is_impossible_time and config.allow_impossible_times and is_randomly_selected)

            if not is_impossible_time or is_impossible_but_selected:
                # The time is either not impossible, or impossible times are allowed and it was randomly selected
                is_preferred_time = (preference_for_time == DOODLE_PREFERRED_TIME)
                cp_var_prefix = 'mod' if is_mod_data else 'student'
                cp_var_name = (cp_var_prefix + str(person_index) + ':time_' + str(time_index))

                constraint_programming_var = model.NewIntVar(0, 1, cp_var_name)
                variable_wrapper = PersonTimeVariableWrapper(net_ids[person_index], time_index, is_preferred_time,
                                                             is_impossible_time, constraint_programming_var)
                person_time_variables[person_index].append(variable_wrapper)
            else:
                person_time_variables[person_index].append(None)

    return person_time_variables

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
    not_preferred_mod_net_ids = []
    impossible_mod_net_ids = []
    not_preferred_student_net_ids = []
    impossible_student_net_ids = []

    for time_index in range(num_section_times):
        mods_assigned_to_times.append([])
        for mod_index in range(num_mods):
            mod_time_var_wrapper = mod_time_variables[mod_index][time_index]
            if mod_time_var_wrapper is not None and mod_time_var_wrapper.isTimeAssignedToPerson(solver):
                mod_net_id = mod_time_var_wrapper.net_id
                mods_assigned_to_times[time_index].append(mod_net_id)

                # Record if this moderator did not receive a preferred time
                if mod_time_var_wrapper.is_impossible_time:
                    impossible_mod_net_ids.append(mod_net_id)
                elif not mod_time_var_wrapper.is_preferred_time:
                    not_preferred_mod_net_ids.append(mod_net_id)

        students_assigned_to_times.append([])
        for student_index in range(num_students):
            student_time_var_wrapper = student_time_variables[student_index][time_index]
            if student_time_var_wrapper is not None and student_time_var_wrapper.isTimeAssignedToPerson(solver):
                student_net_id = student_time_var_wrapper.net_id
                students_assigned_to_times[time_index].append(student_net_id)

                # Record if this student did not receive a preferred time
                if student_time_var_wrapper.is_impossible_time:
                    impossible_student_net_ids.append(student_net_id)
                elif not student_time_var_wrapper.is_preferred_time:
                    not_preferred_student_net_ids.append(student_net_id)

    if len(impossible_mod_net_ids) > 0 or len(impossible_student_net_ids) > 0:
        print('Mods assigned to impossible times:', len(impossible_mod_net_ids),
              '(' + str(impossible_mod_net_ids) + ')')
        print('Students assigned to impossible times:', len(impossible_student_net_ids),
              '(' + str(impossible_student_net_ids) + ')')

    # If there aren't too many to report, print out the students who received not preferred times
    mod_message = 'Mods assigned to not preferred time: ' + str(len(not_preferred_mod_net_ids)) + ' '
    student_message = 'Students assigned to not preferred time: ' + str(len(not_preferred_student_net_ids)) + ' '
    if len(not_preferred_mod_net_ids) <= 10:
        mod_message += str(not_preferred_mod_net_ids)
    if len(not_preferred_student_net_ids) <= 10:
        student_message += str(not_preferred_student_net_ids)

    print(mod_message)
    print(student_message)
    return mods_assigned_to_times, students_assigned_to_times

def currentMillis():
    return int(round(time.time() * 1000))

class SolutionCounter(cp_model.CpSolverSolutionCallback):
    """ Simple callback class to count the number of solutions considered and report progress """

    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.solution_count = 0
        self.millis_at_last_solution = currentMillis()

    def on_solution_callback(self):
        self.solution_count += 1
        millis_since_last_solution = (currentMillis() - self.millis_at_last_solution)
        seconds_since_last_solution = (millis_since_last_solution / 1000.0)
        obj_value = str(self.ObjectiveValue())
        print(f'Viable assignment found (objective={obj_value}), time since last: {str(seconds_since_last_solution)} seconds')
        self.millis_at_last_solution = currentMillis()
