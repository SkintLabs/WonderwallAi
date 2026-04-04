"""
MeatHead / GiLLBoT — Email Service
Sends outreach emails via SendGrid.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("meathead.email")


class EmailService:
    """Sends emails via SendGrid with tracking headers."""

    def __init__(self):
        from server.config import get_settings
        settings = get_settings()
        self.api_key = settings.sendgrid_api_key
        self.configured = bool(self.api_key)

        if self.configured:
            try:
                import sendgrid
                self.client = sendgrid.SendGridAPIClient(api_key=self.api_key)
                logger.info("EmailService initialized (SendGrid connected)")
            except ImportError:
                logger.warning("sendgrid package not installed")
                self.client = None
                self.configured = False
        else:
            self.client = None
            logger.warning("EmailService: SENDGRID_API_KEY not set")

    async def send_email(
        self,
        to_email: str,
        from_email: str,
        from_name: str,
        subject: str,
        html_body: str,
        reply_to: Optional[str] = None,
        unsubscribe_url: Optional[str] = None,
        message_id_header: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send a single email via SendGrid.
        Returns the SendGrid message ID on success, None on failure.
        """
        if not self.configured or not self.client:
            logger.warning("Email send skipped: SendGrid not configured")
            return None

        try:
            from sendgrid.helpers.mail import (
                Mail, Email, To, Content, ReplyTo, Header,
            )

            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_body),
            )

            if reply_to:
                message.reply_to = ReplyTo(reply_to)

            if unsubscribe_url:
                message.header = Header("List-Unsubscribe", f"<{unsubscribe_url}>")

            # Enable open and click tracking
            from sendgrid.helpers.mail import TrackingSettings, OpenTracking, ClickTracking
            tracking = TrackingSettings()
            tracking.open_tracking = OpenTracking(True)
            tracking.click_tracking = ClickTracking(True, True)
            message.tracking_settings = tracking

            response = self.client.send(message)

            if response.status_code in (200, 201, 202):
                msg_id = response.headers.get("X-Message-Id", "")
                logger.info(f"Email sent to {to_email} (id: {msg_id})")
                return msg_id
            else:
                logger.error(f"SendGrid error {response.status_code}: {response.body}")
                return None

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return None
