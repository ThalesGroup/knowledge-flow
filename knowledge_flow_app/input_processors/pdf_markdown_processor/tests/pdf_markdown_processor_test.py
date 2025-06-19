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

# tests/test_pdf_processor.py

import os
from dotenv import load_dotenv
import pytest
from pathlib import Path
import tempfile
from knowledge_flow_app.input_processors.pdf_markdown_processor.pdf_markdown_processor import PdfMarkdownProcessor


dotenv_path = os.getenv("ENV_FILE", "./config/.env")
load_dotenv(dotenv_path)


@pytest.fixture
def processor():
    return PdfMarkdownProcessor()


@pytest.fixture
def sample_pdf_file():
    return Path(__file__).parent / "assets" / "sample.pdf"


def test_pdf_processor_end_to_end(processor, sample_pdf_file):
    with tempfile.TemporaryDirectory(prefix="knowledge_flow_test_") as tmpdirname:
        output_dir = Path(tmpdirname)
        output_dir.mkdir(exist_ok=True, parents=True)

        assert processor.check_file_validity(sample_pdf_file)

        metadata = processor.process_metadata(sample_pdf_file)
        
        assert metadata["document_name"] == "sample.pdf"
        # assert metadata["title"] == "Test Title"
        # assert metadata["author"] == "Test Author"
        # assert metadata["subject"] == "Test Subject"
        assert metadata["num_pages"] == 2
        assert "document_uid" in metadata

        result = processor.convert_file_to_markdown(sample_pdf_file, output_dir)
        
        assert result["status"] == "fallback_to_text"
        assert Path(result["md_file"]).exists()
        assert Path(result["md_file"]).read_text(encoding="utf-8").strip() != ""
