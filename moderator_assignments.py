from preference_input import readDoodlePreferences, readModMaxSectionPreferences
from lp_problem_setup import setupLinearProgrammingVariables, addSectionsPerPersonConstraint,\
                             addPeoplePerSectionTimeConstraint, addNotPreferredTimeFunction
from ortools.linear_solver import pywraplp

def assignModerators(mod_doodle_poll_csv_path, mod_max_section_csv_path):
    """
        Args:
            mod_doodle_poll_csv_path: The file path to the Doodle poll for the moderators in .csv format
            mod_max_section_csv_path: The file path to the max sections .csv file

        Returns:
            List of Integers, at each index is the number of moderators assigned to that section time for use in
                assigning students to section times that have enough moderators
    """
    (mod_net_ids, mod_time_preferences) = readDoodlePreferences(mod_doodle_poll_csv_path)
    max_sections_per_mod = readModMaxSectionPreferences(mod_max_section_csv_path, mod_net_ids)

    mod_solver = pywraplp.Solver('ModeratorAssigner', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    (variables_for_each_mod, variables_for_each_time) = setupLinearProgrammingVariables(mod_solver, mod_net_ids,
                                                                                        mod_time_preferences)
    min_mods_per_time = [1] * len(variables_for_each_time)
    max_mods_per_time = [3] * len(variables_for_each_time)

    addSectionsPerPersonConstraint(mod_solver, variables_for_each_mod, max_sections_per_mod)
    addPeoplePerSectionTimeConstraint(mod_solver, variables_for_each_time, min_mods_per_time, max_mods_per_time)
    addNotPreferredTimeFunction(mod_solver, variables_for_each_mod)

    # Kick off the solver, and verify an optimal solution exists
    result_status = mod_solver.Solve()
    assert result_status == pywraplp.Solver.OPTIMAL

    num_mods_per_section_time = [0] * len(mod_time_preferences[0])

    print('Minimum number of not preferred times selected = %d' % mod_solver.Objective().Value())
    for times_that_work_for_mod in variables_for_each_mod:
        for mod_section_time_var_wrapper in times_that_work_for_mod:
            if mod_section_time_var_wrapper.isTimeAssignedToPerson():
               time_index_assigned = mod_section_time_var_wrapper.time_index
               print(mod_section_time_var_wrapper.net_id + ' has time ' + str(time_index_assigned))
               num_mods_per_section_time[time_index_assigned] += 1

    return num_mods_per_section_time
