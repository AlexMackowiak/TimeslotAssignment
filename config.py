import objective_functions # Need to specify objective function in config
objective_function = objective_functions.everyone_equal_weight

# The locations of the mod and student preference CSV files
semester_data_directory = 'test_data/real_data/fa19_data/'

# Moderator Doodle poll responses CSV
mod_doodle_poll_csv_path = semester_data_directory + 'mod_preferences.csv'

# Max sections each mod is willing to take in [mod Net ID],[max sections] format
mod_max_sections_csv_path = semester_data_directory + 'mod_max_sections.csv' 

# Student Doodle poll responses CSV
student_doodle_poll_csv_path = semester_data_directory + 'student_preferences.csv' 


# The file path to a CSV with [mod net ID],[mod name] format
mod_net_id_to_name_csv_path = 'test_data/real_data/fa19_data/mod_net_ids_to_names.csv'

# The file path to a CSV with format [section time],[(room 1 name:max sections)],...,[(room N name:max sections)]
# For example: "Wednesday 10 AM - 12 PM,(Siebel 1112:2),(Siebel 1314:1),(Siebel 4102:1)"
# These times MUST be the exact same and in the exact same order as the mod and student Doodle polls
section_times_csv_path = 'test_data/real_data/fa19_data/section_times.csv'

# The file path for where to write the final section assignment output CSV
output_csv_path = 'fa19_final_assignments.csv'

# These two values should be pretty self explanatory
# They are the minimum and maximum number of students that can be assigned to a section
min_students_per_section = 5
max_students_per_section = 6


# When this is True, all moderators will be assigned to exactly their maximum amount of sections
# This option is great for creating a good amount of sections with 5 students and reducing computation time
# The downside however is that the program will fail to find a solution if not every mod can have their
#  exact maximum amount of sections. This means you will have to manually fine tune the preferences file
assign_exact_max_sections = False

# When True, this option is the automatic version of assign_exact_max_sections above. It will attempt to maximize the
#  number of sections created, and therefore tend to leave spots open in existing sections. The only downside to using
#  this is that it may add quite a bit of extra computation to the objective function over the manual version.
#  If this extra compution appears to require exponential time, it is best to use the manual version instead.
# assign_exact_max_sections and maximize_number_of_sections cannot both be True at the same time, if they are both set
#  to True, a warning will be logged and assign_exact_max_sections will take precedence
maximize_number_of_sections = False

# When True, will do some simple error checking to see if every mod's net ID roughly corresponds to their name
mod_net_id_error_check = True


# When True, assigning mods to sections that happen right after each other will result in a more optimal solution
#  than assigning them to sections that happen at completely unrelated times
# The preferred_times_only value specifies that only two adjacent, green (preferred) times will be considered
#  contiguous, it requires a decent amount more computation time when tested on real datasets
# The all_possible value, when True, overrides the preferred_times_only value. This specifies that all possible
#  sections that are adjacent will be prioritized. This requires potentially exponential computation time
# The main difference is that:
#  preferred_times_only with [yellow][yellow][green][green][yellow][green][green][red] adds 2 variables to the system
#  all_possible with [yellow][yellow][green][green][yellow][green][green][red] adds 6 variables to the system
prefer_contiguous_sections_preferred_times_only = False
prefer_contiguous_sections_all_possible = False
# Finally, since adding a large number of variables to the system can lead to exponential time behaviours, setting
#  contiguous_sections_percentage to a value lower than 1.0 will cause a fraction of the existing contiguous sections
#  to not be considered. This will therefore not contribute those variables to the system. For example, a value of
#  0.25 will cause only 1/4 contiguous sections to be considered. Setting this value lower than 1.0 may be necessary
#  to avoid exponential runtimes
contiguous_sections_percentage = 1.0

# While predicting exactly what will or will not lead to exponential runtimes is difficult, runtime is clearly very
#  highly correlated with the number of variables in the system. The num_sections_to_greedy_preselect config option
#  adds a way to cut down on the number of variables in the system at the cost of a probably less optimal solution.
# Setting num_sections_to_greedy_preselect to N will make the first step in section assignment to be attempting to
#  assign at most N sections via a greedy algorithm.
# The algorithm used is to select the time index with the least green times, then within that time index select
#  the 5 students and 1 mod who put green for the time and also gave the least number of valid green/yellow times.
# Greedy sections will never be assigned using yellow times, and students may still be added to greedy sections by
#  a later step of the constraint programming optimizer.
num_sections_to_greedy_preselect = 0

# When True, allows a partial assignment to be generated by considering times marked as impossible
# Impossible times will only be selected when a full assignment is impossible without them
# Setting this to True may exponentially increase the amount of time taken to find an optimal solution
# To alleviate this, only a percentage of the impossible times are allowed to be considered
# This percentage may be configured by setting impossible_time_percentage to a different value
allow_impossible_times = False
impossible_time_percentage = 0.05


# When False, allows the constraint programming solver to be terminated early by sending SIGINT
# Terminating the solver early will cause the rest of the program to use the most optimal assignment that
#  has been found so far. This is very unlikely to be the actual optimal assignment so this option should
#  only be used as a last resort when finding the actual optimal assignment will take inordinately long
#  and all other measures listed in usage_instructions.txt have been attempted
# Be very careful about using this with allow_impossible_times set to True as early section assignments
#  will very likely contain times that are impossible for students or moderators
only_allow_optimal_solutions=True
