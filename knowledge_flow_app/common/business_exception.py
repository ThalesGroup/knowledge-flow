class BusinessException(Exception):
    """Base class for business-related errors."""
    pass


class ChatProfileError(Exception):
    """Base class for chat profile errors."""
    pass

class TokenLimitExceeded(ChatProfileError):
    pass

class DocumentProcessingError(ChatProfileError):
    def __init__(self, filename: str):
        super().__init__(f"Failed to process file '{filename}'")
        self.filename = filename

class ProfileNotFound(ChatProfileError):
    def __init__(self, profile_id: str):
        super().__init__(f"Profile '{profile_id}' not found")
        self.profile_id = profile_id

class ProfileDeletionError(ChatProfileError):
    pass

class DocumentDeletionError(ChatProfileError):
    pass

class DocumentNotFound(ChatProfileError):
    pass
