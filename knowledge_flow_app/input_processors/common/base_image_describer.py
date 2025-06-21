# knowledge_flow_app/image_description/base_image_describer.py

from abc import ABC, abstractmethod

class BaseImageDescriber(ABC):
    @abstractmethod
    def describe(self, image_base64: str) -> str:
        """Given a base64 image, return a textual description."""
        pass
