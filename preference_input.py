import csv

DOODLE_RESPONSE_START_LINE = 6

def readDoodlePreferences(doodle_poll_csv_path):
    """
        Reads in the time preferences for every person from a Doodle poll .csv file

        Args:
            doodle_poll_csv_path: The file path to the Doodle poll spreadsheet in .csv format

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

    with open(doodle_poll_csv_path, 'r+', encoding='utf-8-sig') as pref_file:
        # Read in preferences file and trim to the start of the actual preference lines
        preference_data = list(csv.reader(pref_file))
        preference_data = preference_data[DOODLE_RESPONSE_START_LINE:]

        for preference_entry in preference_data:
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

    with open(max_sections_csv_path, 'r+', encoding='utf-8-sig') as max_sections_csv:
        for entry in csv.reader(max_sections_csv):
            net_id = entry[0]
            max_sections = entry[1]

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
