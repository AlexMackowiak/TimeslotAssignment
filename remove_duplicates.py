import sys
import csv
from collections import OrderedDict

DOODLE_RESPONSE_START_LINE = 6

def printUsage():
    print('This program takes one argument: the Doodle poll preference .csv for which to remove earlier netIDs with later poll submissions')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        printUsage()
        exit()

    preference_csv_path = sys.argv[1]
    assert preference_csv_path.endswith('.csv')

    with open(preference_csv_path, 'r+', encoding='utf-8-sig') as pref_file:
        pref_csv_contents = list(csv.reader(pref_file))
        num_duplicates_removed = 0

        # Map each net ID only to its most recent entry
        latest_preferences = OrderedDict();
        for entry in pref_csv_contents[DOODLE_RESPONSE_START_LINE:]:
            netID = entry[0]
            if netID in latest_preferences:
                num_duplicates_removed += 1
            latest_preferences[netID] = entry

    # Rewrite file contents with only most recent preferences
    dot_index = preference_csv_path.find('.')
    replaced_csv_path = preference_csv_path[0:dot_index] + '_no_duplicates.csv'

    with open(replaced_csv_path, 'w+', encoding='utf-8-sig') as output_file:
        pref_writer = csv.writer(output_file, quoting=csv.QUOTE_NONE, escapechar='\\')
        for line in pref_csv_contents[0:DOODLE_RESPONSE_START_LINE]:
            pref_writer.writerow(line)

        for netID in latest_preferences:
            pref_writer.writerow(latest_preferences[netID])

    # Print number replaced
    print('Doodle poll preference file rewritten to ' + replaced_csv_path)
    print('Duplicate entries removed: ' + str(num_duplicates_removed))
