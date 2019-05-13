import csv
from assign_time_slots import assignModeratorsAndStudents
from create_sections_from_time_slots import assignSectionsFromSectionTimes

def main():
    test_data_directory = 'test_data/sp19_data/'
    mod_doodle_poll_csv_path = test_data_directory + 'mod_preferences.csv'
    mod_max_sections_csv_path = test_data_directory + 'mod_max_sections.csv'
    student_doodle_poll_csv_path = test_data_directory + 'student_preferences.csv'
    (mods_assigned_to_times, students_assigned_to_times) = assignModeratorsAndStudents(mod_doodle_poll_csv_path,
                                                                                       mod_max_sections_csv_path,
                                                                                       student_doodle_poll_csv_path)
    assert len(mods_assigned_to_times) == len(students_assigned_to_times)
    section_assignments = assignSectionsFromSectionTimes(mods_assigned_to_times, students_assigned_to_times)

    mod_net_id_to_name_csv_path = 'sp19_full_data/sp19_mod_net_ids_to_names.csv'
    mod_net_id_to_name_dict = readModNetIDToNameMapping(mod_net_id_to_name_csv_path)
    write_sections_to_csv(section_assignments, mod_net_id_to_name_dict)

def write_sections_to_csv(section_assignments, mod_net_id_to_name_dict):
    """
        Writes the already assigned sections to a CSV for use in the email script

        Args:
            section_assignments: List of List of Section representing all Sections created at each time index
            mod_net_id_to_name_dict: A dictionary mapping from moderator NetID to moderator name
    """
    # Note to self: Read this in from a file
    times = ['Wednesday 10 AM - 12 PM', 'Wednesday 12 PM - 2 PM', 'Wednesday 2 PM - 4 PM', 'Wednesday 4 PM - 6 PM', 'Wednesday 6 PM - 8 PM',
             'Thursday 10 AM - 12 PM', 'Thursday 12 PM - 2 PM', 'Thursday 2 PM - 4 PM', 'Thursday 4 PM - 6 PM', 'Thursday 6 PM - 8 PM',
             'Friday 10 AM - 12 PM', 'Friday 12 PM - 2 PM', 'Friday 2 PM - 4 PM', 'Friday 4 PM - 6 PM', 'Friday 6 PM - 8 PM', 
             'Saturday 10 AM - 12 PM', 'Saturday 12 PM - 2 PM', 'Saturday 2 PM - 4 PM', 'Saturday 4 PM - 6 PM', 'Saturday 6 PM - 8 PM']

    # Note to self: Put this in a config file
    output_csv_path = 'sp19_final_assignments.csv'

    with open(output_csv_path, 'w+', encoding='utf-8-sig') as output_file:
        output_writer = csv.writer(output_file, quoting=csv.QUOTE_NONE)

        for time_index in range(len(section_assignments)):
            time_for_index = times[time_index]

            for section_in_time in section_assignments[time_index]:
                section_mod = mod_net_id_to_name_dict[section_in_time.mod_net_id]
                section_room = section_in_time.room

                for student_net_id in section_in_time.student_net_ids:
                    output_writer.writerow([student_net_id, time_for_index, section_mod, section_room])

def readModNetIDToNameMapping(mod_net_id_to_name_csv_path):
    """
        Args:
            mod_net_id_to_name_csv_path: The file path to the CSV file containing
                                            the mod net ID to mod name mapping

        Returns: A dictionary with the mapping for each mod net ID to the moderator's name
    """
    mod_net_id_to_name_dict = {}

    with open(mod_net_id_to_name_csv_path, 'r', encoding='utf-8-sig') as mapping_file:
        for entry in csv.reader(mapping_file):
            net_id = entry[0]
            name = entry[1]

            mod_net_id_to_name_dict[net_id] = name

    return mod_net_id_to_name_dict

if __name__ == '__main__':
    main()
