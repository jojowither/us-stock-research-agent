import pytest
from pydantic_ai import models

models.ALLOW_MODEL_REQUESTS = False


@pytest.fixture
def anyio_backend():
    return "asyncio"
