import config
import unittest
from assign_time_slots import assignModeratorsAndStudents
from create_sections_from_time_slots import assignSectionsFromSectionTimes
TEST_DATA_PREFIX = 'test_data/impossible_test_data/'

class TestImpossible(unittest.TestCase):
    """ Tests that no assignments can be made for inputs with no solution """

    def setUp(self):
        # Ensure that config options are correct for testing
        config.assign_exact_max_sections = False
        config.only_allow_optimal_solutions = True
        config.prefer_contiguous_sections_preferred_times_only = False
        config.prefer_contiguous_sections_all_possible = False
        config.allow_impossible_times = False
        config.impossible_time_percentage = 0.0
        config.min_students_per_section = 5
        config.max_students_per_section = 6

    def test_too_many_students_no_solution(self):
        """ Tests that no assignment can be made when one section would need to have 8 students """
        test_data_dir = TEST_DATA_PREFIX + 'too_many_students/'
        self.verify_no_solution(test_data_dir)
        self.verify_solution_exists_with_impossible_times(test_data_dir, solution_should_exist=True)

    def test_too_few_students_no_solution(self):
        """ Tests that no assignment can be made when one section would need to have 2 students """
        test_data_dir = TEST_DATA_PREFIX + 'too_few_students/'
        self.verify_no_solution(test_data_dir)
        self.verify_solution_exists_with_impossible_times(test_data_dir, solution_should_exist=True)

    def test_too_few_mods_no_solution(self):
        """ Tests that no assignment can be made when there are not enough moderators """
        test_data_dir = TEST_DATA_PREFIX + 'too_few_mods/'
        self.verify_no_solution(test_data_dir)
        self.verify_solution_exists_with_impossible_times(test_data_dir, solution_should_exist=False)

    def test_mod_with_zero_max_sections(self):
        """ Tests that a moderator with zero max sections is not assigned a section """
        test_data_dir = TEST_DATA_PREFIX + 'zero_max_sections/'
        self.verify_no_solution(test_data_dir)
        self.verify_solution_exists_with_impossible_times(test_data_dir, solution_should_exist=False)

    def test_no_mod_available_at_time(self):
        """
            This test reproduced the "ghost section" problem where a section was created with students
             but no moderator. This issue was fixed as a result of this test, and sections without a
             moderator should no longer be possible.
        """
        test_data_dir = TEST_DATA_PREFIX + 'no_mod_available_at_time/'
        self.verify_no_solution(test_data_dir)
        # This test takes seemingly exponential time to complete with impossible times allowed
        #self.verify_solution_exists_with_impossible_times(test_data_dir, solution_should_exist=True)

    def verify_no_solution(self, test_data_dir):
        mod_doodle_poll_csv_path = (test_data_dir + 'mod_preferences.csv')
        mod_max_sections_csv_path = (test_data_dir + 'mod_max_sections.csv')
        student_doodle_poll_csv_path = (test_data_dir + 'student_preferences.csv')
        csv_files = (mod_doodle_poll_csv_path, mod_max_sections_csv_path, student_doodle_poll_csv_path)

        # When impossible times are not allowed, no assignment should be possible
        with self.assertRaises(AssertionError):
            assignModeratorsAndStudents(*csv_files)

    def verify_solution_exists_with_impossible_times(self, test_data_dir, solution_should_exist=True):
        mod_doodle_poll_csv_path = (test_data_dir + 'mod_preferences.csv')
        mod_max_sections_csv_path = (test_data_dir + 'mod_max_sections.csv')
        student_doodle_poll_csv_path = (test_data_dir + 'student_preferences.csv')
        csv_files = (mod_doodle_poll_csv_path, mod_max_sections_csv_path, student_doodle_poll_csv_path)

        config.allow_impossible_times = True
        config.impossible_time_percentage = 1.0
        if solution_should_exist:
            # When impossible times are allowed, some assignment should exist
            assignModeratorsAndStudents(*csv_files)
        else:
            # Even using impossible times no solution should exist
            with self.assertRaises(AssertionError):
                assignModeratorsAndStudents(*csv_files)
