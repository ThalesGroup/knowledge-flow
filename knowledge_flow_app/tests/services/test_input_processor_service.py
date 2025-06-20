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

"""
Tests for InputProcessorService.
Input processor classes are not tested here - they are only mocked.
Covers success scenarios, error handling, and edge cases.
"""

# pylint: disable=redefined-outer-name

from io import BytesIO
from pathlib import Path
import pytest
from fastapi import UploadFile
import pandas as pd
from knowledge_flow_app.services.input_processor_service import InputProcessorService
from knowledge_flow_app.input_processors.base_input_processor import BaseInputProcessor, BaseTabularProcessor
from knowledge_flow_app.services import input_processor_service


# ----------------------------
# ⚙️ Fixtures
# ----------------------------


@pytest.fixture
def sample_pdf():
    """Fixture returning the path to an existing sample PDF file."""
    return Path("knowledge_flow_app/tests/assets/sample.pdf")


@pytest.fixture
def sample_docx():
    """Fixture returning the path to an existing sample DOCX file."""
    return Path("knowledge_flow_app/tests/assets/sample.docx")


@pytest.fixture
def unsupported_file(tmp_path):
    """Fixture creating a file with an unsupported extension."""
    file_path = tmp_path / "file.xyz"
    file_path.write_text("Unsupported format")
    return file_path


@pytest.fixture
def empty_pdf(tmp_path):
    """Fixture creating an empty PDF-like file."""
    file_path = tmp_path / "empty.pdf"
    file_path.write_text("")
    return file_path


class InvalidProcessor(BaseInputProcessor):
    """A processor class that returns no valid output to trigger error handling."""

    def process_metadata(self, file_path, front_metadata):
        return front_metadata

    def process(self, output_dir, input_file, input_file_metadata):
        pass

    def check_file_validity(self):
        pass

    def extract_file_metadata(self, *args, **kwargs):
        return {}


class NoUIDProcessor(BaseInputProcessor):
    """A processor that returns metadata without a document_uid."""

    def process_metadata(self, file_path, front_metadata):
        return {"title": "Missing UID"}

    def process(self, *args, **kwargs):
        pass

    def check_file_validity(self, *args, **kwargs):
        pass

    def extract_file_metadata(self, *args, **kwargs):
        return {}


class TabularDummyProcessor(BaseTabularProcessor):
    """A mock tabular processor that outputs a dummy table and markdown."""

    def process_metadata(self, file_path, front_metadata):
        return {"document_uid": "tabular-uid"}

    def convert_file_to_table(self, file_path):
        return pd.DataFrame([[1, 2], [3, 4]], columns=["a", "b"])

    def convert_file_to_markdown(self, *args, **kwargs):
        return "# Title\nSome content"

    def check_file_validity(self, *args, **kwargs):
        pass

    def extract_file_metadata(self, *args, **kwargs):
        return {}


# ----------------------------
# ✅ Nominal Cases
# ----------------------------


def test_extract_metadata_success_pdf(sample_pdf):
    """Check metadata extraction works for a PDF file."""
    service = InputProcessorService()
    metadata = service.extract_metadata(sample_pdf, {"source": "test"})
    assert "document_uid" in metadata


def test_extract_metadata_success_docx(sample_docx):
    """Check metadata extraction works for a DOCX file."""
    service = InputProcessorService()
    metadata = service.extract_metadata(sample_docx, {"source": "test"})
    assert "document_uid" in metadata


def test_process_success_pdf(tmp_path, sample_pdf, monkeypatch):
    """Ensure PDF file is processed correctly and output is generated."""

    def mock_describe(*args, **kwargs):
        return "This is a test image description"

    monkeypatch.setattr(
        "knowledge_flow_app.input_processors.pdf_markdown_processor.pdf_markdown_processor.PdfMarkdownProcessor._describe_picture",
        mock_describe,
    )

    target_path = tmp_path / sample_pdf.name
    target_path.write_bytes(sample_pdf.read_bytes())
    service = InputProcessorService()
    service.process(tmp_path, target_path.name, {"key": "value"})
    output_file = tmp_path / "output" / "output.md"
    assert output_file.exists()


