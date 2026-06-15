# backend/app/tools/communication/send_email.py
from langchain_core.tools import tool
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)


@tool
def send_email_tool(
    to: str,
    subject: str,
    content: str,
    html: bool = False
) -> Dict[str, Any]:
    """
    Gửi email thông báo hoặc báo cáo
    """
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not all([smtp_user, smtp_password]):
            return {
                "status": "error",
                "message": "Chưa cấu hình SMTP trong file .env"
            }

        msg = MIMEMultipart("alternative")
        msg["From"] = smtp_user
        msg["To"] = to
        msg["Subject"] = subject

        if html:
            msg.attach(MIMEText(content, "html"))
        else:
            msg.attach(MIMEText(content, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to, msg.as_string())

        logger.info(f"✅ Email sent to {to}")
        return {
            "status": "success",
            "message": f"📧 Email đã được gửi thành công đến {to}",
            "sent_to": to
        }

    except Exception as e:
        logger.error(f"Send Email Tool Error: {e}")
        return {
            "status": "error",
            "message": f"Lỗi khi gửi email: {str(e)}"
        }