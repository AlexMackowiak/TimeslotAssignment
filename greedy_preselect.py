from collections import defaultdict
import config
from math import inf
UNUSABLE_VALUE = inf

def getMostConstrainingIndices(most_constraining_time_index, person_time_variables, max_sections_per_person,
                               num_indices_to_get, assigned_times):
    num_people = len(person_time_variables)
    num_section_times = len(person_time_variables[0])

    # Get the number of valid times for each unassigned person and return the most constraining people
    num_times_per_person = [sum(1
                                if (person_time_variables[i][j] is not None)
                                else 0
                                for j in range(num_section_times)
                               )
                            if (person_time_variables[i][most_constraining_time_index] is not None) and
                               (max_sections_per_person[i] > 0) and
                               (most_constraining_time_index not in assigned_times[i])
                            else UNUSABLE_VALUE
                            for i in range(num_people)]
    constraining_indices_sorted = sorted(range(num_people), key=lambda i: num_times_per_person[i])

    # Get the N most constraining people with a green time in the most constraining time index
    i = 0
    most_constraining_green_indices = []
    while len(most_constraining_green_indices) < num_indices_to_get:
        current_person_index = constraining_indices_sorted[i]
        current_person_var = person_time_variables[current_person_index][most_constraining_time_index]
        if (current_person_var is not None) and (current_person_var.is_preferred_time):
            most_constraining_green_indices.append(current_person_index)
        i += 1
    return most_constraining_green_indices

def greedyPreselectSections(model, mod_time_variables, student_time_variables, max_sections_per_time, max_sections_per_mod):
    greedy_assignment = getGreedyAssignment(mod_time_variables, student_time_variables,
                                            max_sections_per_time, max_sections_per_mod)

    # Actually apply the greedy assignment to the constraint programming model
    for (most_constraining_time_index, greedy_mod_index, greedy_student_indices) in greedy_assignment:
        model.Add(mod_time_variables[greedy_mod_index][most_constraining_time_index].variable == 1)
        for greedy_student_index in greedy_student_indices:
            model.Add(student_time_variables[greedy_student_index][most_constraining_time_index].variable == 1)

    return len(greedy_assignment)

def getGreedyAssignment(mod_time_variables, student_time_variables, max_sections_per_time, max_sections_per_mod):
    """
        Attempts to greedily select ahead of time a number of sections 

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student
            max_sections_per_time: List of Integer where each index represents the number of rooms
                                    available at that time index
            max_sections_per_mod: List of Integer, each entry is the max sections for that mod_index
    """
    # Greedy algorithm currently picks the most constraining students and moderators
    # Document this ^ above
    greedy_assignment = []

    num_mods = len(mod_time_variables)    
    num_students = len(student_time_variables)
    num_section_times = len(max_sections_per_time)
    max_sections_per_student = [1] * num_students
    max_sections_per_mod = max_sections_per_mod.copy() # Can't modify outside this function
    max_sections_per_time = max_sections_per_time.copy() # Can't modify outside this function
    mod_assigned_times = defaultdict(set)
    # Keep track of how many students put green for each time slot and decrement as we greedy assign them
    num_students_with_each_time = [sum(1
                                       if (student_time_variables[i][j] is not None) and
                                          (student_time_variables[i][j].is_preferred_time)
                                       else 0
                                       for i in range(num_students))
                                   for j in range(num_section_times)]

    # Loop until we can't assign any more greedy sections
    while len(greedy_assignment) < config.num_sections_to_greedy_preselect:
        # Preferably take as few students as possible and let CP sort out the rest
        valid_greedy_section_time_found = False
        while not valid_greedy_section_time_found:
            # Find the time with the least students still >= config.min
            (most_constraining_time_index, num_students_with_time) = min(enumerate(num_students_with_each_time),
                                                                         key=lambda x: x[1])

            if num_students_with_time == UNUSABLE_VALUE:
                # No more valid times remain, we have greedy selected as much as possible
                return greedy_assignment

            if num_students_with_time < config.min_students_per_section:
                # Not enough students left in the time to make a section
                num_students_with_each_time[most_constraining_time_index] = UNUSABLE_VALUE
                continue

            if max_sections_per_time[most_constraining_time_index] <= 0:
                # No more rooms available at this time, probably filled up in earlier iterations
                num_students_with_each_time[most_constraining_time_index] = UNUSABLE_VALUE
                continue

            # Time has enough students, but still need to see if a mod can be assigned
            for mod_index in range(num_mods):
                mod_var_for_time = mod_time_variables[mod_index][most_constraining_time_index]
                mod_has_time_green = (mod_var_for_time is not None) and (mod_var_for_time.is_preferred_time)
                mod_has_been_fully_assigned = (max_sections_per_mod[mod_index] <= 0)
                mod_previously_assigned_to_time = (most_constraining_time_index in mod_assigned_times[mod_index])

                if mod_has_time_green and (not mod_has_been_fully_assigned) and \
                    (not mod_previously_assigned_to_time):
                    valid_greedy_section_time_found = True
                    break

            if not valid_greedy_section_time_found:
                # No moderator could be assigned to this time
                num_students_with_each_time[most_constraining_time_index] = UNUSABLE_VALUE

        # We have found a time index which can be used to greedy assign a section
        # Pick the first {config.min_students_per_section} who gave the fewest valid time preferences
        # Likewise pick the first moderator who works with the time and gave the fewest valid time preferences
        greedy_student_indices = getMostConstrainingIndices(most_constraining_time_index, student_time_variables,
                                                            max_sections_per_student, config.min_students_per_section,
                                                            defaultdict(set))
        greedy_mod_index = getMostConstrainingIndices(most_constraining_time_index, mod_time_variables,
                                                      max_sections_per_mod, 1, mod_assigned_times)[0]

        # Add this greedy section to the greedy assignment and account for the mod and students having been assigned
        greedy_assignment.append((most_constraining_time_index, greedy_mod_index, greedy_student_indices))
        max_sections_per_time[most_constraining_time_index] -= 1
        max_sections_per_mod[greedy_mod_index] -= 1
        mod_assigned_times[greedy_mod_index].add(most_constraining_time_index)

        for greedy_student_index in greedy_student_indices:
            max_sections_per_student[greedy_student_index] -= 1
            # Need to subtract this student from the other green times they have too
            for time_index in range(num_section_times):
                student_time_var = student_time_variables[greedy_student_index][time_index]
                if (student_time_var is not None) and (student_time_var.is_preferred_time):
                    num_students_with_each_time[time_index] -= 1

    return greedy_assignment
