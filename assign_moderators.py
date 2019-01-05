import csv
from ortools.linear_solver import pywraplp

DOODLE_RESPONSE_START_LINE = 6
DOODLE_PREFERRED_TIME = 'OK'
DOODLE_NOT_PREFERRED_TIME = '(OK)'
DOODLE_IMPOSSIBLE_TIME = ''

class ModPreference:
    def __init__(self, net_id, time_preferences, max_num_sections):
        """
            Args:
                net_id: String for the netID of the moderator with these preferences
                time_preferences: String array with an entry for each time slot in the Doodle poll
                                    'OK' represents a preferred time
                                    '(OK)' represents a time that is not preferred but would work
                                    '' represents a time that will not work for the moderator
                max_num_sections: Integer for the maximum number of sections this moderator will take
        """
        self.net_id = net_id
        self.time_preferences = time_preferences
        self.max_num_sections = max_num_sections

def getModVarNameFromIndices(mod_index, time_index):
    return 'mod_' + str(mod_index) + ':time_' + str(time_index)

def getIndicesFromModVar(solverVar):
    variable_name = solverVar.name()
    colon_string_index = variable_name.find(':')

    mod_index = int(variable_name[len('mod_'):colon_string_index])
    time_index = int(variable_name[(colon_string_index + len(':time_')):])
    return mod_index, time_index

def main():
    mod_doodle_poll_csv_path = 'moderator_preferences_original.csv'
    mod_preferences = readModeratorPreferences(mod_doodle_poll_csv_path)

    mod_solver = pywraplp.Solver('ModeratorAssigner',
                                 pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # Set up the variables for the problem
    # A moderator paired with one section time is considered a variable, this is done for every mod and non-impossible time
    # Each variable may only have either 0 or 1 as its value, a 1 value indicates that mod has that section time
    # Impossible times are represented as None for ease of use so the indices remain the same
    num_moderators = len(mod_preferences)
    num_section_times = len(mod_preferences[0].time_preferences)
    mod_variables = [[mod_solver.IntVar(0, 1, getModVarNameFromIndices(mod_index, time_index)) 
                      if mod_preferences[mod_index].time_preferences[time_index] != DOODLE_IMPOSSIBLE_TIME
                      else None
                      for time_index in range(num_section_times)] 
                     for mod_index in range(num_moderators)]

    addSectionsPerModConstraint(mod_solver, mod_variables, mod_preferences, num_section_times, num_moderators)
    addModsPerSectionTimeConstraint(mod_solver, mod_variables, num_section_times, num_moderators)
    addNotPreferredTimeFunction(mod_solver, mod_variables, mod_preferences, num_section_times, num_moderators)

    # Kick off the solver, and verify an optimal solution exists
    result_status = mod_solver.Solve()
    assert result_status == pywraplp.Solver.OPTIMAL

    num_mods_per_section_time = [0] * num_section_times

    print('Minimum number of not preferred times selected = %d' % mod_solver.Objective().Value())
    for mod_index in range(num_moderators):
        for time_index in range(num_section_times):
            mod_section_time_variable = mod_variables[mod_index][time_index]
            if mod_section_time_variable is not None and mod_section_time_variable.solution_value() != 0:    
                (mod_index, time_index) = getIndicesFromModVar(mod_section_time_variable)
                print(mod_preferences[mod_index].net_id + ' has time ' + str(time_index))
                num_mods_per_section_time[time_index] += 1

    print(num_mods_per_section_time)

def readModeratorPreferences(mod_doodle_poll_csv_path):
    mod_preferences = []

    with open(mod_doodle_poll_csv_path, 'r+', encoding='utf-8-sig') as mod_pref_file:
        # Read in preferences file and trim to the start of the actual preference lines
        mod_preference_data = list(csv.reader(mod_pref_file))
        mod_preference_data = mod_preference_data[DOODLE_RESPONSE_START_LINE:]

        for mod_preference_entry in mod_preference_data:
            net_id = mod_preference_entry[0]
            time_preferences = mod_preference_entry[1:-1]
            max_num_sections = mod_preference_entry[-1] # Assumes this is present in the same CSV file
            mod_preferences.append(ModPreference(net_id, time_preferences, max_num_sections))

    return mod_preferences

def addModsPerSectionTimeConstraint(mod_solver, mod_variables, num_section_times, num_moderators):
    # Changing the min/max mods per section time for either a specific time index or all section times can be done here
    MIN_MODS_PER_SECTION_TIME = [1] * num_section_times
    MAX_MODS_PER_SECTION_TIME = [3] * num_section_times

    # Add the max and min constraint for moderators per section time
    # The sum of all moderator time variable values must be between 1 and 3 inclusive for each section
    for time_index in range(num_section_times):
        min_max_mods_for_section_time = mod_solver.Constraint(float(MIN_MODS_PER_SECTION_TIME[time_index]),
                                                              float(MAX_MODS_PER_SECTION_TIME[time_index]))
        for mod_index in range(num_moderators):
            mod_section_time_variable = mod_variables[mod_index][time_index]
            if mod_section_time_variable is not None:
                min_max_mods_for_section_time.SetCoefficient(mod_section_time_variable, 1)

def addSectionsPerModConstraint(mod_solver, mod_variables, mod_preferences, num_section_times, num_moderators):
    # Add constraint for each moderator to have no more than their max sections
    # This is currently set up so that each moderator has exactly their max sections, but can easily be changed
    for mod_index in range(num_moderators):
        section_times_per_mod = mod_solver.Constraint(float(mod_preferences[mod_index].max_num_sections),
                                                      float(mod_preferences[mod_index].max_num_sections))
        for time_index in range(num_section_times):
            mod_section_time_variable = mod_variables[mod_index][time_index]
            if mod_section_time_variable is not None:
                section_times_per_mod.SetCoefficient(mod_section_time_variable, 1)

def addNotPreferredTimeFunction(mod_solver, mod_variables, mod_preferences, num_section_times, num_moderators):
    # Set up the function to minimize the number of not preferred section times chosen for all moderators
    mod_objective_function = mod_solver.Objective()
    mod_objective_function.SetMinimization()

    for mod_index in range(num_moderators):
        for time_index in range(num_section_times):
            if mod_preferences[mod_index].time_preferences[time_index] == DOODLE_NOT_PREFERRED_TIME:
                mod_objective_function.SetCoefficient(mod_variables[mod_index][time_index], 1)

if __name__ == "__main__":
    main()
