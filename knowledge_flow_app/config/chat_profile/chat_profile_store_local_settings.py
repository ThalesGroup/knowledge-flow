from pathlib import Path
import os

class ChatProfileLocalSettings:
    def __init__(self):
        # Default local path unless overridden by env var
        env_value = os.getenv("LOCAL_CHAT_PROFILE_STORAGE_PATH")
        if env_value:
            self.root_path = Path(env_value).expanduser()
        else:
            self.root_path = Path.home() / ".fred" / "chat-profiles"

        self.root_path.mkdir(parents=True, exist_ok=True)