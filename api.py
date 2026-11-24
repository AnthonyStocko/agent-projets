"""API locale d'agent-projets, en lecture seule (http://localhost:8512 ; AGENT_PROJETS_PORT pour changer de port).

GET /sante, /projets, /projets/<nom> : registre des projets (agent_socle.projets.local, façade sans migration sur les
projets Cucumber et les applications du manager). Aucun secret servi ; toute autre méthode : 405.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from agent_socle import projets

PORT_DEFAUT = 8512


def port() -> int:
    try:
        return int(os.getenv("AGENT_PROJETS_PORT", "").strip() or PORT_DEFAUT)
    except ValueError:
        return PORT_DEFAUT


def reponse(chemin: str):
    """(code HTTP, corps) d'une lecture."""
    chemin = unquote(urlsplit(chemin).path).rstrip("/") or "/"
    if chemin == "/sante":
        return 200, {"ok": True, "source": "agent-projets"}
    if chemin == "/projets" or chemin.startswith("/projets/"):
        donnee = projets.local(chemin)
        return (200, donnee) if donnee is not None else (404, {"erreur": f"projet inconnu : {chemin[9:]}"})
    return 404, {"erreur": f"chemin inconnu : {chemin}"}


class Lecture(BaseHTTPRequestHandler):
    def _envoyer(self, code: int, corps) -> None:
        donnees = json.dumps(corps, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(donnees)))
        self.end_headers()
        self.wfile.write(donnees)

    def do_GET(self):  # noqa: N802
        self._envoyer(*reponse(self.path))

    def _refus(self):
        self._envoyer(405, {"erreur": "API en lecture seule"})

    do_POST = do_PUT = do_PATCH = do_DELETE = _refus

    def log_message(self, *args):
        pass


class Serveur(ThreadingHTTPServer):
    # Pas de réutilisation d'adresse : sous Windows, elle laisserait deux serveurs écouter le même port
    allow_reuse_address = False
    daemon_threads = True


def serveur(numero: int = None, hote: str = "127.0.0.1") -> ThreadingHTTPServer:
    return Serveur((hote, port() if numero is None else numero), Lecture)


def demarrer_en_fond(numero: int = None):
    """Serveur dans un fil de fond ; None si le port est déjà pris (API déjà lancée ailleurs)."""
    try:
        srv = serveur(numero)
    except OSError:
        return None
    threading.Thread(target=srv.serve_forever, daemon=True, name="api-projets").start()
    return srv
