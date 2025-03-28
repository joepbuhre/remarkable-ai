# src/remarkable_ai/webhook_listener.py
import mimetypes
import os
from typing import List
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from remarkable_ai.log import logger
from remarkable_ai.image_analyzer import ImageAnalyzer
from remarkable_ai.email_reader import ReplyAttachmentModel, fetch_latest_image_attachments, reply_to_email


app = FastAPI()
analyzer = ImageAnalyzer()


@app.get("/", response_class=HTMLResponse)
async def welcome():
    logger.info("Welcome page accessed")
    return """
    <html>
        <head>
            <title>remarkable-ai</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(120deg, #1f1f1f, #3d3d3d);
                    color: #ffffff;
                    text-align: center;
                    padding-top: 10%;
                }
                h1 {
                    font-size: 3em;
                    margin-bottom: 0.2em;
                }
                p {
                    font-size: 1.2em;
                    color: #aaa;
                }
            </style>
        </head>
        <body>
            <h1>📦 remarkable-ai</h1>
            <p>Document ingestion service is up and running.</p>
        </body>
    </html>
    """


@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    logger.info(f"Webhook received: {data}")
    return {"status": "received"}


def load_folder_as_attachments(folder_path: str) -> List[ReplyAttachmentModel]:
    attachments: List[ReplyAttachmentModel] = []

    for filename in os.listdir(folder_path):
        logger.info(f"fetching {filename}")
        full_path = os.path.join(folder_path, filename)

        if os.path.isfile(full_path):
            with open(full_path, "rb") as f:
                content = f.read()

            mime_type, _ = mimetypes.guess_type(full_path)
            if mime_type:
                maintype, subtype = mime_type.split("/")
            else:
                maintype, subtype = "application", "octet-stream"

            attachments.append(ReplyAttachmentModel(
                filename=filename,
                content=content,
                mime_type=maintype,
                subtype=subtype
            ))

    return attachments

@app.post("/email-fetch")
async def email_fetch():
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
