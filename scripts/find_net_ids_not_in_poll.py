import csv
import sys

# Simple script to find students who have not yet filled out the poll
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Needs 2 arguments: [student preferences csv] [class roster csv]')
        exit(-1)

    processed_preference_csv_path = sys.argv[1]
    assert processed_preference_csv_path.endswith('.csv')

    class_roster_csv_path = sys.argv[2]
    assert class_roster_csv_path.endswith('.csv')

    # Collect all the Net IDs for students who filled out the poll
    students_who_filled_out_poll = set()
    with open(processed_preference_csv_path, 'r', encoding='utf-8-sig') as pref_file:
         for entry in csv.reader(pref_file):
            net_id = entry[0]
            students_who_filled_out_poll.add(net_id)

    # Collect all the Net IDs for students in the class
    students_in_class = set()
    with open(class_roster_csv_path, 'r', encoding='utf-8-sig') as roster_file:
         for entry in csv.reader(roster_file):
            net_id = entry[0]
            students_in_class.add(net_id)

    # Compare the two to find discrepencies
    print("Students in roster not in poll:")
    for student_in_class in students_in_class:
        if student_in_class not in students_who_filled_out_poll:
            print(student_in_class)

    print("Students in poll not in roster:")
    for student_in_poll in students_who_filled_out_poll:
        if student_in_poll not in students_in_class:
            print(student_in_poll)
