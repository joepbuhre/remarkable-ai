# src/remarkable_ai/email_reader.py
from mailbox import Mailbox
import os
import uuid
import base64
import smtplib
from email.utils import make_msgid
from email.message import EmailMessage
from typing import List, Optional

from imap_tools.mailbox import MailBox
from imap_tools.message import MailMessage
from imap_tools.query import AND
from pydantic import BaseModel

from remarkable_ai.log import logger
from remarkable_ai.config import (
    EMAIL_HOST, EMAIL_USER, EMAIL_PASS, EMAIL_FOLDER, SMTP_PORT,
)


# Attachment model used in outgoing replies
class ReplyAttachmentModel(BaseModel):
    filename: str
    content: bytes
    mime_type: str = "application"
    subtype: str = "octet-stream"


# Attachment extracted from incoming email
class EmailAttachmentModel(BaseModel):
    filename: str
    content_type: str
    base64_content: str


# Full parsed email model
class ParsedEmailModel(BaseModel):
    email_id: uuid.UUID
    from_address: str
    subject: str
    body: str
    attachment: Optional[EmailAttachmentModel] = None
    message_id: Optional[str] = None


def reply_to_email(email: ParsedEmailModel, attachments: List[ReplyAttachmentModel] = []):
    """
    Sends a reply email to the sender with optional attachments using ReplyAttachmentModel.
    Preserves proper threading using Message-ID, In-Reply-To, and References headers.
    """
    msg = EmailMessage()

    # Clean subject line
    if email.subject.lower().startswith("re:"):
        msg["Subject"] = email.subject
    else:
        msg["Subject"] = f"Re: {email.subject}"

    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER
    msg["Message-ID"] = make_msgid()

    if email.message_id:
        msg["In-Reply-To"] = email.message_id
        msg["References"] = email.message_id

    msg.set_content("done")

    for attachment in attachments:
        msg.add_attachment(
            attachment.content,
            maintype=attachment.mime_type,
            subtype=attachment.subtype,
            filename=attachment.filename
        )

    logger.info(f"Replying to {email.from_address} with {len(attachments)} attachment(s)")

    with smtplib.SMTP(EMAIL_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

    logger.info("Reply sent successfully.")

def move_email(mailbox: MailBox, msg: MailMessage):
    try:
        target_folder = "RemarkableAI/Done"
        logger.info(f"Moving message UID {msg.uid} to folder: {target_folder}")
        if msg.uid is not None:
            mailbox.move(msg.uid, "RemarkableAI/Done")
            logger.info(f"Moved message UID {msg.uid} to 'RemarkableAI/Done'")
        else:
            logger.warning("Message has no UID, cannot move.")
    except Exception as e:
        logger.warning(f"Failed to move message {msg.uid}: {e}")

def fetch_latest_image_attachments(dest_folder: str = "tmp") -> List[ParsedEmailModel]:
    """
    Connects to the configured IMAP mailbox and fetches image attachments from the latest seen emails.
    Saves each image into a UUID-based subfolder and returns a list of parsed email models.

    Args:
        dest_folder (str): Folder to save attachments in

    Returns:
        List[ParsedEmailModel]: List of parsed emails containing metadata and base64 image
    """
    results: List[ParsedEmailModel] = []

    logger.info(f"Connecting to IMAP server at: {EMAIL_HOST}")

    with MailBox(EMAIL_HOST) as mailbox:  # type: ignore
        mailbox.login(EMAIL_USER, EMAIL_PASS, EMAIL_FOLDER)
        mailbox.folder.set(EMAIL_FOLDER)


        for msg in mailbox.fetch(AND(seen=True), reverse=True, limit=10):
            for att in msg.attachments:
                if att.content_type.startswith("image/"):
                    email_uuid = uuid.uuid4()
                    subfolder = os.path.join(dest_folder, str(email_uuid))
                    os.makedirs(subfolder, exist_ok=True)

                    image_path = os.path.join(subfolder, att.filename)
                    with open(image_path, "wb") as f:
                        f.write(att.payload)

                    logger.info(f"Saved image to: {image_path}")

                    base64_content = base64.b64encode(att.payload).decode("utf-8")

                    attachment_model = EmailAttachmentModel(
                        filename=att.filename,
                        content_type=att.content_type,
                        base64_content=base64_content
                    )

                    message_id = msg.headers.get("Message-ID", [""])[0] if isinstance(msg.headers.get("Message-ID"), list) else msg.headers.get("Message-ID", [""])

                    email_model = ParsedEmailModel(
                        email_id=email_uuid,
                        from_address=msg.from_,
                        subject=msg.subject,
                        body=msg.text or msg.html or "",
                        message_id=message_id[0],
                        attachment=attachment_model
                    )

                    results.append(email_model)

                    move_email(mailbox, msg)

    if not results:
        logger.warning("No image attachments found in the latest emails.")

    return results
