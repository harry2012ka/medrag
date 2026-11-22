"""Click-through smoke test of the Streamlit UI (empty state -> sample -> question).

Skipped when streamlit isn't installed (the fast `tests` workflow). Runs in the `eval`
workflow, which installs the full requirements and the real embedding model.
"""

import os

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("sentence_transformers")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def _clean_env(monkeypatch):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(k, raising=False)


def test_empty_state_sample_and_question(monkeypatch):
    _clean_env(monkeypatch)
    at = AppTest.from_file(APP, default_timeout=180).run()
    assert not at.exception
    assert any("How this works" in e.label for e in at.expander)
    main_sample = [b for b in at.button if b.key == "sample_main"]
    assert main_sample, "empty state should offer the sample in the main area (sidebar is hidden on phones)"

    main_sample[0].click().run()
    assert not at.exception
    assert "sample" in at.session_state["docs"]
    assert not [b for b in at.button if b.key == "sample_main"]   # empty state gone once a doc is loaded

    at.chat_input[0].set_value("What blood pressure counts as hypertension?").run()
    assert not at.exception
    last = at.session_state["messages"][-1]
    assert last["role"] == "assistant" and last["citations"], last
    assert all(c["page"] for c in last["citations"])


def test_off_topic_question_is_refused(monkeypatch):
    _clean_env(monkeypatch)
    at = AppTest.from_file(APP, default_timeout=180).run()
    [b for b in at.button if b.key == "sample_main"][0].click().run()
    at.chat_input[0].set_value("How do I fix a flat bicycle tire?").run()
    assert not at.exception
    last = at.session_state["messages"][-1]
    assert not last["citations"]
