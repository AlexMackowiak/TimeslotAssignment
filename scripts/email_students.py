import csv
import smtplib
from getpass import getpass, GetPassWarning

# Need a mapping of moderator net IDs to actual names
mod_net_id_to_name_csv_path = 'sp20_full_data/sp20_mod_net_ids_to_names.csv'
mod_name_to_net_id_dict = {}
with open(mod_net_id_to_name_csv_path, 'r') as mapping_file:
    for entry in csv.reader(mapping_file):
        net_id = entry[0]
        name = entry[1]
        mod_name_to_net_id_dict[name] = net_id

# Get the password for the admin email address
from_address = 'cs126sp20@gmail.com'
password = None
if password is None:
    try:
        password = getpass(from_address + ' password: ')
    except GetPassWarning:
        print('Could not securely prompt for password')
        print('Please enter the password into the program itself and remove it afterwards')
        exit(-1)

# Connect to the email server
server = smtplib.SMTP('smtp.gmail.com:587')
server.ehlo()
server.starttls()
server.login(from_address, password)

# Email students one at a time from the previously generated section assignment csv
with open('sp20_full_data/final_section_assignments_sp20.csv', 'r') as student_assignment_file:
    assignments = csv.reader(student_assignment_file)
    for assignment in assignments:
        net_id = assignment[0]
        time = assignment[1]
        moderator = assignment[2]
        room = assignment[3]

        mod_net_id = mod_name_to_net_id_dict[moderator]

        student_address = net_id + '@illinois.edu'
        mod_address = mod_net_id + '@illinois.edu'
        message = "\r\n".join(["From: " + from_address,
                               "To: " + student_address,
                               "Subject: CS 126 Code Review Assignment",
                               "",
                               "Hello,",
                               "",
                               "Your section assignment is every week {} in room {}, and {} ({}) is your code moderator. ".format(time, room, moderator, mod_address),
                               "",
                               "If you have an issue with the time assigned to you please send an email to this account ({}) explaining your circumstances.".format(from_address),
                               "Valid reasons for needing to be reassigned to a different section include having a job that conflicts, religious accommodations, or other similar reasons.",
                               "Not liking your section time, or having RSO events during your section time are not valid reasons for needing to be reassigned."
                               "\r\n",
                               "Please note that while it is likely this will be your code review time for the whole semester, sections are still shuffling around.",
                               "You may potentially be moved to a different section depending on students adding/dropping the class or other factors."
                               "\r\n",
                               "Have a great first code review, and a productive semester!"
                               ])

        print('Emailing: ' + net_id);
        server.sendmail(from_address, student_address, message)

server.quit()
