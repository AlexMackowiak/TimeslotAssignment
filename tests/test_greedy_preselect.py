import unittest
import config
from assign_time_slots import getModelFromInputFiles
from csv_input import readDoodlePreferences, readModMaxSectionPreferences
from greedy_preselect import getGreedyAssignment
from ortools.sat.python import cp_model
TEST_DATA_PREFIX = 'test_data/greedy_preselect_test_data/'

class TestGreedyPreselect(unittest.TestCase):
    """ Tests that the greedy preselect algorithm works correctly """

    def setUp(self):
        # Ensure that config options are correct for testing
        config.assign_exact_max_sections = False
        config.maximize_number_of_sections = False
        config.only_allow_optimal_solutions = True
        config.prefer_contiguous_sections_preferred_times_only = False
        config.prefer_contiguous_sections_all_possible = False
        config.num_sections_to_greedy_preselect = 0
        config.allow_impossible_times = False
        config.min_students_per_section = 5
        config.max_students_per_section = 6

    def test_basic_functionality(self):
        """ Tests that the only possible assignments are made for a trivial case """
        config.num_sections_to_greedy_preselect = 2
        test_data_dir = TEST_DATA_PREFIX + 'trivial_assignment/'
        expected_assignment = {0 : {'eyw3' : ['a1', 'a2', 'a3', 'a4', 'a5']},
                               1 : {'jasonx3' : ['b1', 'b2', 'b3', 'b4', 'b5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_no_greedy_sections(self):
        """ Tests that no greedy sections are assigned when not specified in the config """
        config.num_sections_to_greedy_preselect = 0
        test_data_dir = TEST_DATA_PREFIX + 'trivial_assignment/'
        expected_assignment = {}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_less_sections_than_asked_for(self):
        """ Tests that the max number of assignments is returned when asked for more than the max """
        config.num_sections_to_greedy_preselect = 10
        test_data_dir = TEST_DATA_PREFIX + '3_sections_asked_for_10/'
        expected_assignment = {0 : {'eyw3' : ['a1', 'a2', 'a3', 'a4', 'a5']},
                               1 : {'jasonx3' : ['b1', 'b2', 'b3', 'b4', 'b5']},
                               2 : {'csettl2' : ['c1', 'c2', 'c3', 'c4', 'c5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_mods_obey_physics(self):
        """ Tests that the same moderator is not assigned to the same time more than once """
        config.num_sections_to_greedy_preselect = 3
        test_data_dir = TEST_DATA_PREFIX + 'mods_obey_physics/'
        expected_assignment = {0 : {'mharty2' : ['a1', 'a2', 'a3', 'a4', 'a5']},
                               1 : {'mharty2' : ['c1', 'c2', 'c3', 'c4', 'c5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_most_constraining_picked(self):
        """ Tests that the most constraining students and mods are chosen in the most constraining time """
        config.num_sections_to_greedy_preselect = 2
        test_data_dir = TEST_DATA_PREFIX + 'most_constraining_picked/'
        expected_assignment = {0 : {'eyw3' : ['a1', 'a2', 'a3', 'a4', 'a5']},
                               2 : {'jasonx3' : ['c1', 'c2', 'c3', 'c4', 'c5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_one_mod_two_sections(self):
        """ Tests that greedy assignment can give more than one section to a moderator """
        config.num_sections_to_greedy_preselect = 3
        test_data_dir = TEST_DATA_PREFIX + 'one_mod_two_sections/'
        expected_assignment = {0 : {'eyw3' : ['a1', 'a2', 'a3', 'a4', 'a5']},
                               2 : {'csettl2' : ['b1', 'b2', 'b3', 'b4', 'b5'],
                                    'eyw3' : ['c1', 'c2', 'c3', 'c4', 'c5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_no_yellow_times(self):
        """ Tests that only green times are considered for greedy assignments to be made """
        config.num_sections_to_greedy_preselect = 3
        test_data_dir = TEST_DATA_PREFIX + 'no_yellow_times/'
        expected_assignment = {}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_no_mods_left_to_assign(self):
        """ Tests that greedy assignment stops when all mods have been assigned their max sections """
        config.num_sections_to_greedy_preselect = 4
        test_data_dir = TEST_DATA_PREFIX + 'no_mods_left/'
        expected_assignment = {0 : {'davidb2' : ['a1', 'a2', 'a3', 'a4', 'a5']},
                               1 : {'pjg4' : ['b1', 'b2', 'b3', 'b4', 'b5']},
                               2 : {'davidb2' : ['c1', 'c2', 'c3', 'c4', 'c5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_all_sections_need_min_students(self):
        """ Tests that a greedy assignment can't create a section with students < min per section """
        config.num_sections_to_greedy_preselect = 3
        test_data_dir = TEST_DATA_PREFIX + 'sections_need_min_students/'
        expected_assignment = {0 : {'eyw3' : ['a1', 'a2', 'a3', 'a4', 'a5']},
                               1 : {'jasonx3' : ['b1', 'b2', 'b3', 'b4', 'b5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_more_than_three_rooms(self):
        """ Tests that a greedy assignment works with a non-standard setup of 4 rooms in the first time """
        config.num_sections_to_greedy_preselect = 5
        test_data_dir = TEST_DATA_PREFIX + 'more_than_three_rooms/'
        expected_assignment = {0 : {'eyw3' : ['a1', 'a2', 'a3', 'a4', 'a5'],
                                    'jasonx3' : ['b1', 'b2', 'b3', 'b4', 'b5'],
                                    'csettl2' : ['c1', 'c2', 'c3', 'c4', 'c5'],
                                    'davidb2' : ['d1', 'd2', 'd3', 'd4', 'd5']},
                               1 : {'jasonx3' : ['e1', 'e2', 'e3', 'e4', 'e5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment, non_standard_rooms=True)

    def test_less_than_three_rooms(self):
        """ Tests that greedy assignment ends early when out of rooms to assign """
        config.num_sections_to_greedy_preselect = 3
        test_data_dir = TEST_DATA_PREFIX + 'less_than_three_rooms/'
        expected_assignment = {0 : {'eyw3' : ['a1', 'a2', 'a3', 'a4', 'a5'],
                                    'davidb2' : ['b1', 'b2', 'b3', 'b4', 'b5']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment, non_standard_rooms=True)

    def test_less_students_per_section(self):
        """ Tests that less students per section are assigned when specified in the config """
        config.min_students_per_section = 4
        config.num_sections_to_greedy_preselect = 3
        test_data_dir = TEST_DATA_PREFIX + 'smaller_min_students/'
        expected_assignment = {0 : {'eyw3' : ['a1', 'a2', 'a3', 'a4']},
                               1 : {'davidb2' : ['b1', 'b2', 'b3', 'b4']}}
        self.verify_greedy_assignment(test_data_dir, expected_assignment)

    def test_complex_assignment(self):
        """ Tests that a valid greedy assignment exists on complicated data """
        config.num_sections_to_greedy_preselect = 5
        test_data_dir = TEST_DATA_PREFIX + 'complex_assignment/'
        mod_doodle_poll_csv_path = (test_data_dir + 'mod_preferences.csv')
        mod_max_sections_csv_path = (test_data_dir + 'mod_max_sections.csv')
        student_doodle_poll_csv_path = (test_data_dir + 'student_preferences.csv')
        section_times_csv_path = None

        # Get the constraint programming model
        test_csv_files = (mod_doodle_poll_csv_path, mod_max_sections_csv_path,
                          student_doodle_poll_csv_path, section_times_csv_path)
        (model, mod_time_variables, student_time_variables,
         max_sections_per_mod, max_sections_per_time) = getModelFromInputFiles(*test_csv_files)

        # Attempt a greedy assignment on the model
        greedy_assignment = getGreedyAssignment(mod_time_variables, student_time_variables,
                                                max_sections_per_time, max_sections_per_mod)

        # Verify we received the requested number of sections
        self.assertEqual(len(greedy_assignment), config.num_sections_to_greedy_preselect)

    def verify_greedy_assignment(self, test_data_dir, expected_assignment, non_standard_rooms=False):
        mod_doodle_poll_csv_path = (test_data_dir + 'mod_preferences.csv')
        mod_max_sections_csv_path = (test_data_dir + 'mod_max_sections.csv')
        student_doodle_poll_csv_path = (test_data_dir + 'student_preferences.csv')
        section_times_csv_path = (test_data_dir + 'section_times.csv') if non_standard_rooms else None

        # Get the constraint programming model
        test_csv_files = (mod_doodle_poll_csv_path, mod_max_sections_csv_path,
                          student_doodle_poll_csv_path, section_times_csv_path)
        (model, mod_time_variables, student_time_variables,
         max_sections_per_mod, max_sections_per_time) = getModelFromInputFiles(*test_csv_files)

        # Attempt a greedy assignment on the model
        greedy_assignment = getGreedyAssignment(mod_time_variables, student_time_variables,
                                                max_sections_per_time, max_sections_per_mod)

        # Verify that the assignment has the expected number of sections
        expected_num_sections = sum(len(expected_assignment[time_index])
                                    for time_index in expected_assignment)
        self.assertEqual(len(greedy_assignment), expected_num_sections)

        # Verify the greedy assignment makes the expected sections
        for (time_index, greedy_mod_index, greedy_student_indices) in greedy_assignment:
            mod_net_id = mod_time_variables[greedy_mod_index][time_index].net_id
            student_net_ids = [student_time_variables[student_index][time_index].net_id
                               for student_index in greedy_student_indices]

            self.assertIn(time_index, expected_assignment)
            self.assertIn(mod_net_id, expected_assignment[time_index])
            self.assertCountEqual(student_net_ids, expected_assignment[time_index][mod_net_id])
