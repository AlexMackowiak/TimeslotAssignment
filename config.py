import objective_functions # Need to specify objective function in config
objective_function = objective_functions.everyone_equal_weight

# The locations of the mod and student preference CSV files
semester_data_directory = 'test_data/sp19_data/'

# Moderator Doodle poll responses CSV
mod_doodle_poll_csv_path = semester_data_directory + 'mod_preferences.csv'

# Max sections each mod is willing to take in [mod Net ID],[max sections] format
mod_max_sections_csv_path = semester_data_directory + 'mod_max_sections.csv' 

# Student Doodle poll responses CSV
student_doodle_poll_csv_path = semester_data_directory + 'student_preferences.csv' 


# The file path to a CSV with [mod net ID],[mod name] format
mod_net_id_to_name_csv_path = 'sp19_full_data/sp19_mod_net_ids_to_names.csv'

# The file path to a CSV with format [section time],[(room 1 name:max sections)],...,[(room N name:max sections)]
# For example: "Wednesday 10 AM - 12 PM,(Siebel 1112:2),(Siebel 1314:1),(Siebel 4102:1)"
# These times MUST be the exact same and in the exact same order as the mod and student Doodle polls
section_times_csv_path = 'sp19_full_data/sp19_section_times.csv'

# The file path for where to write the final section assignment output CSV
output_csv_path = 'sp19_final_assignments.csv'


# When this is True, all moderators will be assigned to exactly their maximum amount of sections
# This option is great for creating a good amount of sections with 5 students and reducing computation time
# The downside however is that the program will fail to find a solution if not every mod can have their
#  exact maximum amount of sections, so it will require manual fine tuning of the preferences file
assign_exact_max_sections = True

# When True, will do some simple error checking to see if every mod's net ID roughly corresponds to their name
mod_net_id_error_check = True
