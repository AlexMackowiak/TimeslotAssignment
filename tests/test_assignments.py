import unittest
from experimental_assignments_2 import assignModeratorsAndStudents
from preference_input import readDoodlePreferences, readModMaxSectionPreferences

class TestAssignments(unittest.TestCase):
    """ Tests that assignment works correctly """

    def test_basic_functionality(self):
        """ Tests that the only possible assignments are made for a trivial case """
        test_data_dir = 'test_data/basic_functionality/'
        expected_mod_assignments = [['amackow2'],
                                    ['albertl3'],
                                    ['ysharma5']]
        expected_student_assignments = [['a1', 'a2', 'a3', 'a4', 'a5', 'a6'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'],
                                        ['c1', 'c2', 'c3', 'c4', 'c5', 'c6']]

        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)

    def test_two_sections_one_mod(self):
        """ Tests that a moderator can be assigned multiple sections with the right preferences """
        test_data_dir = 'test_data/two_sections_one_mod/'
        expected_mod_assignments = [['amackow2'],
                                    ['albertl3'],
                                    ['ysharma5'],
                                    ['amackow2']]
        expected_student_assignments = [['a1', 'a2', 'a3', 'a4', 'a5', 'a6'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'],
                                        ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'],
                                        ['d1', 'd2', 'd3', 'd4', 'd5']]

        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)


#    def test_chooses_preferred_times(self):

    def verify_assignments(self, test_data_dir, expected_mod_assignments, expected_student_assignments):
        mod_doodle_poll_csv_path = (test_data_dir + 'mod_preferences.csv')
        mod_max_sections_csv_path = (test_data_dir + 'mod_max_sections.csv')
        student_doodle_poll_csv_path = (test_data_dir + 'student_preferences.csv')
        (mods_assigned_to_times, 
         students_assigned_to_times) = assignModeratorsAndStudents(mod_doodle_poll_csv_path,
                                                                   mod_max_sections_csv_path,
                                                                   student_doodle_poll_csv_path)

        # No guarantee on the order returned within the time index of the assignment
        for time_index in range(len(mods_assigned_to_times)):
            actual_mods_in_time = mods_assigned_to_times[time_index]
            actual_students_in_time = students_assigned_to_times[time_index]
            expected_mods_in_time = expected_mod_assignments[time_index]
            expected_students_in_time = expected_student_assignments[time_index]

            self.assertEqual(len(actual_mods_in_time), len(expected_mods_in_time))
            for mod_assigned_to_time in actual_mods_in_time:
                self.assertIn(mod_assigned_to_time, expected_mods_in_time)

            self.assertEqual(len(actual_students_in_time), len(expected_students_in_time))
            for student_assigned_to_time in actual_students_in_time:
                self.assertIn(student_assigned_to_time, expected_students_in_time)


