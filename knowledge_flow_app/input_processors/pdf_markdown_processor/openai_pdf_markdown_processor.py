# knowledge_flow_app/input_processors/pdf_markdown_processor/openai_pdf_markdown_processor.py

from knowledge_flow_app.input_processors.common.image_describers.openai_image_describer import OpenaiImageDescriber
from knowledge_flow_app.input_processors.pdf_markdown_processor.pdf_markdown_processor import PdfMarkdownProcessor

class OpenaiPdfMarkdownProcessor(PdfMarkdownProcessor):
    def __init__(self):
        super().__init__(image_describer=OpenaiImageDescriber())
