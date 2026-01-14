import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os

def generate_verification_code(length: int = 6) -> str:
    """Generate a random verification code"""
    return ''.join(random.choices(string.digits, k=length))

def generate_reset_token(length: int = 32) -> str:
    """Generate a random password reset token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_verification_email(to_email: str, code: str) -> bool:
    """
    Send verification email with code.
    Note: For production, configure SMTP settings.
    For development, this will print the code to console.
    """
    try:
        print(f"Sending verification email to {to_email} with code {code}")
        # For development - just print to console
        # print(f"\n{'='*50}")
        # print(f"VERIFICATION EMAIL")
        # print(f"To: {to_email}")
        # print(f"Verification Code: {code}")
        # print(f"{'='*50}\n")
        
        # For production, uncomment and configure SMTP:
        smtp_server = os.getenv("SMTP_SERVER", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = "Verify Your Account - CIT Capstone Repository"
        
        body = f"""
        Hello,
        
        Your verification code is: {code}
        
        This code will expire in 15 minutes.
        
        Best regards,
        CIT Capstone Repository Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_password_reset_email(to_email: str, token: str, base_url: str = "http://localhost:5173") -> bool:
    """
    Send password reset email with link.
    Note: For production, configure SMTP settings.
    For development, this will print the link to console.
    """
    try:
        reset_link = f"{base_url}/student/reset-password?token={token}"
        
        # For development - just print to console
        # print(f"\n{'='*50}")
        # print(f"PASSWORD RESET EMAIL")
        # print(f"To: {to_email}")
        # print(f"Reset Link: {reset_link}")
        # print(f"{'='*50}\n")
        
        # For production, uncomment and configure SMTP (similar to above)
        smtp_server = os.getenv("SMTP_SERVER", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = "Password Reset - CIT Capstone Repository"
        body = f"""
        Hello,
        
        You can reset your password by clicking the link below:
        {reset_link}
        This link will expire in 1 hour.

        Best regards,
        CIT Capstone Repository Team
        """
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False

def get_verification_expiry() -> datetime:
    """Get expiry time for verification codes (15 minutes from now)"""
    return datetime.utcnow() + timedelta(minutes=15)

def get_reset_token_expiry() -> datetime:
    """Get expiry time for password reset tokens (1 hour from now)"""
    return datetime.utcnow() + timedelta(hours=1)
