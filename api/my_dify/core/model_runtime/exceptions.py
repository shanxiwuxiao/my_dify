class ModelError(Exception):
    """Base error raised by a model provider."""


class ModelConfigurationError(ModelError):
    """The model provider is not configured correctly."""


class ModelRequestError(ModelError):
    """The model provider request failed."""