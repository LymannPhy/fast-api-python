import re
import smtplib
import random
import string
import os
from jinja2 import Environment, FileSystemLoader
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from core.config import get_settings

settings = get_settings()

def is_valid_email(email: str) -> bool:
    """
    Validate the email address format using a regular expression.
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def generate_verification_code(length: int = 6) -> str:
    """
    Generate a random verification code of specified length.
    """
    return ''.join(random.choices(string.digits, k=length))

def generate_code_expiration(minutes: int = 15) -> datetime:
    """
    Generate the expiration time for a verification code.
    """
    return datetime.utcnow() + timedelta(minutes=minutes)


def send_verification_email(email: str, username: str, verification_code: str):
    if not is_valid_email(email):
        print(f"Invalid email address: {email}")
        return

    # Path to the templates directory
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    print(f"Template directory: {template_dir}")  # Debug statement

    # Check if the directory exists
    if not os.path.exists(template_dir):
        print(f"Template directory does not exist: {template_dir}")
        return

    # Initialize the Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader(template_dir))

    # Attempt to load the template
    try:
        template = env.get_template('verification_email.html')
        print("Template loaded successfully!")
    except Exception as e:
        print(f"Error loading template: {e}")
        return

    # Render the HTML content with the provided username and verification code
    html_content = template.render(username=username, verification_code=verification_code)
    subject = "Your Verification Code"
    _send_email(email, subject, html_content, is_html=True)


def send_password_reset_email(email: str, username: str, reset_code: str):
    if not is_valid_email(email):
        print(f"Invalid email address: {email}")
        return

    # Path to the templates directory
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')

    # Check if the directory exists
    if not os.path.exists(template_dir):
        print(f"Template directory does not exist: {template_dir}")
        return

    # Initialize the Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader(template_dir))

    # Attempt to load the template
    try:
        template = env.get_template('password_reset_email.html')  # Update to the correct template name
    except Exception as e:
        print(f"Error loading template: {e}")
        return

    # Render the HTML content with the provided username and reset code
    html_content = template.render(username=username, verification_code=reset_code)
    subject = "Reset Your Password"
    _send_email(email, subject, html_content, is_html=True)



def _send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    """
    Helper function to send an email using SMTP with an option for HTML content.
    """
    try:
        # Email sender credentials
        sender_email = settings.EMAIL_SENDER
        sender_password = settings.EMAIL_PASSWORD

        # SMTP server configuration
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach the email body (HTML or plain text)
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Set up the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable security
            server.login(sender_email, sender_password)  # Login
            server.sendmail(sender_email, to_email, msg.as_string())  # Send email

        print(f"Verification email sent to {to_email}")

    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")




