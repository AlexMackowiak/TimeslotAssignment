import config
import random
from csv_input import readSectionTimeInfo

class Section:
    def __init__(self, mod_net_id, room):
        self.mod_net_id = mod_net_id
        self.room = room
        self.student_net_ids = []

    def addStudent(self, student_net_id):
        self.student_net_ids.append(student_net_id)

def popRandomElement(list_to_pop):
    random_index = random.randint(0, (len(list_to_pop) - 1))
    return list_to_pop.pop(random_index)

def assignSectionsFromSectionTimes(mods_assigned_to_times, students_assigned_to_times):
    """
        Args:
            mods_assigned_to_times: List of List of Strings where the entry at each index is all net IDs of the
                                       moderators assigned to that time index 
            students_assigned_to_times: List of List of Strings where the entry at each index is all net IDs of the
                                            students assigned to that time index

        Returns: List of List of Section where the entry at each index is all Sections complete with moderator, 
                    room, and students that have been assigned to that time index
    """
    random.seed("Creatively Titled Section Assignment Seed") # Ensure deterministic behavior
    (_, rooms_in_each_time) = readSectionTimeInfo(config.section_times_csv_path)

    sections_in_each_time = []
    num_sections_with_min = 0
    for time_index in range(len(mods_assigned_to_times)):
        mods_in_time = mods_assigned_to_times[time_index]
        students_in_time = students_assigned_to_times[time_index]
        rooms_in_time = rooms_in_each_time[time_index]

        # Need to turn [('Siebel 1112', 2), ('Siebel 1314', 1), ('Siebel 4102', 1)]
        # into an ordering with repeats: ['Siebel 1112', 'Siebel 1314', 'Siebel 4102', 'Siebel 1112']
        i = 0
        room_order = []
        while len(rooms_in_time) > 0:
            i = i % len(rooms_in_time)
            room_order.append(rooms_in_time[i].name)
            rooms_in_time[i].max_sections -= 1
            if rooms_in_time[i].max_sections <= 0:
                del rooms_in_time[i]
                i -= 1
            i += 1

        # Randomly assign moderators for the section time to a room
        num_sections_in_time = len(mods_in_time)
        sections_in_time = [Section(popRandomElement(mods_in_time), room_order[i])
                            for i in range(num_sections_in_time)]

        # Randomly remove students from the students in this time slot and put them in a section
        section_index = 0
        for _ in range(len(students_in_time)):
            random_student = popRandomElement(students_in_time)
            sections_in_time[section_index].addStudent(random_student)

            section_index += 1
            section_index %= len(sections_in_time)

        print('Time', time_index)
        for section in sections_in_time:
            print(section.mod_net_id + ':', section.student_net_ids, 'room:', section.room)
            if len(section.student_net_ids) == config.min_students_per_section:
                num_sections_with_min += 1

        sections_in_each_time.append(sections_in_time)

    print('Number of sections with', config.min_students_per_section, 'students:', num_sections_with_min)
    return sections_in_each_time
