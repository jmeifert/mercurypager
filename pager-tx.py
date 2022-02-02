import smtplib
from email.mime.text import MIMEText
from orion import FormatUtils
# SMTP login information
SMTP_ADDR = ""
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SMTP_PASSWORD = ""
PAGER_SERVER_ADDRESS = ""


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
sm = SMTP(SMTP_ADDR, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT)

print("Mercury Pager Transmitter")
while(True):
    while(True):
        print("Enter address to page (xxx.xxx.xxx.xxx):")
        addr = input(">")
        if(FormatUtils.isValidOctets(addr)):
            break
        else:
            print("Address " + addr + " is invalid.")
    print("Enter body text (ASCII):")
    body = input(">")
    sm.send(PAGER_SERVER_ADDRESS, addr, body)
    print("Page sent. Press CTRL-C to exit.\n")
