import unittest
import config
from assign_time_slots import assignModeratorsAndStudents
from csv_input import readDoodlePreferences, readModMaxSectionPreferences
TEST_DATA_PREFIX = 'test_data/assignment_test_data/'

class TestAssignments(unittest.TestCase):
    """ Tests that assignment works correctly """

    def setUp(self):
        # Ensure that config options are correct for testing
        config.assign_exact_max_sections = False
        config.maximize_number_of_sections  = False
        config.only_allow_optimal_solutions = True
        config.prefer_contiguous_sections_preferred_times_only = False
        config.prefer_contiguous_sections_all_possible = False
        config.allow_impossible_times = False
        config.min_students_per_section = 5
        config.max_students_per_section = 6

    def test_basic_functionality(self):
        """ Tests that the only possible assignments are made for a trivial case """
        test_data_dir = TEST_DATA_PREFIX + 'basic_functionality/'
        expected_mod_assignments = [['amackow2'],
                                    ['albertl3'],
                                    ['ysharma5']]
        expected_student_assignments = [['a1', 'a2', 'a3', 'a4', 'a5', 'a6'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'],
                                        ['c1', 'c2', 'c3', 'c4', 'c5', 'c6']]

        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)

    def test_two_sections_one_mod(self):
        """ Tests that a moderator can be assigned multiple sections with the right preferences """
        test_data_dir = TEST_DATA_PREFIX + 'two_sections_one_mod/'
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
        test_data_dir = TEST_DATA_PREFIX + 'four_sections_one_aamir/'
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
        test_data_dir = TEST_DATA_PREFIX + 'three_mods_one_section_time/'
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
        test_data_dir = TEST_DATA_PREFIX + 'chooses_preferred_times/'
        expected_mod_assignments = [['amackow2'],
                                    ['albertl3'],
                                    ['ysharma5'],
                                    ['albertl3']]
        expected_student_assignments = [['c1', 'c2', 'c3', 'c4', 'c5'],
                                        ['a1', 'a2', 'a3', 'a4', 'a5'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'],
                                        ['d1', 'd2', 'd3', 'd4', 'd5', 'd6']]

        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)

    def test_different_num_rooms(self):
        """ Tests that assignments can be maded with different numbers of rooms at each time """
        test_data_dir = TEST_DATA_PREFIX + 'different_num_rooms/'
        expected_mod_assignments = [['amackow2', 'ssolank2', 'arnavs3', 'ysharma5', 'albertl3'],
                                    ['amackow2', 'ssolank2'],
                                    ['amackow2']]
        expected_student_assignments = [['a1', 'a2', 'a3', 'a4', 'a5',
                                         'b1', 'b2', 'b3', 'b4', 'b5', 'b6',
                                         'c1', 'c2', 'c3', 'c4', 'c5',
                                         'd1', 'd2', 'd3', 'd4', 'd5', 'd6',
                                         'e1', 'e2', 'e3', 'e4', 'e5'],
                                        ['f1', 'f2', 'f3', 'f4', 'f5', 'f6',
                                         'g1', 'g2', 'g3', 'g4', 'g5', 'g6'],
                                        ['h1', 'h2', 'h3', 'h4', 'h5']]

        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments,
                                non_standard_rooms=True)

    def test_maximize_num_sections(self):
        """ Tests that the total number of sections is maximized when the option is enabled """
        test_data_dir = TEST_DATA_PREFIX + 'maximize_num_sections/'
        config.maximize_number_of_sections = False

        expected_mod_assignments = [['davidb2'],
                                    ['snadeem2'],
                                    ['pjg4'],
                                    ['elainew2'],
                                    ['bzinn2'],
                                    []]
        expected_student_assignments = [['a1', 'a2', 'a3', 'a4', 'a5', 'a6'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'],
                                        ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'],
                                        ['d1', 'd2', 'd3', 'd4', 'd5', 'd6'],
                                        ['e1', 'e2', 'e3', 'e4', 'e5', 'e6'],
                                        []]
        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)

        # Verify that not preferred times will be picked to maxmize the number of sections
        config.maximize_number_of_sections = True
        expected_mod_assignments[5] = ['bzinn2']
        expected_student_assignments = [['a1', 'a2', 'a3', 'a4', 'a5'],
                                        ['b1', 'b2', 'b3', 'b4', 'b5'],
                                        ['c1', 'c2', 'c3', 'c4', 'c5'],
                                        ['d1', 'd2', 'd3', 'd4', 'd5'],
                                        ['e1', 'e2', 'e3', 'e4', 'e5'],
                                        ['a6', 'b6', 'c6', 'd6', 'e6']]
        self.verify_assignments(test_data_dir, expected_mod_assignments, expected_student_assignments)

    def verify_assignments(self, test_data_dir, expected_mod_assignments, expected_student_assignments,
                           non_standard_rooms=False):
        # Set up paths to CSV files for this test
        mod_doodle_poll_csv_path = (test_data_dir + 'mod_preferences.csv')
        mod_max_sections_csv_path = (test_data_dir + 'mod_max_sections.csv')
        student_doodle_poll_csv_path = (test_data_dir + 'student_preferences.csv')
        section_times_csv_path = (test_data_dir + 'section_times.csv') if non_standard_rooms else None

        # Call the section assigner
        csv_files = (mod_doodle_poll_csv_path, mod_max_sections_csv_path,
                     student_doodle_poll_csv_path, section_times_csv_path)
        (mods_assigned_to_times, students_assigned_to_times) = assignModeratorsAndStudents(*csv_files)
        self.assertEqual(len(mods_assigned_to_times), len(expected_mod_assignments))
        self.assertEqual(len(students_assigned_to_times), len(expected_student_assignments))

        # No guarantee on the order returned within the time index of the assignment
        for time_index in range(len(mods_assigned_to_times)):
            actual_mods_in_time = mods_assigned_to_times[time_index]
            actual_students_in_time = students_assigned_to_times[time_index]
            expected_mods_in_time = expected_mod_assignments[time_index]
            expected_students_in_time = expected_student_assignments[time_index]

            # Verify the mods in each time are expected
            self.assertEqual(len(actual_mods_in_time), len(expected_mods_in_time))
            for mod_assigned_to_time in actual_mods_in_time:
                self.assertIn(mod_assigned_to_time, expected_mods_in_time)

            # Verify the students in each time are expected
            self.assertEqual(len(actual_students_in_time), len(expected_students_in_time))
            for student_assigned_to_time in actual_students_in_time:
                self.assertIn(student_assigned_to_time, expected_students_in_time)


