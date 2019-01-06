from moderator_assignments import assignModerators

if __name__ == "__main__":
    mod_doodle_poll_csv_path = 'moderator_preferences_original.csv'
    num_mods_per_section_time = assignModerators(mod_doodle_poll_csv_path)
    print(num_mods_per_section_time)
