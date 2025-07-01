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

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from knowledge_flow_app.services.chat_profile_service import (
    ChatProfileService,
    count_tokens_from_markdown,
)
from knowledge_flow_app.application_context import ApplicationContext


@pytest.fixture
def service(monkeypatch):
    service = ChatProfileService()
    monkeypatch.setattr(service, "store", MagicMock())
    monkeypatch.setattr(service, "processor", MagicMock())
    return service


def test_count_tokens_from_markdown_fallback(monkeypatch, tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("text")

    class FallbackEncoding:
        def encode(self, text):
            return text.split()

    # simulate missing model_name
    monkeypatch.setattr("knowledge_flow_app.services.chat_profile_service.ApplicationContext.get_instance", lambda: MagicMock(get_embedder=lambda: MagicMock(embedding=None)))
    monkeypatch.setattr("tiktoken.get_encoding", lambda _: FallbackEncoding())

    assert count_tokens_from_markdown(md_file) == 1


@pytest.mark.asyncio
async def test_list_profiles_with_corrupt_entry(service, caplog):
    service.store.list_profiles.return_value = [{"id": "123", "documents": [{}]}]
    result = await service.list_profiles()
    assert isinstance(result, list)  # error is logged, not raised


@pytest.mark.asyncio
async def test_create_profile_missing_output_md(service, monkeypatch, tmp_path):
    input_file = tmp_path / "test.docx"
    input_file.write_text("dummy")

    def fake_process(output_dir, input_file, input_file_metadata):
        (output_dir / "output").mkdir(parents=True, exist_ok=True)  # no md file created

    monkeypatch.setattr(service.processor, "process", fake_process)

    with pytest.raises(FileNotFoundError):
        await service.create_profile("Missing md", "md fail", tmp_path)


def test_count_tokens_from_markdown(monkeypatch, tmp_path):
    md_file = tmp_path / "file.md"
    md_file.write_text("hello world")

    class FakeEncoding:
        def encode(self, text):
            return text.split()

    embedder = MagicMock()
    embedder.embedding.model_name = "test-model"
    monkeypatch.setattr("tiktoken.encoding_for_model", lambda _: FakeEncoding())
    monkeypatch.setattr("knowledge_flow_app.services.chat_profile_service.ApplicationContext.get_instance", lambda: MagicMock(get_embedder=lambda: embedder))

    tokens = count_tokens_from_markdown(md_file)
    assert tokens == 2


@pytest.mark.asyncio
async def test_list_profiles_nominal(service):
    service.store.list_profiles.return_value = [{"id": "123", "title": "T", "description": "D", "documents": []}]
    result = await service.list_profiles()
    assert result[0].id == "123"


@pytest.mark.asyncio
async def test_create_profile_empty_dir(service, tmp_path):
    result = await service.create_profile("Empty", "Nothing", tmp_path)
    assert result.title == "Empty"


@pytest.mark.asyncio
async def test_create_profile_too_many_tokens(service, monkeypatch, tmp_path):
    input_file = tmp_path / "file.docx"
    input_file.write_text("dummy")

    def fake_process(output_dir, input_file, input_file_metadata):
        out = output_dir / "output"
        out.mkdir(parents=True, exist_ok=True)
        (out / "file.md").write_text("# mock")

    monkeypatch.setattr(service.processor, "process", fake_process)
    monkeypatch.setattr("knowledge_flow_app.services.chat_profile_service.count_tokens_from_markdown", lambda _: ApplicationContext.get_instance().get_chat_profile_max_tokens + 1)

    with pytest.raises(ValueError):
        await service.create_profile("Too many", "tokens", tmp_path)


@pytest.mark.asyncio
async def test_delete_profile(service):
    service.store.delete_profile.return_value = None
    result = await service.delete_profile("abc")
    assert result == {"success": True}


@pytest.mark.asyncio
async def test_get_profile_with_markdown(service):
    service.store.get_profile_description.return_value = {"id": "1", "title": "T", "description": "D"}
    service.store.list_markdown_files.return_value = [("doc.md", "# md")]
    result = await service.get_profile_with_markdown("1")
    assert "# md" in result["markdown"]


@pytest.mark.asyncio
async def test_get_profile_with_markdown_no_md(service):
    service.store.get_profile_description.return_value = {"id": "1", "title": "T", "description": "D"}
    if hasattr(service.store, "list_markdown_files"):
        delattr(service.store, "list_markdown_files")
    result = await service.get_profile_with_markdown("1")
    assert result["markdown"] == ""


@pytest.mark.asyncio
async def test_update_profile_nominal(service, monkeypatch, tmp_path):
    upload = MagicMock()
    upload.filename = "f.docx"
    upload.read = AsyncMock(return_value=b"hello")

    service.store.get_profile_description.return_value = {
        "id": "1",
        "documents": [],
        "title": "",
        "description": "",
        "tokens": 0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "creator": "system",
        "user_id": "local",
    }
    service.store.list_markdown_files.return_value = []
    service.store.save_profile = MagicMock()

    def fake_process(output_dir, input_file, input_file_metadata):
        out = output_dir / "output"
        out.mkdir(parents=True, exist_ok=True)
        (out / "f.md").write_text("# md")

    monkeypatch.setattr(service.processor, "process", fake_process)
    monkeypatch.setattr("knowledge_flow_app.services.chat_profile_service.count_tokens_from_markdown", lambda _: 10)

    result = await service.update_profile("1", "T", "D", [upload])
    assert result.tokens == 10


@pytest.mark.asyncio
async def test_update_profile_error(service):
    service.store.get_profile_description.side_effect = Exception("fail")
    with pytest.raises(HTTPException):
        await service.update_profile("1", "T", "D", [])


@pytest.mark.asyncio
async def test_delete_document(service, monkeypatch):
    service.store.get_profile_description.return_value = {"id": "1", "documents": [{"id": "d1", "tokens": 10}]}
    service.store.get_document.return_value.__enter__.return_value.read.return_value = b"abc"
    service.store.list_markdown_files.return_value = [("d1.md", "# md")]
    service.store.save_profile = MagicMock()
    service.store.delete_markdown_file = MagicMock()

    result = await service.delete_document("1", "d1")
    assert result["success"]


@pytest.mark.asyncio
async def test_delete_document_error(service):
    service.store.get_profile_description.side_effect = Exception("fail")
    with pytest.raises(HTTPException):
        await service.delete_document("1", "d1")
