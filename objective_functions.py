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
