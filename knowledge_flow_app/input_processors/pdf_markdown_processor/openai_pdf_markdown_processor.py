# Copyright Thales 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# knowledge_flow_app/input_processors/pdf_markdown_processor/openai_pdf_markdown_processor.py

from knowledge_flow_app.input_processors.common.image_describers.openai_image_describer import OpenaiImageDescriber
from knowledge_flow_app.input_processors.pdf_markdown_processor.pdf_markdown_processor import PdfMarkdownProcessor


class OpenaiPdfMarkdownProcessor(PdfMarkdownProcessor):
    def __init__(self):
        super().__init__(image_describer=OpenaiImageDescriber())
