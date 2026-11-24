"""API en lecture d'agent-projets."""
import json
import urllib.error
import urllib.request

import pytest

import api
from agent_socle import projets

REGISTRE = {"alpha": {"cucumber": {"client_repo": "r1"}, "application": None}}


@pytest.fixture
def serveur(monkeypatch):
    monkeypatch.setattr(projets, "registre", lambda: REGISTRE)
    srv = api.demarrer_en_fond(0)
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def test_sante_registre_et_projet(serveur):
    assert _get(serveur + "/sante") == (200, {"ok": True, "source": "agent-projets"})
    assert _get(serveur + "/projets") == (200, REGISTRE)
    assert _get(serveur + "/projets/alpha/") == (200, REGISTRE["alpha"])


def test_inconnu_404_et_ecriture_refusee(serveur):
    for chemin in ("/projets/inconnu", "/autre"):
        with pytest.raises(urllib.error.HTTPError) as e:
            _get(serveur + chemin)
        assert e.value.code == 404
    requete = urllib.request.Request(serveur + "/projets", data=b"{}", method="POST")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(requete, timeout=5)
    assert e.value.code == 405


def test_client_du_socle_passe_par_l_api(serveur, monkeypatch):
    monkeypatch.setenv("AGENT_PROJETS_API", serveur)
    monkeypatch.setattr(api, "reponse", lambda chemin: (200, {"via": "api", "chemin": chemin}))
    assert projets.lire("/projets/alpha") == {"via": "api", "chemin": "/projets/alpha"}


def test_port_occupe_et_port_par_variable(serveur, monkeypatch):
    port = int(serveur.rsplit(":", 1)[1])
    assert api.demarrer_en_fond(port) is None
    monkeypatch.setenv("AGENT_PROJETS_PORT", "9999")
    assert api.port() == 9999
    monkeypatch.setenv("AGENT_PROJETS_PORT", "x")
    assert api.port() == api.PORT_DEFAUT


def test_cli_projets(monkeypatch, capsys):
    import main
    monkeypatch.setattr(projets, "registre", lambda: REGISTRE)
    assert main.main(["--step", "projets"]) == 0
    assert json.loads(capsys.readouterr().out) == REGISTRE
    assert main.main(["--step", "projets", "--nom", "inconnu"]) == 1
