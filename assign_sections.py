from moderator_assignments import assignModerators
from student_assignments import assignStudents
from experimental_assignments_2 import assignModeratorsAndStudents

if __name__ == "__main__":
#    mod_doodle_poll_csv_path = 'moderator_preferences_original.csv'
#    mod_max_sections_csv_path = 'moderator_max_sections_preferences.csv'
#    student_doodle_poll_csv_path = 'student_preferences_original_no_duplicates.csv'

    test_data_directory = 'test_data/fa18/'
    mod_doodle_poll_csv_path = test_data_directory + 'mod_preferences.csv'
    mod_max_sections_csv_path = test_data_directory + 'mod_max_sections.csv'
    student_doodle_poll_csv_path = test_data_directory + 'student_preferences.csv'
    assignModeratorsAndStudents(mod_doodle_poll_csv_path, mod_max_sections_csv_path,
                                student_doodle_poll_csv_path)
"""
    num_mods_per_section_time = assignModerators(mod_doodle_poll_csv_path,
                                                 mod_max_sections_csv_path)
    print(num_mods_per_section_time)

    working_times = [2, 1, 1, 1, 3, 3, 2, 2, 1, 2, 2]
    num_students_per_section_time = assignStudents(student_doodle_poll_csv_path,
                                                   working_times)
                                                   #num_mods_per_section_time)
    print(num_students_per_section_time)
"""
