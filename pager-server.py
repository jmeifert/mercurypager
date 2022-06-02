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
    config_lines = []
    for i in f.readlines():
        if(i[0] != "#" and i[0] != " "):
            config_lines.append(i.split("=")[1].strip("\n"))

IMAP_ADDR = config_lines[0]
IMAP_SERVER = config_lines[1]
IMAP_PORT = int(config_lines[2])
IMAP_PASSWORD = config_lines[3]
SMTP_ADDR = config_lines[4]
SMTP_SERVER = config_lines[5]
SMTP_PORT = int(config_lines[6])
SMTP_PASSWORD = config_lines[7]
SOURCE_ADDRESS = config_lines[8]
PAGE_COOLDOWN = int(config_lines[9])
MAX_PAGE_LENGTH = int(config_lines[10])
OUTGOING_MESSAGE_SUBJECT = config_lines[11]
OUTGOING_MESSAGE_HEADER = config_lines[12] + "\n"

################################################################################ LOGGING
def get_date_and_time(): # Long date and time for logging
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
LOG_PATH = "mercury.log"
#
# How the log identifies which module is logging.
LOG_PREFIX = "(Mercury)"

# Initialize log file if needed
if(LOG_TO_FILE):
    try:
        os.remove(LOG_PATH)
    except:
        pass
    with open(LOG_PATH, "w") as f:
        f.write(get_date_and_time() + " [INFO] " + LOG_PREFIX + " Logging initialized.\n")

def log(level: int, data: str):
    if(level >= LOG_LEVEL):
        output = get_date_and_time()
        if(level == 0):
            output += " [INFO] "
        elif(level == 1):
            output += " [WARN] "
        else:
            output += " [ERR!] "
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
                message_subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(message_subject, bytes):
                    message_subject = message_subject.decode(encoding)
                
                message_from, encoding = decode_header(msg.get("From"))[0]
                if isinstance(message_from, bytes):
                    message_from = message_from.decode(encoding)
                if("<" in message_from):
                    message_from = message_from.split("<")[1].strip(">")
            if msg.is_multipart():
                for part in msg.walk():       
                    if part.get_content_type() == "text/plain":
                        message_body = part.get_payload(decode=True).decode()
            
            else:
                if msg.get_content_type() == "text/plain":
                    message_body = msg.get_payload(decode=True).decode("ascii", "ignore")
        if(remove):
            self.imap.store(str(index), '+FLAGS', '\\Deleted')
            self.imap.expunge()
        
        # Close connection
        self.imap.close()
        self.imap.logout()
        return message_from, message_subject, message_body
    
    def read_last(self, remove=False):
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
log(0, "----- Mercury Pager Server -----")
log(0, "- Homepage: https://github.com/jmeifert/mercurypager")
log(0, "- Updates: https://github.com/jmeifert/mercurypager/releases")
im = IMAP(IMAP_ADDR, IMAP_PASSWORD, IMAP_SERVER, IMAP_PORT)
sm = SMTP(SMTP_ADDR, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT)
ni = NetworkInterface(SOURCE_ADDRESS, 65535)
while(True):
    #try:
    if(im.getMessageCount() > 0):
        # Fetch mail
        mail_from, mail_subject, mail_body = im.read_last(remove=True)
        log(0, "Message received from " + mail_from + ".")
        # Assemble packet
        if(FormatUtils.is_valid_address(mail_subject)):
            dest = mail_subject
        else:
            dest = '255.255.255.255'
        page_body = mail_from + ":\n" + mail_body 
        sp = ni.make_packet(FormatUtils.trim_bytes(page_body.encode("ascii", "ignore"), MAX_PAGE_LENGTH), dest, 65535)
        # Send packet
        ni.send_packet(sp)
        # Notify sender that packet was sent
        log(0, "Sent page:\n" + page_body + "\nto address " + sp.get_dest() + ".")
        if(mail_from != IMAP_ADDR and mail_from != SMTP_ADDR): # don't send messages to self
            sm.send(mail_from, OUTGOING_MESSAGE_SUBJECT, (OUTGOING_MESSAGE_HEADER + "The following page...\n" + page_body + "\n...to address " + sp.get_dest() + " was successfully sent on " + get_date_and_time() + "."))
        # Cool down
        sleep(PAGE_COOLDOWN)
        log(0, "Listening.")
    else:
        sleep(3) # mail check cooldown

    #except Exception as e:
    #    log(2, "Unexpected error: " + str(e) + ". Restarting after cooldown.")
    #    sleep(PAGE_COOLDOWN)
