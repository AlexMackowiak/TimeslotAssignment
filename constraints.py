import config

def addMaxSectionsPerModConstraint(model, mod_time_variables, max_sections_per_mod):
    """
        Adds the constraint that the total number of section times a mod is assigned must be
            less than or equal to their preferred maximum number of sections

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            max_sections_per_mod: List of Integer, each entry is the max sections for that mod_index
    """
    num_mods = len(mod_time_variables)
    num_section_times = len(mod_time_variables[0])

    for mod_index in range(num_mods):
        all_time_vars_for_mod = sum([mod_time_variables[mod_index][time_index].variable
                                     for time_index in range(num_section_times)
                                     if mod_time_variables[mod_index][time_index] is not None])

        if config.assign_exact_max_sections:
            model.Add(all_time_vars_for_mod == max_sections_per_mod[mod_index])
        else:
            model.Add(1 <= all_time_vars_for_mod)
            model.Add(all_time_vars_for_mod <= max_sections_per_mod[mod_index])

def addMaxSectionsPerSectionTimeConstraint(model, mod_time_variables, max_sections_per_time):
    """
        Adds the constraint that the number of moderators assigned to a section time must be
            less than or equal to the maximum sections that can happen at that time. This is
            usually bounded by the number of rooms available (3 for every time by default)

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            max_sections_per_time: List of Integer where each index represents the number of rooms
                                    available at that time index
    """
    num_mods = len(mod_time_variables)
    num_section_times = len(mod_time_variables[0])

    for time_index in range(num_section_times):
        all_mod_vars_for_time = sum([mod_time_variables[mod_index][time_index].variable
                                     for mod_index in range(num_mods)
                                     if mod_time_variables[mod_index][time_index] is not None])
        model.Add(all_mod_vars_for_time <= max_sections_per_time[time_index])

def addSectionsPerStudentConstraint(model, student_time_variables):
    """
        Adds the constraint that the number of sections assigned to a student must be exactly 1

        Args:
            model: The CpModel object that represents the constraints of the problem
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student
    """
    num_students = len(student_time_variables)
    num_section_times = len(student_time_variables[0])

    for student_index in range(num_students):
        all_student_vars_for_time = sum([student_time_variables[student_index][time_index].variable
                                         for time_index in range(num_section_times)
                                         if student_time_variables[student_index][time_index] is not None])
        model.Add(all_student_vars_for_time == 1)

def addStudentsPerSectionTimeConstraint(model, mod_time_variables, student_time_variables, max_sections_for_times):
    """
        This is where things get complicated and why linear programming cannot solve the system as a whole
        A little about constraint programming: It's an NP hard problem, so on some level it is just trying
        every possible solution

        Consider the mod and student vars in one specific section time, and call the current solution
        being tried curr_sol, this function does 3 things:
        1. If sum(mod_vars) in curr_sol = X then it forces sum(student_vars) in curr_sol to be Y or Z
            where Y or Z is an appropriate student count for the number of mods
            (i.e. 1 mod -> (5 or 6 students), 2 mods -> (10, 11, or 12 students))

        2. Bidirectional implication
           if sum(student_vars) in curr_sol is Y or Z it forces sum(mod_vars) in curr_sol to be X

        3. Adds the constraint that one of these paths must be taken, that is it will not consider
            solutions that do not match either of the above criteria

        This is repeated for every time index, and adds ~14 more variables to the system per section time

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student
            max_sections_for_times: List of Integer where each index represents the number of rooms
                                    available at that time index
    """
    num_mods = len(mod_time_variables)
    num_students = len(student_time_variables)
    num_section_times = len(mod_time_variables[0])
    num_decision_vars = 0

    for time_index in range(num_section_times):
        max_sections_for_time = max_sections_for_times[time_index]

        mods_in_time = [mod_time_variables[mod_index][time_index].variable
                            for mod_index in range(num_mods)
                            if mod_time_variables[mod_index][time_index] is not None]
        students_in_time = [student_time_variables[student_index][time_index].variable
                            for student_index in range(num_students)
                            if student_time_variables[student_index][time_index] is not None]

        if (len(mods_in_time) == 0) or (len(students_in_time) == 0):
            # This time index should never allow a section
            model.Add(sum(mods_in_time) == 0)
            model.Add(sum(students_in_time) == 0)
            continue

        # Need to create decision variables for the possible number of mods in this time beforehand
        # A decision variable can take two values: 0 or 1, where 1 indicates the "decision" was taken
        #  corresponding to whatever path of other variable constraints the decision variable represents
        num_sections_decision_vars = []
        for _ in range(max_sections_for_time + 1):
            num_sections_decision_vars.append(model.NewBoolVar('decision' + str(num_decision_vars)))
            num_decision_vars += 1

        # End goal is to create if then logic
        # If sum(mods_in_time) == 0 then sum(students_in_time) == 0
        # If sum(mods_in_time) == 1 then sum(students_in_time) == 5 or sum(students_in_time) == 6
        # Etc. the tricky bit is allowing the "or" logic in the second part
        for possible_num_sections_in_time in range(max_sections_for_time + 1):
            model.Add(sum(mods_in_time) == possible_num_sections_in_time)\
                 .OnlyEnforceIf(num_sections_decision_vars[possible_num_sections_in_time])

            possible_sum_decision_vars = []
            for possible_student_sum in range(config.min_students_per_section * possible_num_sections_in_time,
                                              (config.max_students_per_section * possible_num_sections_in_time) + 1):
                possible_sum_decision_var = model.NewBoolVar('decision' + str(num_decision_vars))
                possible_sum_decision_vars.append(possible_sum_decision_var)
                num_decision_vars += 1

                model.Add(sum(students_in_time) == possible_student_sum)\
                     .OnlyEnforceIf(possible_sum_decision_var)\
                     .OnlyEnforceIf(num_sections_decision_vars[possible_num_sections_in_time])

            # The sum of all decision vars for sum(mods_in_time) EXCEPT the current one
            #  and the decision vars for sum(students_in_time) must be 1
            # This enforces that either a different sum(mods_in_time) var is active, or the current "or" logic is
            model.Add((sum([num_sections_decision_vars[i] 
                            for i in range(max_sections_for_time + 1)
                            if i != possible_num_sections_in_time]) + \
                       sum(possible_sum_decision_vars)) == 1)

        # Ensure that exactly one of the sum(mods_in_time) decision vars is active
        model.Add(sum(num_sections_decision_vars) == 1)

    print('Num decision variables: ' + str(num_decision_vars))
