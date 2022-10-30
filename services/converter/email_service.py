import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

BASE_URL = os.environ.get("BASE_URL")
API_KEY = os.environ.get("SENDGRID_API_KEY")
EMAIL_CONVERTER = os.environ.get("EMAIL_CONVERTER")
EMAIL_USER = os.environ.get("EMAIL_USER")
STRESS_TEST = os.environ.get("STRESS_TEST", True)

if STRESS_TEST == "0":
    STRESS_TEST = False


def send_notification(email, file_id):
    from app import logger
    if STRESS_TEST:
        return

    message = Mail(
        from_email=EMAIL_CONVERTER,
        to_emails=EMAIL_USER,
        subject="Archivo convertido",
        html_content='<p>Descargar archivo: <a href="{0}api/files/{1}">aqui</a></p>'.format(
            BASE_URL, file_id
        ),
    )
    try:
        sg = SendGridAPIClient(API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        logger.error(f"Error sending email: {e}")
