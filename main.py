"""CLI d'agent-projets.

  python main.py --step api [--port 8512]   sert l'API en lecture (registre des projets)
  python main.py --step projets [--nom X]   affiche le registre (JSON)
"""
import argparse
import json
import sys

from agent_socle import projets


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Agent Projets et connexions")
    parser.add_argument("--step", choices=["api", "projets"], required=True,
                        help="api : sert l'API en lecture sur AGENT_PROJETS_PORT (8512) ; projets : affiche le registre")
    parser.add_argument("--port", type=int, default=None, help="api : port d'écoute (défaut 8512)")
    parser.add_argument("--nom", default="", help="projets : un seul projet")
    args = parser.parse_args(argv)
    if args.step == "api":
        import api
        srv = api.serveur(args.port)
        print(f"[PROJETS] API en lecture sur http://127.0.0.1:{srv.server_port}")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    donnee = projets.registre()
    if args.nom:
        donnee = donnee.get(args.nom)
        if donnee is None:
            print(f"[PROJETS] projet inconnu : {args.nom}", file=sys.stderr)
            return 1
    print(json.dumps(donnee, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
