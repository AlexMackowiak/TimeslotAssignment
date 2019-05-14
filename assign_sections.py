import csv
import config
from assign_time_slots import assignModeratorsAndStudents
from create_sections_from_time_slots import assignSectionsFromSectionTimes

def main():
    # Assign moderators and students to their time slots
    (mods_assigned_to_times, students_assigned_to_times) = assignModeratorsAndStudents(config.mod_doodle_poll_csv_path,
                                                                                       config.mod_max_sections_csv_path,
                                                                                       config.student_doodle_poll_csv_path)
    # Assign moderators and students to sections within their assigned time slots
    assert len(mods_assigned_to_times) == len(students_assigned_to_times)
    section_assignments = assignSectionsFromSectionTimes(mods_assigned_to_times, students_assigned_to_times)

    # Write the final section assignment out to a CSV for use with the email script
    mod_net_id_to_name_dict = readModNetIDToNameMapping(config.mod_net_id_to_name_csv_path)
    write_sections_to_csv(section_assignments, mod_net_id_to_name_dict)

def write_sections_to_csv(section_assignments, mod_net_id_to_name_dict):
    """
        Writes the already assigned sections to a CSV for use in the email script

        Args:
            section_assignments: List of List of Section representing all Sections created at each time index
            mod_net_id_to_name_dict: A dictionary mapping from moderator NetID to moderator name
    """
    # Read the names for the section times like "Wednesday 10 AM - 12 PM" into a list
    with open(config.section_times_csv_path, 'r', encoding='utf-8-sig') as section_times_file:
        times = list(csv.reader(section_times_file))

    # Write the section assignments to the final output csv path
    with open(config.output_csv_path, 'w+', encoding='utf-8-sig') as output_file:
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

            # Do some rudimentary error checking, SP19 had two mods with flipped Net IDs
            if config.mod_net_id_error_check:
                (first_name, last_name) = name.lower().split(' ', 1)
                if (net_id[0] != first_name[0]) and (net_id[0] != last_name[0]):
                    print('Warning: Net ID ' + net_id + ' does not appear to correspond to ' + name,
                          'please double check this')

            mod_net_id_to_name_dict[net_id] = name

    return mod_net_id_to_name_dict

if __name__ == '__main__':
    main()
