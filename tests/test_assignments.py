import unittest
import config
from assign_time_slots import assignModeratorsAndStudents
from preference_input import readDoodlePreferences, readModMaxSectionPreferences

class TestAssignments(unittest.TestCase):
    """ Tests that assignment works correctly """

    def setUp(self):
        # Ensure that config options are correct for testing
        config.assign_exact_max_sections = False
        config.semester_has_fourth_room = False

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

    def test_four_sections_one_aamir(self):
        """ Tests a moderator can be assigned to many sections """
        test_data_dir = 'test_data/four_sections_one_aamir/'
        expected_mod_assignments = [['aamirh2'],
                                    ['aamirh2'],
                                    ['albertl3'],
                                    ['aamirh2'],
                                    ['aamirh2'],
                                    ['albertl3']]
        expected_student_assignments = [['a1', 'a2', 'a3', 'a4', 'a5', 'a6'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5'],
                                        ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'],
                                        ['d1', 'd2', 'd3', 'd4', 'd5', 'd6'],
                                        ['e1', 'e2', 'e3', 'e4', 'e5'],
                                        ['f1', 'f2', 'f3', 'f4', 'f5', 'f6']]

        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)

    def test_three_mods_one_section_time(self):
        """ Tests that multiple moderators can be assigned to a section time """
        test_data_dir = 'test_data/three_mods_one_section_time/'
        expected_mod_assignments = [['ssolank2', 'ztan19', 'amackow2'],
                                    ['bzinn2'],
                                    ['pjg4']]
        expected_student_assignments = [['a1', 'a2', 'a3', 'a4', 'a5',
                                            'c1', 'c2', 'c3', 'c4', 'c5', 'c6',
                                            'e1', 'e2', 'e3', 'e4', 'e5'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'],
                                        ['d1', 'd2', 'd3', 'd4', 'd5']]

        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)

    def test_chooses_preferred_times(self):
        """ Tests that no not preferred times are chosen when a solution exists without them """
        test_data_dir = 'test_data/chooses_preferred_times/'
        expected_mod_assignments = [['amackow2'],
                                    ['albertl3'],
                                    ['ysharma5'],
                                    ['albertl3']]
        expected_student_assignments = [['c1', 'c2', 'c3', 'c4', 'c5'],
                                        ['a1', 'a2', 'a3', 'a4', 'a5'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'],
                                        ['d1', 'd2', 'd3', 'd4', 'd5', 'd6']]

        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)

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


