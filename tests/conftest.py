"""Pytest configuration scoped to the Claude plugin tests."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "gateway_environment: contacts the production GoodMem Cloud gateway; "
        "opt in with GOODMEM_GATEWAY_ENVIRONMENT_CHECK=1",
    )
