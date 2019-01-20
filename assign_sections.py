import csv
import random
from moderator_assignments import assignModerators
from student_assignments import assignStudents
from experimental_assignments_2 import assignModeratorsAndStudents

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

    mod_net_id_to_name_csv_path = 'sp19_mod_net_ids_to_names.csv'
    mod_net_id_to_name_dict = readModNetIDToNameMapping(mod_net_id_to_name_csv_path)
    write_sections_to_csv(section_assignments, mod_net_id_to_name_dict)

class Section:
    def __init__(self, mod_net_id, room):
        self.mod_net_id = mod_net_id
        self.room = room
        self.student_net_ids = []

    def addStudent(self, student_net_id):
        self.student_net_ids.append(student_net_id)

def assignSectionsFromSectionTimes(mods_assigned_to_times, students_assigned_to_times):
    random.seed("Creatively Titled Section Assignment Seed") # Ensure deterministic behavior
    rooms = ['Siebel 1112', 'Siebel 1314', 'Siebel 1112', 'Siebel 4102']

    sections_in_each_time = []
    num_sections_with_five = 0
    for time_index in range(len(mods_assigned_to_times)):
        mods_in_time = mods_assigned_to_times[time_index]
        students_in_time = students_assigned_to_times[time_index]

        num_sections_in_time = len(mods_in_time)
        sections_in_time = [Section(popRandomElement(mods_in_time), rooms[i])
                            for i in range(num_sections_in_time)]

        section_index = 0
        for _ in range(len(students_in_time)):
            random_student = popRandomElement(students_in_time)
            sections_in_time[section_index].addStudent(random_student)

            section_index += 1
            section_index %= len(sections_in_time)

        print('Time ' + str(time_index))
        for section in sections_in_time:
            if len(section.student_net_ids) == 5:
                num_sections_with_five += 1
            print(section.mod_net_id + ': ' + str(section.student_net_ids) + ' room: ' + section.room)

        sections_in_each_time.append(sections_in_time)

    print('Number of sections with 5 students: ' + str(num_sections_with_five))
    return sections_in_each_time

def popRandomElement(list_to_pop):
    random_index = random.randint(0, (len(list_to_pop) - 1))
    return list_to_pop.pop(random_index)

def write_sections_to_csv(section_assignments, mod_net_id_to_name_dict):
    times = ['Wednesday 10 AM - 12 PM', 'Wednesday 12 PM - 2 PM', 'Wednesday 2 PM - 4 PM', 'Wednesday 4 PM - 6 PM', 'Wednesday 6 PM - 8 PM',
             'Thursday 10 AM - 12 PM', 'Thursday 12 PM - 2 PM', 'Thursday 2 PM - 4 PM', 'Thursday 4 PM - 6 PM', 'Thursday 6 PM - 8 PM',
             'Friday 10 AM - 12 PM', 'Friday 12 PM - 2 PM', 'Friday 2 PM - 4 PM', 'Friday 4 PM - 6 PM', 'Friday 6 PM - 8 PM', 
             'Saturday 10 AM - 12 PM', 'Saturday 12 PM - 2 PM', 'Saturday 2 PM - 4 PM', 'Saturday 4 PM - 6 PM', 'Saturday 6 PM - 8 PM']
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
    mod_net_id_to_name_dict = {}

    with open(mod_net_id_to_name_csv_path, 'r', encoding='utf-8-sig') as mapping_file:
        for entry in csv.reader(mapping_file):
            net_id = entry[0]
            name = entry[1]

            mod_net_id_to_name_dict[net_id] = name

    return mod_net_id_to_name_dict

if __name__ == '__main__':
    main()
