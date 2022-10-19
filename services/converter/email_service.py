import smtplib
import os

email_user = os.environ.get("EMAIL_USER")
email_psw = os.environ.get("EMAIL_PASSWORD")


s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
s.login(email_user, email_psw)

def send_notification(filename, dst_format, receiver):
    
    print("user:", email_user)
    print("psw:", email_psw)
    message = """\
Subject: Archivo """ + filename + """ convertido satisfactoriamente a """ + dst_format + """.

La conversion de su archivo ha finalizado. Ingrese a la plataforma para descargarlo."""
    s.sendmail(email_user, receiver, message)
