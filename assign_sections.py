from moderator_assignments import assignModerators
from student_assignments import assignStudents
from experimental_assignments_2 import assignModeratorsAndStudents

if __name__ == "__main__":
    test_data_directory = 'test_data/fa18_data/'
    mod_doodle_poll_csv_path = test_data_directory + 'mod_preferences.csv'
    mod_max_sections_csv_path = test_data_directory + 'mod_max_sections.csv'
    student_doodle_poll_csv_path = test_data_directory + 'student_preferences.csv'
    (mods_assigned_to_times, students_assigned_to_times) = assignModeratorsAndStudents(mod_doodle_poll_csv_path,
                                                                                       mod_max_sections_csv_path,
                                                                                       student_doodle_poll_csv_path)
    assert len(mods_assigned_to_times) == len(students_assigned_to_times)

    for time_index in range(len(mods_assigned_to_times)):
        mods_in_time = mods_assigned_to_times[time_index]
        students_in_time = students_assigned_to_times[time_index]

        print('Time ' + str(time_index) + ': ' + str(mods_in_time) + ' ' + str(students_in_time))
