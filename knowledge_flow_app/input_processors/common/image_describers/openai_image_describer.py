# knowledge_flow_app/input_processors/openai_image_describer.py

import base64
import logging
import requests
from knowledge_flow_app.input_processors.common.base_image_describer import BaseImageDescriber
from knowledge_flow_app.config.embedding_openai_settings import EmbeddingOpenAISettings

logger = logging.getLogger(__name__)

class OpenaiImageDescriber(BaseImageDescriber):
    def __init__(self):
        self.settings = EmbeddingOpenAISettings()

    def describe(self, image_base64: str) -> str:
        try:
            image_bytes = base64.b64decode(image_base64)

            headers = {
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Describe the image in detail. "
                                    "Start with 'There is an image showing...' and include structure, relationships, and context."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 512,
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

        except Exception as e:
            logger.error(f"OpenAI image description failed: {e}")
            return "Image description not available."
