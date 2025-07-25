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

import tempfile
from pathlib import Path

import pytest

from knowledge_flow_app.core.processors.input.docx_markdown_processor.docx_markdown_processor import DocxMarkdownProcessor


@pytest.fixture
def processor():
    return DocxMarkdownProcessor()


@pytest.mark.asyncio
async def test_process_docx_file(processor):
    test_docx_path = Path("knowledge_flow_app/input_processors/docx_markdown_processor/tests/assets/sample.docx")

    assert processor.check_file_validity(test_docx_path)
    metadata = processor.process_metadata(test_docx_path)
    assert "document_uid" in metadata

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        result = processor.convert_file_to_markdown(test_docx_path, output_dir)
        print(result)
