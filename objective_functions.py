import config
import random
# You really should use a first come first serve objective function (try not to lie to students)

# Simplest function for calculation speed, inadvisable to use this however from a moderator perspective
def everyone_equal_weight(num_mods, num_students, index, is_mod_coefficient):
    return 1

# Still a simple function for calculation, but ensures every mod assignment is prioritized over all student assignments
def moderators_equal_but_higher_priority(num_mods, num_students, index, is_mod_coefficient):
    if is_mod_coefficient:
        return num_students + 1
    return 1

# Simple first come first serve, with mods having slightly higher priority than students, you should probably default to this
def first_come_first_serve(num_mods, num_students, index, is_mod_coefficient):
    if is_mod_coefficient:
        return (num_mods - index) + num_students
    return num_students - index

# Most complicated for computation, first come first serve but every mod assignment is prioritized over all student assignments
def first_come_first_serve_mods_high_priority(num_mods, num_students, index, is_mod_coefficient):
    if is_mod_coefficient:
        return ((num_students * num_students) / 2) + (num_mods - index)
    return num_students - index

# Below is the code that actually makes use of the objective functions defined above
def addFunctionToMinimize(model, mod_time_variables, student_time_variables, max_total_sections):
    """
        Adds the objective function to minimize to the model
        The objective function that gets added is specified in the config file.

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod
            student_time_variables: 2D List of PersonTimeVariableWrapper,
                                        if [student_index][time_index] is None then
                                        that time is impossible for that student
            max_total_sections: Integer for the maximum number of sections possible if every
                                 moderator is assigned to their maximum number of sections
    """
    num_mods = len(mod_time_variables)
    num_students = len(student_time_variables)
    num_section_times = len(mod_time_variables[0])
    not_preferred_variables = []

    # Give impossible times an extremely high cost to discourage the use of these times
    impossible_variables = []
    IMPOSSIBLE_VARIABLE_PENALTY = 10000

    # Give not preferred times a multiplier to make them have a higher priority than contiguous sections
    NOT_PREFERRED_PRIORITY_MULTIPLIER = 10

    # Give making more sections a high enough priority to outweigh shifting students around
    MAX_SECTIONS_PRIORITY_MULTIPLIER = (config.max_students_per_section + 1) * NOT_PREFERRED_PRIORITY_MULTIPLIER

    # Minimize the sum of not preferred times
    for time_index in range(num_section_times):
        for mod_index in range(num_mods):
            mod_time_var_wrapper = mod_time_variables[mod_index][time_index]
            if mod_time_var_wrapper is not None:
                if mod_time_var_wrapper.is_impossible_time:
                    # Penalize the use of this impossible time heavily
                    impossible_variables.append(IMPOSSIBLE_VARIABLE_PENALTY * mod_time_var_wrapper.variable)
                elif not mod_time_var_wrapper.is_preferred_time:
                    # Penalize this not preferred time so that preferred times are picked with higher priority
                    coefficient = config.objective_function(num_mods, num_students, mod_index, True)
                    coefficient *= NOT_PREFERRED_PRIORITY_MULTIPLIER
                    not_preferred_variables.append(coefficient * mod_time_var_wrapper.variable)
                else:
                    # Do nothing on preferred times, they may be used freely at no cost
                    pass

        for student_index in range(num_students):
            student_time_var_wrapper = student_time_variables[student_index][time_index]
            if student_time_var_wrapper is not None:
                if student_time_var_wrapper.is_impossible_time:
                    # Penalize the use of this impossible time heavily
                    impossible_variables.append(IMPOSSIBLE_VARIABLE_PENALTY * student_time_var_wrapper.variable)
                elif not student_time_var_wrapper.is_preferred_time:
                    # Penalize this not preferred time so that preferred times are picked with higher priority
                    coefficient = config.objective_function(num_mods, num_students, student_index, False)
                    coefficient *= NOT_PREFERRED_PRIORITY_MULTIPLIER
                    not_preferred_variables.append(coefficient * student_time_var_wrapper.variable)
                else:
                    # Do nothing on preferred times, they may be used freely at no cost
                    pass

    # Maximize the amount of contiguous section times when the option is enabled
    # If the option is not enabled this will be an empty list
    contiguous_section_variables = []
    should_consider_contiguous_sections = config.prefer_contiguous_sections_preferred_times_only or \
                                          config.prefer_contiguous_sections_all_possible
    if should_consider_contiguous_sections:
        contiguous_section_variables = create_contiguous_section_decision_variables(model, mod_time_variables)

    # Maximize the amount of sections created when the option is enabled
    # If the option is not enabled this will be an empty list
    mod_time_variables_to_maximize = []
    maximum_total_sections_objective_offset = 0
    if config.maximize_number_of_sections and config.assign_exact_max_sections:
        print('WARNING: config.assign_exact_max_sections must be disabled to use config.maximize_number_of_sections')
        print('WARNING: If these are both enabled it would add add extraneous computation time')
    elif config.maximize_number_of_sections:
        # Only config.maximize_number_of_sections is enabled, factor that into the objective function
        # Ensure objective function has minimum possible value of 0
        maximum_total_sections_objective_offset = MAX_SECTIONS_PRIORITY_MULTIPLIER * max_total_sections
        # Maximize the number of sections by adding negative weight to each moderator assignment that exists
        for mod_index in range(num_mods):
            for time_index in range(num_section_times):
                mod_time_var_wrapper = mod_time_variables[mod_index][time_index]
                if mod_time_var_wrapper is not None:
                    mod_time_variables_to_maximize.append(MAX_SECTIONS_PRIORITY_MULTIPLIER * mod_time_var_wrapper.variable)

    # Finally, minimize all of the above things
    model.Minimize(sum(not_preferred_variables) + sum(impossible_variables) - sum(contiguous_section_variables) +
                   len(contiguous_section_variables) - sum(mod_time_variables_to_maximize) +
                   maximum_total_sections_objective_offset)

