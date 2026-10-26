"""Smoke test: the dashboard renders without exceptions or error banners (e.g. an unbalanced reconciliation)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parent.parent


@pytest.mark.skipif(not (ROOT / "suppliers.duckdb").exists(), reason="run generate_data.py first")
def test_dashboard_renders_and_balances():
    at = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=60).run()
    assert not at.exception
    assert not at.error
