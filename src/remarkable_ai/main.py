# src/remarkable_ai/main.py
import os
from loguru import logger
import uvicorn
from remarkable_ai.email_reader import fetch_latest_image_attachments, reply_to_email
from remarkable_ai.image_analyzer import ImageAnalyzer
from remarkable_ai.webhook_listener import app, load_folder_as_attachments
from remarkable_ai.config import WEBHOOK_PORT

def email_fetch():
    emails = fetch_latest_image_attachments()
    for email in emails:
        if email.attachment is None:
            continue
        analyzer = ImageAnalyzer()

        filename = os.path.splitext(email.attachment.filename)[0]
        
        analyzer.output_docx = f"tmp\\{str(email.email_id)}\\{filename}.docx"
        analyzer.output_pdf = f"tmp\\{str(email.email_id)}\\{filename}.pdf"
        analyzer.output_md = f"tmp\\{str(email.email_id)}\\{filename}.md"

        md_file = analyzer.analyze_image(email.attachment, email.body)
        docx_file = analyzer.convert_to_docx(md_file)
        logger.info(f"Process complete. Output: {docx_file}")
        logger.info("Replying on email now")

        
        # build attachments
        attachment_list = load_folder_as_attachments(f"tmp\\{str(email.email_id)}")
        reply_to_email(
            email,
            attachments=attachment_list
        )

if __name__ == "__main__":
    email_fetch()