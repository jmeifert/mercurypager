from datetime import datetime
import imaplib
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText
import email
from time import sleep
from adrcfs import NetworkInterface, FormatUtils
import os

################################################################ USER CONSTANTS (Read from configuration file)
with open("mercury.conf","r") as f:
    configLines = []
    for i in f.readlines():
        if(i[0] != "#" and i[0] != " "):
            configLines.append(i.split("=")[1].strip("\n"))

IMAP_ADDR = configLines[0]
IMAP_SERVER = configLines[1]
IMAP_PORT = int(configLines[2])
IMAP_PASSWORD = configLines[3]
SMTP_ADDR = configLines[4]
SMTP_SERVER = configLines[5]
SMTP_PORT = int(configLines[6])
SMTP_PASSWORD = configLines[7]
SOURCE_ADDRESS = configLines[8]
PAGE_COOLDOWN = int(configLines[9])
MAX_PAGE_LENGTH = int(configLines[10])
OUTGOING_MESSAGE_SUBJECT = configLines[11]
OUTGOING_MESSAGE_HEADER = configLines[12] + "\n"

################################################################################ LOGGING
def getDateAndTime(): # Long date and time for logging
        now = datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')

# Logging level (0: INFO, 1: WARN (recommended), 2: ERROR, 3: NONE)
LOG_LEVEL = 0
#
# Should the log output to the console?
LOG_TO_CONSOLE = True
#
# Should the log output to a log file?
LOG_TO_FILE = False
#
# Where to generate logfile if need be
LOG_PATH = "adr-cfs.log"
#
# How the log identifies which module is logging.
LOG_PREFIX = "(ADR-CFS)"

# Initialize log file if needed
if(LOG_TO_FILE):
    try:
        os.remove(LOG_PATH)
    except:
        pass
    with open(LOG_PATH, "w") as f:
        f.write(getDateAndTime() + " [  OK  ] " + LOG_PREFIX + " Logging initialized.\n")

def log(level: int, data: str):
    if(level >= LOG_LEVEL):
        output = getDateAndTime()
        if(level == 0):
            output += " [  OK  ] "
        elif(level == 1):
            output += " [ WARN ] "
        else:
            output += " [ ERR. ] "
        output += LOG_PREFIX + " "
        output += data
        if(LOG_TO_FILE):
            with open(LOG_PATH, "a") as f:
                f.write(output + "\n")
        if(LOG_TO_CONSOLE):
            print(output)

################################################################################ IMAP Tools
class IMAP:
    def __init__(self, useremail, password, server, port):
        self.useremail = useremail
        self.password = password
        self.server = server
        self.port = port

    def getMessageCount(self):
        self.imap = imaplib.IMAP4_SSL(self.server, self.port)
        self.imap.login(self.useremail, self.password)

        status, messages = self.imap.select("INBOX")

        self.imap.close()
        self.imap.logout()
        return int(messages[0])

    def read(self, index, remove=False):
        # Open connection
        self.imap = imaplib.IMAP4_SSL(self.server, self.port)
        self.imap.login(self.useremail, self.password)
        self.imap.select("INBOX")
        # Read the message
        res, msg = self.imap.fetch(str(index), "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])
                Subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(Subject, bytes):
                    Subject = Subject.decode(encoding)
                
                From, encoding = decode_header(msg.get("From"))[0]
                if isinstance(From, bytes):
                    From = From.decode(encoding)
                if("<" in From):
                    From = From.split("<")[1].strip(">")
            if msg.is_multipart():
                for part in msg.walk():       
                    if part.get_content_type() == "text/plain":
                        Body = part.get_payload(decode=True).decode()
            
            else:
                if msg.get_content_type() == "text/plain":
                    Body = msg.get_payload(decode=True).decode("ascii", "ignore")
        if(remove):
            self.imap.store(str(index), '+FLAGS', '\\Deleted')
            self.imap.expunge()
        
        # Close connection
        self.imap.close()
        self.imap.logout()
        return From, Subject, Body
    
    def readLast(self, remove=False):
        lm = self.getMessageCount()
        return self.read(lm, remove)

################################################################################ SMTP Tools
class SMTP:
    def __init__(self, useremail, password, server, port):
        self.useremail = useremail
        self.password = password
        self.server = server
        self.port = port

    def send(self, recipient, subject, message):
        self.smtp = smtplib.SMTP(self.server, self.port)
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.login(self.useremail, self.password)

        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = self.useremail
        msg['To'] = recipient
        self.smtp.sendmail(self.useremail, recipient, msg.as_string())

        self.smtp.quit()

################################################################################ Main Loop
log(0, "Welcome to Mercury Pager Server")
im = IMAP(IMAP_ADDR, IMAP_PASSWORD, IMAP_SERVER, IMAP_PORT)
sm = SMTP(SMTP_ADDR, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT)
ni = NetworkInterface(SOURCE_ADDRESS, 65535)
while(True):
    try:
        if(im.getMessageCount() > 0):
            # Fetch mail
            From, Subject, Body = im.readLast(remove=True)
            log(0, "Message received from " + From + ".")
            # Assemble packet
            if(FormatUtils.isValidAddress(Subject)):
                dest = Subject
            else:
                dest = "255.255.255.255"
            sp = ni.makePacket(FormatUtils.trimBytes(Body.encode("ascii", "ignore"), MAX_PAGE_LENGTH), dest, 65535)
            # Send packet
            ni.sendPacket(sp)
            # Notify sender that packet was sent
            log(0, "Sent page:\n" + Body + "\nto address " + sp.getDest() + ".")
            if(From != IMAP_ADDR and From != SMTP_ADDR): # don't send messages to self
                sm.send(From, OUTGOING_MESSAGE_SUBJECT, (OUTGOING_MESSAGE_HEADER + "The following page:\n" + Body + "\nto address " + sp.getDest() + " was successfully sent on " + getDateAndTime() + "."))
            # Cool down
            sleep(PAGE_COOLDOWN)

    except Exception as e:
        log(2, "Unexpected error in fetch-process-transmit loop: " + str(e) + ". Restarting after cooldown.")
        sleep(PAGE_COOLDOWN)
