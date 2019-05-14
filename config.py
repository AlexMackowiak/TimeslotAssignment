
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

# The file path for where to write the final section assignment output CSV
output_csv_path = 'sp19_final_assignments.csv'

# The file path to a CSV with [section time] on each line specifying all available section time slots
# These times MUST be the exact same and in the exact same order as the mod and student Doodle polls
section_times_csv_path = 'sp19_full_data/section_times.csv'