def create_contiguous_section_decision_variables(model, mod_time_variables):
    """
        Creates and returns the decision variables for assigning moderators to teach contiguous sections
         according to the specified values in the config file. These decision variables should then be used
         in an objective function for the system such that assigning contiguous sections is more optimal.

        Args:
            model: The CpModel object that represents the constraints of the problem
            mod_time_variables: 2D List of PersonTimeVariableWrapper, if [mod_index][time_index]
                                    is None then that time is impossible for that mod

        Returns:
            A List of CpModel.IntVar such that each variable is assigned value 1 iff a moderator is
                assigned to teach both the adjacent sections that the variable represents
    """
    random.seed("Creatively Titled Contiguous Time Selection Seed") # Ensure deterministic behavior
    contiguous_section_variables = []
    num_contiguous_variables = 0
    num_mods = len(mod_time_variables)
    num_section_times = len(mod_time_variables[0])

    for mod_index in range(num_mods):
        for section_index in range(num_section_times - 1):
            current_mod_time_var_wrapper = mod_time_variables[mod_index][section_index]
            next_mod_time_var_wrapper = mod_time_variables[mod_index][section_index + 1]

            # Determine if the current and next times are contiguous given the specification in the config file
            if current_mod_time_var_wrapper is None or next_mod_time_var_wrapper is None:
                continue

            # Verify current and next times take place on the same weekday
            if current_mod_time_var_wrapper.day_of_week != next_mod_time_var_wrapper.day_of_week:
                continue

            if config.prefer_contiguous_sections_all_possible:
                # Need times to not be impossible (both yellow and green are allowed as contiguous)
                if current_mod_time_var_wrapper.is_impossible_time or next_mod_time_var_wrapper.is_impossible_time:
                    continue
            elif config.prefer_contiguous_sections_preferred_times_only:
                # Need times to be preferred (just green times are allowed as contiguous)
                if (not current_mod_time_var_wrapper.is_preferred_time) or (not next_mod_time_var_wrapper.is_preferred_time):
                    continue

            # Don't consider these contiguous times if random chance has selected to not use them (reduce computation time)
            if random.random() >= config.contiguous_sections_percentage:
                continue

            # We have two adjacent times that need to be prioritized in assignment
            left_section_value = current_mod_time_var_wrapper.variable
            right_section_value = next_mod_time_var_wrapper.variable
            # Create a new variable to represent the sum of assigning the moderator to these two sections
            unique_variable_name = 'contiguous_var_' + str(num_contiguous_variables)
            left_and_right_section_sum = model.NewIntVar(0, 2, unique_variable_name)
            model.Add(left_and_right_section_sum == left_section_value + right_section_value)

            # Create a decision variable to represent that the moderator was assigned these contiguous sections
            # contiguous_decision_variable = (left_and_right_section_sum // 2)
            unique_variable_name = 'contiguous_var_' + str(num_contiguous_variables + 1)
            contiguous_decision_variable = model.NewIntVar(0, 1, unique_variable_name)
            model.AddDivisionEquality(contiguous_decision_variable, left_and_right_section_sum, 2)

            # Factor this decision variable into the objective function to make using it more optimal than not
            contiguous_section_variables.append(contiguous_decision_variable)
            num_contiguous_variables += 2

    print('Num contiguous variables:', num_contiguous_variables)
    return contiguous_section_variables
