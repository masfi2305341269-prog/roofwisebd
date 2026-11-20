"""
RoofwiseBD — Secure Email Delivery Service
Sends transactional emails (e.g. password reset) via SMTP.
Supports STARTTLS (port 587, default) and implicit TLS (port 465).
Never logs raw tokens, passwords, or SMTP credentials.
"""
import logging
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Raised when an email cannot be delivered due to SMTP or network failure."""


def _build_reset_email(to_email: str, reset_link: str) -> MIMEMultipart:
    """
    Constructs a MIME multipart password reset email with both plain-text
    and HTML parts.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "RoofwiseBD — Password Reset Request"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email

    plain_text = (
        "RoofwiseBD Password Reset\n"
        "=========================\n\n"
        "We received a request to reset the password for your RoofwiseBD account.\n\n"
        "To reset your password, click the link below (valid for 15 minutes):\n\n"
        f"{reset_link}\n\n"
        "If you did not request a password reset, you can safely ignore this email. "
        "Your password will not change.\n\n"
        "This link expires in 15 minutes and can only be used once.\n\n"
        "— The RoofwiseBD Team\n"
        "Bangladesh Rooftop Solar Assessment Platform"
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RoofwiseBD Password Reset</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="600" cellpadding="0" cellspacing="0" role="presentation"
               style="background:#ffffff;border-radius:8px;overflow:hidden;
                      box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a6b3a,#2d9b5a);
                       padding:32px 40px;text-align:center;">
              <h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:700;">
                ☀️ RoofwiseBD
              </h1>
              <p style="color:#a8e6c1;margin:6px 0 0;font-size:13px;">
                Bangladesh Rooftop Solar Assessment Platform
              </p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <h2 style="color:#1a1a1a;margin:0 0 16px;font-size:20px;">
                Password Reset Request
              </h2>
              <p style="color:#555;line-height:1.6;margin:0 0 20px;">
                We received a request to reset the password for your RoofwiseBD account.
                Click the button below to choose a new password.
              </p>
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td align="center" style="padding:16px 0 24px;">
                    <a href="{reset_link}"
                       style="background:#1a6b3a;color:#ffffff;text-decoration:none;
                              padding:14px 32px;border-radius:6px;font-size:15px;
                              font-weight:600;display:inline-block;">
                      Reset My Password
                    </a>
                  </td>
                </tr>
              </table>
              <p style="color:#777;font-size:13px;line-height:1.5;margin:0 0 12px;">
                Or copy and paste this link into your browser:
              </p>
              <p style="background:#f0f8f4;border:1px solid #c8e6c9;border-radius:4px;
                        padding:10px 14px;font-size:12px;color:#2d6a4f;
                        word-break:break-all;margin:0 0 24px;">
                {reset_link}
              </p>
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                     style="background:#fff8e1;border:1px solid #ffe082;border-radius:6px;">
                <tr>
                  <td style="padding:14px 18px;">
                    <p style="color:#7a5700;font-size:13px;margin:0;line-height:1.5;">
                      ⚠️ <strong>This link expires in 15 minutes</strong> and can only
                      be used once. If you did not request a password reset, please
                      ignore this email — your account remains secure.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#f8f8f8;padding:20px 40px;border-top:1px solid #eee;
                       text-align:center;">
              <p style="color:#aaa;font-size:12px;margin:0;">
                © 2026 RoofwiseBD · AI-Powered Rooftop Solar Assessment for Bangladesh<br>
                This is an automated message. Please do not reply to this email.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    return msg


def send_email(
    to_email: str,
    subject: str,
    plain_text: str,
    html_content: Optional[str] = None,
) -> None:
    """
    Low-level SMTP send function.
    Uses STARTTLS for port 587 (default) or implicit SSL for port 465.
    Raises EmailDeliveryError on any SMTP or network failure.
    Never exposes SMTP credentials or raw tokens in log messages.
    """
    if not settings.SMTP_HOST:
        raise EmailDeliveryError("SMTP_HOST is not configured. Email delivery is disabled.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    if html_content:
        msg.attach(MIMEText(html_content, "html", "utf-8"))

    _deliver(msg, to_email)


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """
    Sends a formatted password reset email to the specified recipient.
    Raises EmailDeliveryError if delivery fails for any reason.
    The raw reset token is embedded only in `reset_link` and never logged here.
    """
    if not settings.SMTP_HOST:
        raise EmailDeliveryError("SMTP_HOST is not configured. Email delivery is disabled.")

    msg = _build_reset_email(to_email, reset_link)
    _deliver(msg, to_email)
    logger.info("Password reset email dispatched to %s", to_email)


def _build_otp_email(to_email: str, otp: str) -> MIMEMultipart:
    """
    Constructs a MIME multipart email containing a 6-digit verification OTP.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "RoofwiseBD — Your 6-Digit Email Verification Code"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email

    plain_text = (
        "RoofwiseBD Email Verification\n"
        "============================\n\n"
        "Welcome to RoofwiseBD!\n\n"
        f"Your 6-digit email verification code is: {otp}\n\n"
        "This code will expire in 10 minutes and can only be used once.\n\n"
        "If you did not create an account on RoofwiseBD, you can safely ignore this email.\n\n"
        "— The RoofwiseBD Team\n"
        "Bangladesh Rooftop Solar Assessment Platform"
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RoofwiseBD Email Verification</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="600" cellpadding="0" cellspacing="0" role="presentation"
               style="background:#ffffff;border-radius:8px;overflow:hidden;
                      box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a6b3a,#2d9b5a);
                       padding:32px 40px;text-align:center;">
              <h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:700;">
                ☀️ RoofwiseBD
              </h1>
              <p style="color:#a8e6c1;margin:6px 0 0;font-size:13px;">
                Bangladesh Rooftop Solar Assessment Platform
              </p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <h2 style="color:#1a1a1a;margin:0 0 16px;font-size:20px;">
                Verify Your Email Address
              </h2>
              <p style="color:#555;line-height:1.6;margin:0 0 24px;">
                Thank you for signing up with RoofwiseBD! Please use the 6-digit code below to verify your email address and activate your account.
              </p>
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td align="center" style="padding:16px 0 28px;">
                    <div style="background:#f0f8f4;border:2px dashed #1a6b3a;border-radius:8px;
                                display:inline-block;padding:16px 36px;letter-spacing:8px;
                                font-size:32px;font-weight:700;color:#1a6b3a;font-family:monospace;">
                      {otp}
                    </div>
                  </td>
                </tr>
              </table>
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                     style="background:#fff8e1;border:1px solid #ffe082;border-radius:6px;">
                <tr>
                  <td style="padding:14px 18px;">
                    <p style="color:#7a5700;font-size:13px;margin:0;line-height:1.5;">
                      ⚠️ <strong>This code expires in 10 minutes</strong> and can only be used once. If you did not create an account on RoofwiseBD, please disregard this email.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#f8f8f8;padding:20px 40px;border-top:1px solid #eee;
                       text-align:center;">
              <p style="color:#aaa;font-size:12px;margin:0;">
                © 2026 RoofwiseBD · AI-Powered Rooftop Solar Assessment for Bangladesh<br>
                This is an automated message. Please do not reply to this email.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    return msg


def send_verification_otp_email(to_email: str, otp: str) -> None:
    """
    Sends a formatted 6-digit OTP verification email via SMTP.
    Raises EmailDeliveryError if delivery fails or SMTP is unconfigured.
    Never exposes credentials or raw OTP in log output.
    """
    if not settings.SMTP_HOST:
        raise EmailDeliveryError("SMTP_HOST is not configured. Email delivery is disabled.")

    msg = _build_otp_email(to_email, otp)
    _deliver(msg, to_email)
    logger.info("Verification OTP email dispatched to %s", to_email)


def _deliver(msg: MIMEMultipart, to_email: str) -> None:
    """
    Internal delivery helper.
    Selects SMTP_SSL (port 465) or STARTTLS (all other ports, default 587).
    """
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD

    try:
        if smtp_port == 465:
            # Implicit SSL/TLS
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())
        else:
            # STARTTLS (port 587 or any other port)
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())
    except smtplib.SMTPAuthenticationError:
        # Log no credentials — only the category of failure
        logger.error(
            "SMTP authentication failed for host %s:%s. "
            "Check SMTP_USER and SMTP_PASSWORD environment variables.",
            smtp_host, smtp_port
        )
        raise EmailDeliveryError("Email delivery failed: SMTP authentication error.")
    except smtplib.SMTPException as exc:
        logger.error("SMTP error while sending to %s: %s", to_email, type(exc).__name__)
        raise EmailDeliveryError(f"Email delivery failed: SMTP error ({type(exc).__name__}).")
    except socket.timeout:
        logger.error("SMTP connection to %s:%s timed out.", smtp_host, smtp_port)
        raise EmailDeliveryError("Email delivery failed: SMTP connection timed out.")
    except OSError as exc:
        logger.error("Network error connecting to SMTP %s:%s: %s", smtp_host, smtp_port, type(exc).__name__)
        raise EmailDeliveryError(f"Email delivery failed: network error ({type(exc).__name__}).")
