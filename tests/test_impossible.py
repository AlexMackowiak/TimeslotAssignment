import unittest
from assign_time_slots import assignModeratorsAndStudents

class TestImpossible(unittest.TestCase):
    """ Tests that no assignments can be made for inputs with no solution """

    def test_too_many_students_no_solution(self):
        """ Tests that no assignment can be made when one section would have to have 8 students """
        test_data_dir = 'test_data/too_many_students/'
        self.verify_no_solution(test_data_dir)

    def test_too_few_students_no_solution(self):
        """ Tests that no assignment can be made when one section would have to have 2 students """
        test_data_dir = 'test_data/too_few_students/'
        self.verify_no_solution(test_data_dir)

    def test_too_few_mods_no_solution(self):
        """ Tests that no assignment can be made when there are not enough moderators """
        test_data_dir = 'test_data/too_few_mods/'
        self.verify_no_solution(test_data_dir)

    def test_mod_with_zero_max_sections(self):
        """ Tests that a moderator with zero max sections is not assigned a section """
        test_data_dir = 'test_data/zero_max_sections/'
        self.verify_no_solution(test_data_dir)

    def verify_no_solution(self, test_data_dir):
        mod_doodle_poll_csv_path = (test_data_dir + 'mod_preferences.csv')
        mod_max_sections_csv_path = (test_data_dir + 'mod_max_sections.csv')
        student_doodle_poll_csv_path = (test_data_dir + 'student_preferences.csv')

        with self.assertRaises(AssertionError):
            assignModeratorsAndStudents(mod_doodle_poll_csv_path, mod_max_sections_csv_path,
                                        student_doodle_poll_csv_path)
