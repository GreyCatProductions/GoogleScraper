import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

# Example usage
#recipient_emails = ["email1@gmail.com", "email2@gmail.com"]
#message_content = "My message"
#title = "My title"
def send_email(recipient_emails, message_content, title):
    sender_email = "workstationemailsender@gmail.com"
    sender_password = "vzri xnsf jkvk zajb"

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = ", ".join(recipient_emails)
    message['Subject'] = "*Message from Scraper* " + title

    message.attach(MIMEText(message_content + "\n\n ~beep bop I am a bot~", 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()

        logging.info(f"Email sent successfully to {recipient_emails}")

    except Exception as e:
        logging.error(f"Failed to send email. Error: {str(e)}")



