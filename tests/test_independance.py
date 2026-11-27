"""agent-projets n'importe aucun autre agent : seulement agent_socle, la bibliothèque standard et ses dépendances."""
import ast
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
INTERDITS = ("tools", "webhook_server", "mcp_lecture", "manager")


def test_aucun_import_d_un_autre_agent():
    fautes = []
    for f in sorted(p for p in RACINE.rglob("*.py") if "tests" not in p.parts and not {".venv", "venv"} & set(p.parts)):
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            noms = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                [n.module or ""] if isinstance(n, ast.ImportFrom) else []
            fautes += [f"{f.name}:{n.lineno} {nom}" for nom in noms if nom.split(".")[0] in INTERDITS]
    assert not fautes, fautes
