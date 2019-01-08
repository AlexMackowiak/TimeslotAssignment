from preference_input import readDoodlePreferences
from lp_problem_setup import setupLinearProgrammingVariables, addSectionsPerPersonConstraint,\
                             addPeoplePerSectionTimeConstraint, addNotPreferredTimeFunction
from ortools.linear_solver import pywraplp

def assignStudents(stud_doodle_poll_csv_path, num_mods_per_section_time):
    """
        Args:
            stud_doodle_poll_csv_path: The file path to the Doodle poll for the students in .csv format
            num_mods_per_section_time: The number of moderators assigned during a section time
    """
    (stud_net_ids, stud_time_preferences) = readDoodlePreferences(stud_doodle_poll_csv_path)

    stud_solver = pywraplp.Solver('StudentAssigner', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    (variables_for_each_stud, variables_for_each_time) = setupLinearProgrammingVariables(stud_solver, stud_net_ids,
                                                                                            stud_time_preferences)
    sections_per_stud = [1] * len(stud_net_ids)
    min_studs_per_time = [5 * num_mods_in_time for num_mods_in_time in num_mods_per_section_time]
    max_studs_per_time = [6 * num_mods_in_time for num_mods_in_time in num_mods_per_section_time]

    print(min_studs_per_time)
    print(max_studs_per_time)

    addSectionsPerPersonConstraint(stud_solver, variables_for_each_stud, sections_per_stud)
    addPeoplePerSectionTimeConstraint(stud_solver, variables_for_each_time, min_studs_per_time, max_studs_per_time)
    addNotPreferredTimeFunction(stud_solver, variables_for_each_stud)

    # Kick off the solver, and verify an optimal solution exists
    result_status = stud_solver.Solve()
    assert result_status == pywraplp.Solver.OPTIMAL

    num_studs_per_section_time = [0] * len(stud_time_preferences[0])

    print('Minimum number of not preferred times selected = %d' % mod_solver.Objective().Value())
    for times_that_work_for_stud in variables_for_each_stud:
        for stud_section_time_var_wrapper in times_that_work_for_stud:
            if stud_section_time_var_wrapper.isTimeAssignedToPerson():
               time_index_assigned = stud_section_time_var_wrapper.time_index
               #print(stud_section_time_var_wrapper.net_id + ' has time ' + str(time_index_assigned))
               num_studs_per_section_time[time_index_assigned] += 1

    return num_studs_per_section_time
