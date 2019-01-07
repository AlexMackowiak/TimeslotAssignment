DOODLE_PREFERRED_TIME = 'OK'
DOODLE_NOT_PREFERRED_TIME = '(OK)'
DOODLE_IMPOSSIBLE_TIME = ''

class PersonAssignedToTimeVariableWrapper:
    def __init__(self, net_id, time_index, is_preferred_time, linear_programming_var):
        """
            Args:
                net_id: String for the netID of the student or moderator this LP variable represents
                time_index: Integer for the time slot this LP variable represents
                is_preferred_time: True if this person marked this time as preferred
                linear_programming_var: The OR-Tools IntVar object being wrapped with extra data
        """
        self.net_id = net_id
        self.time_index = time_index
        self.is_preferred_time = is_preferred_time
        self.variable = linear_programming_var

    def isTimeAssignedToPerson(self):
        """
            The output of this function should only be used after the linear programming solver
                has been run

            Returns:
                True if this person was assigned this time by the LP solver, false otherwise
        """
        return (self.variable.solution_value() != 0)

def setupLinearProgrammingVariables(lp_solver, net_ids, time_preferences):
    """
        Initializes and wraps all the LP variables used by the LP solver
        A person paired with one section time is considered a variable, this is done for every net_id and section time
            the person declared as non-impossible
        Each variable may only have either 0 or 1 as its value, a solution value of 1 indicates that person was assigned
            that section time

        Args:
            lp_solver: The pywraplp.Solver object which will solve the linear programming assignment problem
            net_ids: List of Strings for each person's net ID
            time_preferences: List where each entry is all the time preferences for one person

        Returns:
            Two lists that represent the same LP variables, but a different order of iteration (row vs. column order)
            variables_for_each_person: List with all person/time LP vars for a single person at an index
            variables_for_each_time: List with all person/time LP vars for a single section time at an index
    """
    num_people = len(net_ids)
    num_section_times = len(time_preferences[0])

    variables_for_each_person = [[] for _ in range(num_people)]
    variables_for_each_time = [[] for _ in range(num_section_times)]

    for person_index in range(num_people):
        for time_index in range(num_section_times):
            preference_for_time = time_preferences[person_index][time_index]

            if preference_for_time != DOODLE_IMPOSSIBLE_TIME:
                is_preferred_time = (preference_for_time == DOODLE_PREFERRED_TIME)
                linear_programming_var = lp_solver.IntVar(0, 1, ('person_' + str(person_index) + ':time_' + str(time_index)))
                variable_wrapper = PersonAssignedToTimeVariableWrapper(net_ids[person_index], time_index,
                                                                       is_preferred_time, linear_programming_var)

                variables_for_each_person[person_index].append(variable_wrapper)
                variables_for_each_time[time_index].append(variable_wrapper)

    return variables_for_each_person, variables_for_each_time

def addSectionsPerPersonConstraint(lp_solver, variables_for_each_person, max_sections_per_person):
    """
        Adds the constraint to the LP solver that no person has more than their maximum number of sections
            For students this should be 1 section
            For moderators this should be the maximum sections requested

        This is currently set up so each person has exactly their maximum sections so that the numbers can be
            messed with easier when configuring (TODO: make this a config option)
        Mathematically, this constraint is expressed as
            (the sum of all person/time assignment variables for a person) = (max sections for that person)

        Args:
            lp_solver: The pywraplp.Solver object which will solve the linear programming assignment problem
            variables_for_each_person: List where each entry is a List of type PersonAssignedToTimeVariableWrapper
                                        which represents all person/time variables for a single person
            max_sections_per_person: List of Integers, max_sections_per_person[i] is the maximum sections the ith
                                        person can have
    """
    for (times_that_work_for_person, max_sections) in zip(variables_for_each_person, max_sections_per_person):
        section_times_per_person = lp_solver.Constraint(float(max_sections), float(max_sections))

        for person_section_time_var_wrapper in times_that_work_for_person:
            section_times_per_person.SetCoefficient(person_section_time_var_wrapper.variable, 1)

def addPeoplePerSectionTimeConstraint(lp_solver, variables_for_each_time, min_per_section_time, max_per_section_time):
    """
        Adds the constraint to the LP solver that every section time has between a minimum and maximum of people
            For students this should be between 5 and 6 times the number of moderators assigned to a section time
            For moderators this should be between 1 and the number of rooms available
        Mathematically this constraint is expressed as
            min_for_a_time <= (the sum of all person/time variables for that section time) <= max_for_a_time

        Args:
            lp_solver: The pywraplp.Solver object which will solve the linear programming assignment problem
            variables_for_each_time: List where each entry is a List of type PersonAssignedToTimeVariableWrapper
                                        which represents all person/time variables for a single section time
    """
    for (people_that_can_take_time, min_for_time, max_for_time) in \
            zip(variables_for_each_time, min_per_section_time, max_per_section_time):
        min_max_people_for_section_time = lp_solver.Constraint(float(min_for_time), float(max_for_time))

        for person_section_time_var_wrapper in people_that_can_take_time:
            min_max_people_for_section_time.SetCoefficient(person_section_time_var_wrapper.variable, 1)

def addNotPreferredTimeFunction(lp_solver, variables_for_each_person):
    """
        Adds the function to minimize to the LP solver, mathematically this function is specified as
            minimize f where f = (the sum of all person/time assignment variables where the time is not preferred)
        This means the LP solver can pick preferred times for free, but choosing not preferred times incurs a cost

        Args:
            lp_solver: The pywraplp.Solver object which will solve the linear programming assignment problem
            variables_for_each_persono: List where each entry is a List of type PersonAssignedToTimeVariableWrapper
                                            which represents all person/time variables for a single person
    """
    lp_objective_function = lp_solver.Objective()
    lp_objective_function.SetMinimization()

    for times_that_work_for_person in variables_for_each_person:
        for person_section_time_var_wrapper in times_that_work_for_person:
            is_preferred_time = (person_section_time_var_wrapper.is_preferred_time)

            if not is_preferred_time:
                lp_objective_function.SetCoefficient(person_section_time_var_wrapper.variable, 1)
