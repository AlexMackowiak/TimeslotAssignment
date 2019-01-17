import sys
import csv
from os.path import isfile
from collections import OrderedDict

DOODLE_RESPONSE_START_LINE = 6
DOODLE_RESPONSE_END_LINE = -3
DOODLE_IMPOSSIBLE_TIME = ''
MINIMUM_REQUIRED_TIMES = 7

def printUsage():
    print('This program takes one argument: the Doodle poll preference .csv for which to remove earlier netIDs with later poll submissions')

"""
This script writes to a new file after doing the following 4 things:
1. Replaces names (when people can't read directions) with NetIDs according to a mapping defined in a .csv file
2. Removes all earlier Doodle poll entries by people who have made a more recent poll submission
3. Prints NetIDs for any people who have given less than the minimum number of times
4. Trims the useless starting and ending information from the poll so only time preference information remains in the file
"""
if __name__ == "__main__":
    if len(sys.argv) != 2:
        printUsage()
        exit()

    preference_csv_path = sys.argv[1]
    assert preference_csv_path.endswith('.csv')

    # Build mapping for people who filled out the poll with their name
    name_to_netid_map = {}
    people_who_cant_read_csv_path = 'people_who_cant_read_sp19.csv'
    with open(people_who_cant_read_csv_path, 'r', encoding='utf-8-sig') as cant_read_file:
        for entry in csv.reader(cant_read_file):
            name = entry[0]
            netID = entry[1]
            name_to_netid_map[name] = netID

    with open(preference_csv_path, 'r', encoding='utf-8-sig') as pref_file:
        pref_csv_contents = list(csv.reader(pref_file))
        # Trim useless beginning and ending CSV stuff
        pref_csv_contents = pref_csv_contents[DOODLE_RESPONSE_START_LINE:
                                              DOODLE_RESPONSE_END_LINE]
        num_names_fixed = 0
        num_duplicates_removed = 0

        # Map each net ID only to its most recent entry
        latest_entries = OrderedDict();
        for entry in pref_csv_contents:
            netID = entry[0]

            # Correct it if it's a name
            if netID in name_to_netid_map:
                netID = name_to_netid_map[netID]
                entry[0] = netID
                num_names_fixed += 1

            # Make sure it actually looks somewhat like a netID
            if ((not netID[0].isalpha()) or (not netID[-1].isdigit())) and (netID != 'gsoares'):
                print(netID + ' does not look like a NetID, skipping')
                continue

            # Standardize on lowercase
            netID = netID.lower()
            entry[0] = netID

            if netID in latest_entries:
                num_duplicates_removed += 1
            latest_entries[netID] = entry

    # Find students who didn't give us enough times
    for netID in latest_entries:
        preferences = latest_entries[netID][1:]
        num_times_given = 0

        for preference in preferences:
            if preference != DOODLE_IMPOSSIBLE_TIME:
                num_times_given += 1

        if num_times_given < MINIMUM_REQUIRED_TIMES:
            print(netID + ': ' + str(num_times_given) + ' times')

    # Rewrite file contents with only most recent preferences
    dot_index = preference_csv_path.find('.')
    replaced_csv_path = preference_csv_path[0:dot_index] + '_no_duplicates.csv'

    with open(replaced_csv_path, 'w+', encoding='utf-8-sig') as output_file:
        pref_writer = csv.writer(output_file, quoting=csv.QUOTE_NONE, escapechar='\\')
        #for line in pref_csv_contents[0:DOODLE_RESPONSE_START_LINE]:
        #    pref_writer.writerow(line)

        for netID in latest_entries:
            pref_writer.writerow(latest_entries[netID])

    # Print number replaced
    print('Doodle poll preference file rewritten to ' + replaced_csv_path)
    print('Duplicate entries removed: ' + str(num_duplicates_removed))
    print('Names substituted for NetIDs: ' + str(num_names_fixed))
