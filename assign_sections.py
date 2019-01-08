from moderator_assignments import assignModerators
from student_assignments import assignStudents

if __name__ == "__main__":
    mod_doodle_poll_csv_path = 'moderator_preferences_original.csv'
    mod_max_sections_csv_path = 'moderator_max_sections_preferences.csv'
    student_doodle_poll_csv_path = 'student_preferences_original_no_duplicates.csv'

    num_mods_per_section_time = assignModerators(mod_doodle_poll_csv_path,
                                                 mod_max_sections_csv_path)
    print(num_mods_per_section_time)
    num_students_per_section_time = assignStudents(student_doodle_poll_csv_path,
                                                   num_mods_per_section_time)
    print(num_students_per_section_time)
