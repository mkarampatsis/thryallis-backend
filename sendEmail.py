import sys
from smtplib import SMTP as SMTP # this invokes the secure SMTP protocol (port 465, uses SSL)
from email.mime.text import MIMEText

from datetime import datetime
from time import sleep
from src.config import (
  EMAIL_USERNAME,
  EMAIL_PASSWORD,
  EMAIL_SMTPSERVER,
  EMAIL_DESTINATION
)


SMTPSERVER = EMAIL_SMTPSERVER
SENDER = 'no-reply@thryallis.ypes.gov.gr'
DESTINATION = EMAIL_DESTINATION
SUBJECT = "Message from Tryallis System"

USERNAME = EMAIL_USERNAME
PASSWORD = EMAIL_PASSWORD

users = ["Markos", "Nikos", "Giorgos"]

# typical values for text_subtype are plain, html, xml
TEXT_SUBTYPE = 'html'

message = '''
    <p>Αυτό το μήνυμα επιβεβαιώνει τη .....</p>
    <p>
        Ονοματεπώνυμο: %s<br>
    </p>

    <p>Αλλό κείμενο Για να αρχικοποιήσετε το λογαριασμό σας και να δημιουργήσετε password πατήστε <a href="https://my.central.ntua.gr/auth/forgotpasswd" target="_blank">εδώ</a>.</p>

    <p><strong>ΟΔΗΓΙΕΣ</strong>: Html Κείμενο</p> 
    
    
    <p>Veltion<br>
    Registration Team
    </p>
'''   

print ('Start of program')

for user in users:
  text = message % (user)

  try:
    #print text
    msg = MIMEText(text, TEXT_SUBTYPE, 'utf-8')
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = ", ".join(DESTINATION)

    conn = SMTP("mailgate.cosmotemail.gr", 587)
    conn.set_debuglevel(False)  # enable debug to see server responses

    conn.ehlo()
    conn.starttls()
    conn.ehlo()  # required after STARTTLS

    conn.login(USERNAME, PASSWORD)

    try:
      conn.sendmail(SENDER, DESTINATION, msg.as_string())
      print ("Message sent")
    except Exception as e:
      print("Send error:", e)
    finally:
      conn.quit()

  except Exception as e:
    sys.exit("mail failed; %s" % str(e)) # give a error message
  
  sleep(5)

print('End of program')
