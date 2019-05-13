import random

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
    rooms = ['Siebel 1112', 'Siebel 1314', 'Siebel 1112', 'Siebel 4102']

    sections_in_each_time = []
    num_sections_with_five = 0
    for time_index in range(len(mods_assigned_to_times)):
        mods_in_time = mods_assigned_to_times[time_index]
        students_in_time = students_assigned_to_times[time_index]

        # Randomly assign moderators for the section time to a room
        num_sections_in_time = len(mods_in_time)
        sections_in_time = [Section(popRandomElement(mods_in_time), rooms[i])
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
            if len(section.student_net_ids) == 5:
                num_sections_with_five += 1

        sections_in_each_time.append(sections_in_time)

    print('Number of sections with 5 students:', num_sections_with_five)
    return sections_in_each_time
