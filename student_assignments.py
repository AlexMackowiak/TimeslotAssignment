from preference_input import readDoodlePreferences
from lp_problem_setup import setupLinearProgrammingVariables, addSectionsPerPersonConstraint,\
                             addPeoplePerSectionTimeConstraint, addNotPreferredTimeFunction
from ortools.linear_solver import pywraplp

def assignStudents(student_doodle_poll_csv_path, num_mods_per_section_time):
    """
        Args:
            student_doodle_poll_csv_path: The file path to the Doodle poll for the studentents in .csv format
            num_mods_per_section_time: The number of moderators assigned during a section time
    """
    (student_net_ids, student_time_preferences) = readDoodlePreferences(student_doodle_poll_csv_path)

    student_solver = pywraplp.Solver('StudentAssigner', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    (variables_for_each_student, variables_for_each_time) = setupLinearProgrammingVariables(student_solver,
                                                                                            student_net_ids,
                                                                                            student_time_preferences)
    sections_per_student = [1] * len(student_net_ids)
    min_students_per_time = [4 * num_mods_in_time for num_mods_in_time in num_mods_per_section_time]
    max_students_per_time = [6 * num_mods_in_time for num_mods_in_time in num_mods_per_section_time]

    addSectionsPerPersonConstraint(student_solver, variables_for_each_student, sections_per_student)
    addPeoplePerSectionTimeConstraint(student_solver, variables_for_each_time,
                                      min_students_per_time, max_students_per_time)
    addNotPreferredTimeFunction(student_solver, variables_for_each_student)

    # Kick off the solver, and verify an optimal solution exists
    result_status = student_solver.Solve()
    assert result_status == pywraplp.Solver.OPTIMAL

    num_students_per_section_time = [0] * len(student_time_preferences[0])

    print('Minimum number of not preferred times selected = %d' % mod_solver.Objective().Value())
    for times_that_work_for_student in variables_for_each_student:
        for student_section_time_var_wrapper in times_that_work_for_student:
            if student_section_time_var_wrapper.isTimeAssignedToPerson():
               time_index_assigned = student_section_time_var_wrapper.time_index
               #print(student_section_time_var_wrapper.net_id + ' has time ' + str(time_index_assigned))
               num_students_per_section_time[time_index_assigned] += 1

    return num_students_per_section_time
