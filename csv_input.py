import csv

def readDoodlePreferences(doodle_poll_csv_path):
    """
        Reads in the time preferences for every person from a preprocessed Doodle poll .csv file

        Args:
            doodle_poll_csv_path: The file path to the preprocessed Doodle poll spreadsheet in .csv format

        Returns:
            net_ids: List of Strings for each person's net ID
            time_preferences: List where each entry is all the time preferences for a person
                                    time preferences are a List of Strings where for each time slot in the Doodle poll
                                    'OK' represents a preferred time
                                    '(OK)' represents a time that is not preferred but would work
                                    '' represents a time that will not work for the person

            Both lists returned store information for the same person at the same index
            Probably should make some data container object instead... TODO
    """
    net_ids = []
    all_time_preferences = []

    with open(doodle_poll_csv_path, 'r', encoding='utf-8-sig') as pref_file:
        for preference_entry in csv.reader(pref_file):
            net_id = preference_entry[0]
            time_preferences = preference_entry[1:]

            net_ids.append(net_id)
            all_time_preferences.append(time_preferences)

    return net_ids, all_time_preferences

def readModMaxSectionPreferences(max_sections_csv_path, mod_net_ids):
    """
        Reads in the max section preferences from a csv where each line is like:
        amackow2,2
        for the moderator with net ID "amackow2" to have at most 2 sections, the order of net IDs
        in this file does not matter

        Args:
            max_sections_csv_path: The path to the csv file following the format stated above
            mod_net_ids: List of Strings for the net IDs of all moderators with a Doodle poll entry

        Returns:
            List of Integers for the max number of sections each moderator will take in the same order
                as the mod_net_ids parameter

        Raises:
            AssertionError: if there are any mods with a Doodle poll entry but no max section entry
    """
    max_sections_per_mod = [0] * len(mod_net_ids)
    all_mods_accounted_for = True

    # Map net IDs to their list index so order doesn't matter in the .csv
    mod_net_id_to_index_dict = {}
    for (mod_index, mod_net_id) in enumerate(mod_net_ids):
        mod_net_id_to_index_dict[mod_net_id] = mod_index

    with open(max_sections_csv_path, 'r', encoding='utf-8-sig') as max_sections_csv:
        for entry in csv.reader(max_sections_csv):
            net_id = entry[0]
            max_sections = int(entry[1])

            if net_id not in mod_net_id_to_index_dict:
                #all_mods_accounted_for = False
                print('Mod has max sections entry but no Doodle poll entry: ' + net_id)
                continue

            mod_index = mod_net_id_to_index_dict[net_id]
            del mod_net_id_to_index_dict[net_id] # Remove so we catch duplicate entries
            max_sections_per_mod[mod_index] = max_sections

    if len(mod_net_id_to_index_dict) > 0:
        all_mods_accounted_for = False
        for leftover_net_id in mod_net_id_to_index_dict:
            print('Mod has Doodle poll entry but no max sections entry: ' + leftover_net_id)

    assert all_mods_accounted_for
    return max_sections_per_mod

def readModNetIDToNameMapping(mod_net_id_to_name_csv_path, mod_net_id_error_check):
    """
        Args:
            mod_net_id_to_name_csv_path: The file path to the CSV file containing
                                            the mod net ID to mod name mapping
            mod_net_id_error_check: if True, some basic error checking is performed and will
                                    print to console in the likely event that it finds a Net ID
                                    which does not conform to the validation criteria

        Returns: A dictionary with the mapping for each mod net ID to the moderator's name
    """
    mod_net_id_to_name_dict = {}

    with open(mod_net_id_to_name_csv_path, 'r', encoding='utf-8-sig') as mapping_file:
        for entry in csv.reader(mapping_file):
            net_id = entry[0]
            name = entry[1]

            # Do some rudimentary error checking, SP19 had two mods with flipped Net IDs
            if mod_net_id_error_check:
                (first_name, last_name) = name.lower().split(' ', 1)
                if (net_id[0] != first_name[0]) and (net_id[0] != last_name[0]):
                    print('Warning: Net ID ' + net_id + ' does not appear to correspond to ' + name,
                          'please double check this')

            mod_net_id_to_name_dict[net_id] = name

    return mod_net_id_to_name_dict

def readSectionTimeInfo(section_time_csv_path):
    """
        Args:
            section_time_csv_path: The file path to a CSV file with [section time],[num rooms at time]
                                    format. Example: "Wednesday 10 AM - 12 PM,4"

        Returns:
            section_times: List of String where each index is the description of the section time
            num_rooms_in_each_time: List of Integer where each index is the number of rooms
                                    available at that time index
    """
    section_times = []
    num_rooms_in_each_time = []

    with open(section_time_csv_path, 'r', encoding='utf-8-sig') as section_time_file:
        for entry in csv.reader(section_time_file):
            section_times.append(entry[0])
            num_rooms_in_each_time.append(int(entry[1]))

    return section_times, num_rooms_in_each_time
