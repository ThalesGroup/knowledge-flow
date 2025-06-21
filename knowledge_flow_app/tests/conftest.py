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

import os
import warnings
import pytest
from knowledge_flow_app.application_context import ApplicationContext
from knowledge_flow_app.common.structures import ChatProfileStorageConfig, Configuration, ContentStorageConfig, EmbeddingConfig, MetadataStorageConfig, ProcessorConfig, VectorStorageConfig

os.environ["OPENAI_API_KEY"] = "sk-test-key"

@pytest.fixture(scope="function", autouse=True)
def app_context():
    """Fixture to initialize (and reset) the ApplicationContext for tests."""

    # 🧼 Force reset the singleton before initializing
    ApplicationContext._instance = None

    config = Configuration(
        security={
            "enabled": False,
            "keycloak_url": "http://fake",
            "client_id": "test-client"
        },
        content_storage=ContentStorageConfig(
            type="local"
        ),
        metadata_storage=MetadataStorageConfig(
            type="local"
        ),
        vector_storage=VectorStorageConfig(
            type="in_memory"
        ),
        embedding=EmbeddingConfig(
            type="openai"
        ),
        chat_profile_storage=ChatProfileStorageConfig(
            type="local"
        ),
        input_processors=[
            ProcessorConfig(
                prefix=".docx",
                class_path="knowledge_flow_app.input_processors.docx_markdown_processor.docx_markdown_processor.DocxMarkdownProcessor"
            ),
            ProcessorConfig(
                prefix=".pdf",
                class_path="knowledge_flow_app.input_processors.pdf_markdown_processor.pdf_markdown_processor.PdfMarkdownProcessor"
            ),
            ProcessorConfig(
                prefix=".pptx",
                class_path="knowledge_flow_app.input_processors.pptx_markdown_processor.pptx_markdown_processor.PptxMarkdownProcessor"
            ),
        ]
    )

    ApplicationContext(config)