def test_process_success_docx(tmp_path, sample_docx):
    """Ensure DOCX file is processed correctly and output is generated."""
    target_path = tmp_path / sample_docx.name
    target_path.write_bytes(sample_docx.read_bytes())
    service = InputProcessorService()
    service.process(tmp_path, target_path.name, {"key": "value"})
    output_file = tmp_path / "output" / "output.md"
    assert output_file.exists()


def test_process_tabular_processor_creates_csv(monkeypatch, tmp_path):
    """Ensure that processing CSV with TabularDummyProcessor creates a table.csv."""

    class DummyContext:
        def get_input_processor_instance(self, ext):
            return TabularDummyProcessor()

    monkeypatch.setattr(input_processor_service.ApplicationContext, "get_instance", DummyContext)
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b\n1,2\n3,4")
    service = InputProcessorService()
    service.process(tmp_path, "sample.csv", {"document_uid": "tabular-uid"})
    output_file = tmp_path / "output" / "table.csv"
    assert output_file.exists()


@pytest.mark.asyncio
async def test_process_file_method(monkeypatch, tmp_path):
    class DummyContext:
        def get_input_processor_instance(self, ext):
            return TabularDummyProcessor()

    monkeypatch.setattr(input_processor_service.ApplicationContext, "get_instance", DummyContext)
    csv_content = b"a,b\n1,2\n3,4"
    upload = UploadFile(filename="data.csv", file=BytesIO(csv_content))
    service = InputProcessorService()
    await service.process_file(upload, {"meta": "test"}, tmp_path)
    doc_dir = tmp_path / "data.csv" / "tabular-uid"
    assert (doc_dir / "metadata.json").exists()


# ----------------------------
# ❌ Failure Cases
# ----------------------------


def test_extract_metadata_failure_unsupported_extension(unsupported_file):
    """Validate that unsupported file types raise a ValueError."""
    service = InputProcessorService()
    with pytest.raises(ValueError, match="No input processor found for extension"):
        service.extract_metadata(unsupported_file, {"source": "test"})


def test_extract_metadata_missing_document_uid(monkeypatch, tmp_path):
    """Validate that missing document_uid in metadata raises a ValueError."""

    class DummyContext:
        def get_input_processor_instance(self, ext):
            return NoUIDProcessor()

    fake_file = tmp_path / "fake.pdf"
    fake_file.write_text("Fake content")
    monkeypatch.setattr(input_processor_service.ApplicationContext, "get_instance", DummyContext)
    service = InputProcessorService()
    with pytest.raises(ValueError, match="missing 'document_uid'"):
        service.extract_metadata(fake_file, {})


@pytest.mark.asyncio
async def test_process_file_missing_document_uid(monkeypatch, tmp_path):
    """Validate that missing document_uid in async process_file raises RuntimeError."""

    class DummyContext:
        def get_input_processor_instance(self, ext):
            return NoUIDProcessor()

    fake_file = UploadFile(filename="note.md", file=BytesIO(b"# Missing UID"))
    monkeypatch.setattr(input_processor_service.ApplicationContext, "get_instance", DummyContext)
    service = InputProcessorService()
    with pytest.raises(RuntimeError, match="Missing document UID in metadata"):
        await service.process_file(fake_file, {}, tmp_path)


@pytest.mark.asyncio
async def test_process_unknown_processor_type(monkeypatch, tmp_path):
    """Validate error is raised when processor type is unrecognized."""

    class DummyContext:
        def get_input_processor_instance(self, ext):
            return InvalidProcessor()

    input_file = tmp_path / "sample.weird"
    input_file.write_text("some data")
    monkeypatch.setattr(input_processor_service.ApplicationContext, "get_instance", DummyContext)
    service = InputProcessorService()
    with pytest.raises(RuntimeError, match="Unknown processor type"):
        service.process(tmp_path, input_file.name, {"document_uid": "test"})


# ----------------------------
# ⚠️ Edge Cases
# ----------------------------


def test_extract_metadata_empty_file(empty_pdf):
    """Ensure that extracting metadata from an empty file raises an exception."""
    service = InputProcessorService()
    with pytest.raises(Exception):
        service.extract_metadata(empty_pdf, {"note": "empty file"})


def test_process_file_not_found(tmp_path):
    """Ensure that attempting to process a nonexistent file raises FileNotFoundError."""
    service = InputProcessorService()
    with pytest.raises(FileNotFoundError):
        service.process(tmp_path, "nonexistent.pdf", {"key": "value"})
