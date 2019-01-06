import csv
from ortools.linear_solver import pywraplp

DOODLE_RESPONSE_START_LINE = 6
DOODLE_PREFERRED_TIME = 'OK'
DOODLE_NOT_PREFERRED_TIME = '(OK)'
DOODLE_IMPOSSIBLE_TIME = ''

class ModAssignedToTimeVariableWrapper:
    def __init__(self, net_id, time_index, is_preferred_time, linear_programming_var):
        """
            Args:
                net_id: String for the netID of the moderator this LP variable represents
                time_index: Integer for the time slot this LP variable represents
                is_preferred_time: True if this moderator marked this time as preferred
                linear_programming_var: The OR-Tools IntVar object being wrapped with extra data
        """
        self.net_id = net_id
        self.time_index = time_index
        self.is_preferred_time = is_preferred_time
        self.variable = linear_programming_var

    def isTimeAssignedToMod(self):
        """
            The output of this function should only be used after the linear programming solver
                has been run

            Returns:
                True if this moderator was assigned this time by the LP solver, false otherwise
        """
        return (self.variable.solution_value() != 0)

def main():
    mod_doodle_poll_csv_path = 'moderator_preferences_original.csv'
    (mod_net_ids, mod_time_preferences, max_sections_per_mod) = readModeratorPreferences(mod_doodle_poll_csv_path)

    mod_solver = pywraplp.Solver('ModeratorAssigner', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # Set up the variables for the problem
    # A moderator paired with one section time is considered a variable, this is done for every mod and non-impossible time
    # Each variable may only have either 0 or 1 as its value, a 1 value indicates that mod has that section time
    # Impossible times are represented as None for ease of use so the indices remain the same
    num_moderators = len(mod_net_ids)
    num_section_times = len(mod_time_preferences[0])

    variables_for_each_mod = [[] for _ in range(num_moderators)]
    variables_for_each_time = [[] for _ in range(num_section_times)]
    # The two lists above represent the same LP variables, but a different way of iterating over them (row vs. column order)

    for mod_index in range(num_moderators):
        for time_index in range(num_section_times):
            mod_preference_for_time = mod_time_preferences[mod_index][time_index]

            if mod_preference_for_time != DOODLE_IMPOSSIBLE_TIME:
                is_preferred_time = (mod_preference_for_time == DOODLE_PREFERRED_TIME)
                linear_programming_var = mod_solver.IntVar(0, 1, ('mod_' + str(mod_index) + ':time_' + str(time_index)))
                variable_wrapper = ModAssignedToTimeVariableWrapper(mod_net_ids[mod_index], time_index, 
                                                                    is_preferred_time, linear_programming_var)

                variables_for_each_mod[mod_index].append(variable_wrapper)
                variables_for_each_time[time_index].append(variable_wrapper)

    addSectionsPerModConstraint(mod_solver, variables_for_each_mod, max_sections_per_mod)
    addModsPerSectionTimeConstraint(mod_solver, variables_for_each_time)
    addNotPreferredTimeFunction(mod_solver, variables_for_each_mod)

    # Kick off the solver, and verify an optimal solution exists
    result_status = mod_solver.Solve()
    assert result_status == pywraplp.Solver.OPTIMAL

    num_mods_per_section_time = [0] * num_section_times

    print('Minimum number of not preferred times selected = %d' % mod_solver.Objective().Value())
    for times_that_work_for_mod in variables_for_each_mod:
        for mod_section_time_var_wrapper in times_that_work_for_mod:
            if mod_section_time_var_wrapper.isTimeAssignedToMod():
               time_index_assigned = mod_section_time_var_wrapper.time_index
               print(mod_section_time_var_wrapper.net_id + ' has time ' + str(time_index_assigned))
               num_mods_per_section_time[time_index_assigned] += 1

    print(num_mods_per_section_time)

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
            #mod_preferences.append(ModPreferences(net_id, time_preferences, max_num_sections))

    return mod_net_ids, mod_time_preferences, max_sections_per_mod

def addSectionsPerModConstraint(mod_solver, variables_for_each_mod, max_sections_per_mod):
    """
        Adds the constraint to the LP solver that no moderator has more than their max requested number of sections
        This is currently set up so each moderator has exactly their maximum sections so that the numbers can be
            messed with easier when configuring (TODO: make this a config option)
        Mathematically, this constraint is expressed as
            (the sum of all mod/time assignment variables for a mod) <= (max sections for that mod)

        Args:
            mod_solver: The pywraplp.Solver object which will solve the linear programming assignment problem
            variables_for_each_mod: List where each entry is a List of type ModAssignedToTimeVariableWrapper
                                        which represents all mod/time variables for a single moderator
            max_sections_per_mod: List of Integers, max_sections_per_mod[i] is the maximum sections the ith
                                    moderator will take
    """
    for (times_that_work_for_mod, max_sections_for_this_mod) in zip(variables_for_each_mod, max_sections_per_mod):
        section_times_per_mod = mod_solver.Constraint(float(max_sections_for_this_mod),
                                                      float(max_sections_for_this_mod))
        for mod_section_time_var_wrapper in times_that_work_for_mod:
            section_times_per_mod.SetCoefficient(mod_section_time_var_wrapper.variable, 1)

def addModsPerSectionTimeConstraint(mod_solver, variables_for_each_time):
    """
        Adds the constraint to the LP solver that every section time has at least one moderator, and no section time
            has more moderators than there are rooms (currently: 1 <= mods in section time <= 3)
        Mathematically this constraint is expressed as
           1 <= (the sum of all mod/time assignment variables for a section time) <= 3

        Args:
            mod_solver: The pywraplp.Solver object which will solve the linear programming assignment problem
            variables_for_each_time: List where each entry is a List of type ModAssignedToTimeVariableWrapper
                                        which represents all mod/time variables for a single section time
    """
    # Changing the min/max mods per section time for either a specific time index or all section times can be done here
    min_mods_per_section_time = [1] * len(variables_for_each_time)
    max_mods_per_section_time = [3] * len(variables_for_each_time)

    for (moderators_that_can_take_time, min_mods_for_time, max_mods_for_time) in \
            zip(variables_for_each_time, min_mods_per_section_time, max_mods_per_section_time):
        min_max_mods_for_section_time = mod_solver.Constraint(float(min_mods_for_time), float(max_mods_for_time))

        for mod_section_time_var_wrapper in moderators_that_can_take_time:
            min_max_mods_for_section_time.SetCoefficient(mod_section_time_var_wrapper.variable, 1)

def addNotPreferredTimeFunction(mod_solver, variables_for_each_mod):
    """
        Adds the function to minimize to the LP solver, mathematically this function is specified as
            minimize f where f = (the sum of all mod/time assignment variables where the time is not preferred)
        This means the LP solver can pick preferred times for free, but choosing not preferred times incurs a cost

        Args:
            mod_solver: The pywraplp.Solver object which will solve the linear programming assignment problem
            variables_for_each_mod: List where each entry is a List of type ModAssignedToTimeVariableWrapper
                                        which represents all mod/time variables for a single moderator
    """
    mod_objective_function = mod_solver.Objective()
    mod_objective_function.SetMinimization()

    for times_that_work_for_mod in variables_for_each_mod:
        for mod_section_time_var_wrapper in times_that_work_for_mod:
            is_preferred_time = (mod_section_time_var_wrapper.is_preferred_time)

            if not is_preferred_time:
                mod_objective_function.SetCoefficient(mod_section_time_var_wrapper.variable, 1)

if __name__ == "__main__":
    main()
