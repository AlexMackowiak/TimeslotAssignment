import unittest
from assign_time_slots import assignModeratorsAndStudents
from create_sections_from_time_slots import assignSectionsFromSectionTimes
TEST_DATA_PREFIX = 'test_data/impossible_test_data/'

class TestImpossible(unittest.TestCase):
    """ Tests that no assignments can be made for inputs with no solution """

    def test_too_many_students_no_solution(self):
        """ Tests that no assignment can be made when one section would have to have 8 students """
        test_data_dir = TEST_DATA_PREFIX + 'too_many_students/'
        self.verify_no_solution(test_data_dir)

    def test_too_few_students_no_solution(self):
        """ Tests that no assignment can be made when one section would have to have 2 students """
        test_data_dir = TEST_DATA_PREFIX + 'too_few_students/'
        self.verify_no_solution(test_data_dir)

    def test_too_few_mods_no_solution(self):
        """ Tests that no assignment can be made when there are not enough moderators """
        test_data_dir = TEST_DATA_PREFIX + 'too_few_mods/'
        self.verify_no_solution(test_data_dir)

    def test_mod_with_zero_max_sections(self):
        """ Tests that a moderator with zero max sections is not assigned a section """
        test_data_dir = TEST_DATA_PREFIX + 'zero_max_sections/'
        self.verify_no_solution(test_data_dir)

    def test_no_mod_available_at_time(self):
        """
            This test reproduced the "ghost section" problem where a section was created with students
             but no moderator. This issue was fixed as a result of this test, and sections without a
             moderator should no longer be possible.
        """
        test_data_dir = TEST_DATA_PREFIX + 'no_mod_available_at_time/'
        self.verify_no_solution(test_data_dir)

    def verify_no_solution(self, test_data_dir):
        mod_doodle_poll_csv_path = (test_data_dir + 'mod_preferences.csv')
        mod_max_sections_csv_path = (test_data_dir + 'mod_max_sections.csv')
        student_doodle_poll_csv_path = (test_data_dir + 'student_preferences.csv')

        with self.assertRaises(AssertionError):
            assignModeratorsAndStudents(mod_doodle_poll_csv_path, mod_max_sections_csv_path,
                                        student_doodle_poll_csv_path)
