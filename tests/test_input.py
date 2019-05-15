import unittest
from csv_input import readDoodlePreferences, readModMaxSectionPreferences

class TestInput(unittest.TestCase):
    """ Tests related to reading input from CSV formats """

    def test_read_mod_doodle_poll(self):
        mod_doodle_poll_csv_path = 'test_data/basic_functionality/mod_preferences.csv'
        (mod_net_ids, mod_time_preferences) = readDoodlePreferences(mod_doodle_poll_csv_path)

        expected_net_ids = ['amackow2', 'albertl3', 'ysharma5']
        expected_time_preferences = [['OK', '', ''],
                                     ['', 'OK', ''],
                                     ['', '', 'OK']]

        self.assertEqual(mod_net_ids, expected_net_ids)
        self.assertEqual(mod_time_preferences, expected_time_preferences)

    def test_read_mod_max_sections(self):
        mod_doodle_poll_csv_path = 'test_data/two_sections_one_mod/mod_preferences.csv'
        mod_max_sections_csv_path = 'test_data/two_sections_one_mod/mod_max_sections.csv'
        (mod_net_ids, _) = readDoodlePreferences(mod_doodle_poll_csv_path)

        # The max sections data is purposefully out of order to test that order doesn't matter
        max_sections_per_mod = readModMaxSectionPreferences(mod_max_sections_csv_path, mod_net_ids)
        
        expected_max_sections_per_mod = [3, 2, 1]
        self.assertEqual(max_sections_per_mod, expected_max_sections_per_mod)

    def test_read_student_doodle_poll(self):
        student_doodle_poll_csv_path = 'test_data/basic_functionality/student_preferences.csv'
        (net_ids, time_preferences) = readDoodlePreferences(student_doodle_poll_csv_path)
        
        expected_net_ids = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6',
                            'b1', 'b2', 'b3', 'b4', 'b5', 'b6',
                            'c1', 'c2', 'c3', 'c4', 'c5', 'c6']
        expected_time_preferences = [['OK','',''], ['OK','',''], ['OK','',''],
                                     ['OK','',''], ['OK','',''], ['OK','',''],
                                     ['','OK',''], ['','OK',''], ['','OK',''],
                                     ['','OK',''], ['','OK',''], ['','OK',''],
                                     ['','','OK'], ['','','OK'], ['','','OK'],
                                     ['','','OK'], ['','','OK'], ['','','OK']]

        self.assertEqual(net_ids, expected_net_ids)
        self.assertEqual(time_preferences, expected_time_preferences)
