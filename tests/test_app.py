"""IHM d'agent-projets : démarrage à blanc (registre factice, aucun appel réseau)."""
import os

import dotenv
from streamlit.testing.v1 import AppTest

from agent_socle import projets

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def test_page_affiche_registre_et_tests(monkeypatch):
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setenv("AGENT_AUTH", "0")
    monkeypatch.setenv("AGENT_PROJETS_PORT", "0")
    monkeypatch.setenv("AGENT_KNOWLEDGE_DIR", "")
    monkeypatch.delenv("GROUNDCOVER_API_KEY", raising=False)
    monkeypatch.setattr(projets, "registre", lambda: {"alpha": {"cucumber": {"client_repo": "r1"}, "application": None}})
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert at.title[0].value == "🗂️ Projets et connexions"
    assert [b.label for b in at.button][:1] == ["Tester la connexion"]
    assert len(at.dataframe) == 1
