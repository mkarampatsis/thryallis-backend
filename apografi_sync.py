from src.apografi.sync_dictionaries import sync_apografi_dictionaries
from src.apografi.sync_organizations import sync_organizations
from src.apografi.sync_organizational_units import sync_organizational_units

import sys
from smtplib import SMTP as SMTP # this invokes the secure SMTP protocol (port 465, uses SSL)
from email.mime.text import MIMEText

from datetime import datetime

SMTPSERVER = "smtp.ntua.gr"
SENDER = 'no-reply@thryallis.ypes.gov.gr'
DESTINATION = ['marka@mail.ntua.gr','marka@central.ntua.gr']

USERNAME = "jraptaki"
PASSWORD = "l1vadak1a"

message_dictionaries = '''
    <p>Ο συγχρονισμός των λεξικών ολοκληρώθηκε</p>
    <p>Ώρα που ξεκίνησε: %s</p>
    <p>Ώρα που τελειώσε: %s</p>
''' 

message_organizations = '''
    <p>Ο συγχρονισμός των φορέων ολοκληρώθηκε</p>
    <p>Ώρα που ξεκίνησε: %s</p>
    <p>Ώρα που τελειώσε: %s</p>
''' 

message_organizational_units = '''
    <p>Ο συγχρονισμός των μονάδων ολοκληρώθηκε</p>
    <p>Ώρα που ξεκίνησε: %s</p>
    <p>Ώρα που τελειώσε: %s</p>
'''

def send_email(subject, message, start_time, end_time):
  try:
    text = message %(start_time, end_time)
    msg = MIMEText(text, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SENDER
    msg['To'] = ", ".join(DESTINATION)

    conn = SMTP(SMTPSERVER, port=25)
    conn.set_debuglevel(False)
    conn.ehlo()
    conn.starttls()  # enable TLS
    # If authentication is required, uncomment and set USERNAME and PASSWORD
    conn.login(USERNAME, PASSWORD)

    try:
        conn.sendmail(SENDER, DESTINATION, msg.as_string())
        print("Message sent")
    except Exception as e:
        print("Send error:", e)
    finally:
        conn.quit()

  except Exception as e:
    sys.exit("mail failed; %s" % str(e))  # give an error message 

# Sync Dictionaries
# start_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
# sync_apografi_dictionaries()
# end_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
# send_email(
#     subject="Thryallis - Συγχρονισμός Λεξικών Απογραφής",
#     message=message_dictionaries,
#     start_time=start_time,
#     end_time=end_time
# )

# Sync Organizations
start_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
sync_organizations()
end_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
send_email(
  subject="Thryallis - Συγχρονισμός Φορέων Απογραφής",
  message=message_organizations,
  start_time=start_time,
  end_time=end_time
)

# Sync Organizational Units
start_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
sync_organizational_units()
end_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
send_email(
  subject="Thryallis - Συγχρονισμός Μονάδων Απογραφής",
  message=message_organizational_units,
  start_time=start_time,
  end_time=end_time
)