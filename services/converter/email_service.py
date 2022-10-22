import smtplib
import os

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
STRESS_TEST = os.environ.get("STRESS_TEST", False)
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")

if STRESS_TEST == '0':
    STRESS_TEST = False

if not EMAIL_USER or not EMAIL_PASSWORD or not BASE_URL:
    raise ValueError(
        "Missing EMAIL_USER, EMAIL_PASSWORD or BASE_URL environment variable"
    )


s = smtplib.SMTP("smtp.gmail.com", 587)
s.starttls()
s.login(EMAIL_USER, EMAIL_PASSWORD)


def send_notification(email, file_id):
    from app import logger

    if STRESS_TEST:
        return

    url = f"{BASE_URL}/api/files/{file_id}"
    logger.info(f"Sending email to {email} with link {url}")
    s.sendmail(
        EMAIL_USER,
        "graulopezjavier@gmail.com",
        """
        Subject: Archivo convertido

        La conversion de su archivo ha finalizado. Ingrese a la plataforma para descargarlo.
        {}
        """.format(
            url
        ),
    )
