import csv
from lp_problem_setup import setupLinearProgrammingVariables, addSectionsPerPersonConstraint,\
                             addPeoplePerSectionTimeConstraint, addNotPreferredTimeFunction
from ortools.linear_solver import pywraplp

DOODLE_RESPONSE_START_LINE = 6

def assignModerators(mod_doodle_poll_csv_path):
    """
        Args:
            mod_doodle_poll_csv_path: The file path to the Doodle poll which also has max section information

        Returns:
            List of Integers, at each index is the number of moderators assigned to that section time for use in
                assigning students to section times that have enough moderators
    """
    (mod_net_ids, mod_time_preferences, max_sections_per_mod) = readModeratorPreferences(mod_doodle_poll_csv_path)
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

def readModeratorPreferences(mod_doodle_poll_csv_path):
    """
        Reads in the time and max sections preferences for each moderator from a csv file.
        This function assumes a Doodle poll format that has been modified to put the max sections each moderator
            will take at the end of their entry (TODO: put max sections preferences in a different file)

        Args:
            mod_doodle_poll_csv_path: The file path to the Doodle poll which also has max section information

        Returns:
            mod_net_ids: List of Strings for each moderator's net ID
            mod_time_preferences: List where each entry is all the time preferences for a moderator
                                    time preferences are a List of Strings where for each time slot in the Doodle poll
                                    'OK' represents a preferred time
                                    '(OK)' represents a time that is not preferred but would work
                                    '' represents a time that will not work for the moderator
            max_sections_per_mod: List of Integers for the maximum number of sections each moderator will take

            All of the lists returned store information for the same moderator at the same index
            Probably should make some data container object instead... TODO
    """
    mod_net_ids = []
    mod_time_preferences = []
    max_sections_per_mod = []

    with open(mod_doodle_poll_csv_path, 'r+', encoding='utf-8-sig') as mod_pref_file:
        # Read in preferences file and trim to the start of the actual preference lines
        mod_preference_data = list(csv.reader(mod_pref_file))
        mod_preference_data = mod_preference_data[DOODLE_RESPONSE_START_LINE:]

        for mod_preference_entry in mod_preference_data:
            net_id = mod_preference_entry[0]
            time_preferences = mod_preference_entry[1:-1]
            max_num_sections = mod_preference_entry[-1] # Assumes this is present in the same CSV file

            mod_net_ids.append(net_id)
            mod_time_preferences.append(time_preferences)
            max_sections_per_mod.append(max_num_sections)

    return mod_net_ids, mod_time_preferences, max_sections_per_mod
