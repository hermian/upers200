import os
import smtplib
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
# And imghdr to find types of our images
import config


def send_mail(contents, subject=f'{date.today()} Upers 200', filename='매매종목.csv'):
    email_from = config.email_from
    email_to = config.email_to
    email_cc = config.email_cc
    email_subject = subject
    email_contents = contents
    password = config.email_password

    msg = MIMEMultipart()
    body_part = MIMEText(email_contents)
    msg['Subject'] = email_subject
    msg['From'] = email_from
    msg['To'] = ','.join(email_to)
    msg['Cc'] = email_cc

    msg.attach(body_part)
    if os.path.exists(filename):
        with open(filename, 'rb') as fp:
            msg.attach(MIMEApplication(fp.read(), Name=filename))

    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(email_from, password)
    smtp.sendmail(email_from, email_to, msg.as_string())

    print(msg.as_string())

    smtp.quit()

if __name__ == '__main__':
    send_mail("...test ...", "TEST")
