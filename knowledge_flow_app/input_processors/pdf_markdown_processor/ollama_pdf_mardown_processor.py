# knowledge_flow_app/input_processors/pdf_markdown_processor/ollama_pdf_markdown_processor.py

from knowledge_flow_app.input_processors.common.image_describers.ollama_image_describer import OllamaImageDescriber
from knowledge_flow_app.input_processors.pdf_markdown_processor.pdf_markdown_processor import PdfMarkdownProcessor

class OllamaPdfMarkdownProcessor(PdfMarkdownProcessor):
    def __init__(self):
        super().__init__(image_describer=OllamaImageDescriber())
