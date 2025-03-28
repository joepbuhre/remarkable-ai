# src/remarkable_ai/image_analyzer.py

import os
import base64
from typing import List, Union
from h11 import Response
import pypandoc
from openai import OpenAI
from remarkable_ai.config import OPENAPI_APIKEY
from remarkable_ai.email_reader import EmailAttachmentModel
from remarkable_ai.log import logger
from dotenv import load_dotenv

from openai.types.responses import ResponseInputTextParam, ResponseInputParam, ResponseInputImageParam, ResponseInputMessageContentListParam
from openai.types.responses.response_input_item_param import Message

from openai.types.beta.threads import Text, ImageURL
# from openai.types.beta.assistants import ResponseInputParam


load_dotenv()

def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

class ImageAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAPI_APIKEY)

        self.template_path = os.getenv("TEMPLATE_DOCX_PATH")
        self.image_path = os.getenv("IMAGE_PATH")
        self.output_md = "input.md"
        self.output_docx = "output.docx"
        self.output_pdf = "output.pdf"

    def encode_image(self, path: str) -> str:
        try:
            with open(path, "rb") as image_file:
                logger.info(f"Encoding image: {path}")
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            logger.error(f"Image not found: {path}")
            raise

    def analyze_image(self, image: EmailAttachmentModel, user_prompt: str = "") -> str:
        content: ResponseInputMessageContentListParam = [
            ResponseInputTextParam(
                        type="input_text",
                        text="Analyze this handwritten note. Please analyze"
                    )
        ] 

        # Add user prompt if supplied
        if user_prompt != "":
            content.append(
                ResponseInputTextParam(
                    type="input_text",
                    text=user_prompt
                )
            )
        # Add image
        content.append(
            ResponseInputImageParam(
                type="input_image",
                detail="auto",
                image_url=f"data:image/jpeg;base64,{image.base64_content}"
            )
        )

        # construct image
        input_data: Message = Message(
                role='user', 
                content=content
            )
        
        logger.info("Calling OpenAI for image + text analysis")
        response = self.client.responses.create(
            model="gpt-4o",
            input=[input_data]
        )

        markdown = response.output_text
        with open(self.output_md, "w", encoding="utf-8") as f:
            f.write(markdown)

        logger.info("Analysis complete. Markdown saved.")
        return self.output_md

    def convert_to_docx(self, input_md: Union[str, None] = None) -> str:
        input_md = input_md or self.output_md

        logger.info("Converting markdown to DOCX")
        try:
            pypandoc.convert_file(
                input_md,
                "docx",
                outputfile=self.output_docx,
                extra_args=[f"--reference-doc={self.template_path}"]
            )
            logger.info("DOCX generated successfully")
            return self.output_docx
        except Exception as e:
            logger.exception("DOCX conversion failed")
            raise

    def convert_docx_to_pdf(self, input_docx: str) -> str:
        logger.info(f"Converting DOCX to PDF: {input_docx}")
        try:
            pypandoc.convert_file(
                input_docx,
                "pdf",
                outputfile=self.output_pdf,
                extra_args=["--pdf-engine=xelatex"]
            )
            logger.info("PDF created successfully")
            return self.output_pdf
        except Exception as e:
            logger.exception("DOCX to PDF conversion failed")
            raise

