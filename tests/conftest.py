"""Shared pytest configuration.

Integration tests are skipped by default. Run them explicitly with:

    uv run pytest -m integration
"""

import pytest


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip @pytest.mark.integration tests unless -m integration is passed."""
    marker_expr = config.getoption("-m") or ""
    if "integration" in marker_expr:
        return
    skip_integration = pytest.mark.skip(
        reason="integration test; run with: pytest -m integration",
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
