import csv
import sys

def main(doodle_poll_csv_path, output_path, num_lines_to_remove):
    num_rows_processed = 0

    with open(doodle_poll_csv_path, 'r', encoding='utf-8-sig') as pref_file:
        with open(output_path, 'w', encoding='utf-8-sig') as output_file:
            output_writer = csv.writer(output_file, quoting=csv.QUOTE_NONE)

            for preference_entry in csv.reader(pref_file):
                assert (len(preference_entry) >= 2)
                net_id = preference_entry[0]
                time_preferences = preference_entry[1:]

                yellows_removed_row = [net_id]
                for time_preference in time_preferences:
                    if time_preference == '(OK)' and num_rows_processed < num_lines_to_remove:
                        yellows_removed_row.append('')
                    else:
                        yellows_removed_row.append(time_preference)
                
                output_writer.writerow(yellows_removed_row)
                num_rows_processed += 1

if __name__ == '__main__':
    if (len(sys.argv) == 4):
        main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
