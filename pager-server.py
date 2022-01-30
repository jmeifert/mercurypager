from datetime import datetime
import imaplib
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText
import email
from time import sleep
from orion import NetworkInterface, FormatUtils

# IMAP login information
IMAP_ADDR = ""
IMAP_SERVER = "outlook.office365.com"
IMAP_PORT = 993
IMAP_PASSWORD = ""

# SMTP login information
SMTP_ADDR = ""
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SMTP_PASSWORD = ""

# Packet radio address of paging server ("xxx.xxx", default "0.0")
SOURCE_ADDRESS = "0.0"

# Page cooldown in seconds
PAGE_COOLDOWN = 10

# Whitelist for incoming pages
IMAP_WHITELIST = []

# Subject for outgoing messages
OUTGOING_MESSAGE_SUBJECT = "Mercury Pager - Page Sent."

# Header for outgoing messages
OUTGOING_MESSAGE_HEADER = "Thank you for using Mercury Pager.\n" # Requires newline unless empty.

# Utils
def getDateAndTime(): # Long date and time
        now = datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')

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

# Main loop
print("Mercury Pager Server")

im = IMAP(IMAP_ADDR, IMAP_PASSWORD, IMAP_SERVER, IMAP_PORT)
sm = SMTP(SMTP_ADDR, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT)
octs = FormatUtils.parseOctets(SOURCE_ADDRESS)
ni = NetworkInterface(octs[0], octs[1])

while(True):
    try:
        if(im.getMessageCount() > 0):
            # Fetch mail
            From, Subject, Body = im.readLast(remove=True)
            if(From in IMAP_WHITELIST):
                print(getDateAndTime() + ": Message received from " + From + ".")
                # Read address from subject
                destAddr = FormatUtils.parseOctets(Subject)
                # Assemble packet
                sp = ni.makePacket(Body.encode("ascii", "ignore"), destAddr[0], destAddr[1])
                # Send packet
                ni.sendPacket(sp)
                print(getDateAndTime() + ": Sent page:\n" + Body + "\nto address " + str(destAddr[0]) + "." + str(destAddr[1]) + ".")
                sm.send(From, OUTGOING_MESSAGE_SUBJECT, (OUTGOING_MESSAGE_HEADER + "The following page:\n" + Body + "\nto address " + str(destAddr[0]) + "." + str(destAddr[1]) + " was successfully sent on " + getDateAndTime() + "."))
                # Cool down
                sleep(PAGE_COOLDOWN)

    except Exception as e:
        print("Exception encountered: " + str(e) + ". Retrying...")
        sleep(1)
