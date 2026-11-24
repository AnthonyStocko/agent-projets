# agent-projets

Projets et connexions : registre des projets en lecture et tests de connexion, issus d'`agent-scrum-master`.

| | |
|---|---|
| IHM | `streamlit run app.py` → http://localhost:8504 (`.streamlit/config.toml`, 127.0.0.1) |
| API (lecture) | http://localhost:8512 : `/sante`, `/projets`, `/projets/<nom>` ; démarrée par l'IHM ou `python main.py --step api` (`AGENT_PROJETS_PORT`) |
| CLI | `python main.py --step api\|projets [--nom X]` |
| Registre | façade sans migration (`agent_socle.projets`) : projets Cucumber (`<AGENT_DATA_DIR>/.tmp/cucumber/<client>/projet.json`) et applications du manager (`commun.toml` de `SAVOYE_CONFIG_DIR`), sans fusion |
| Secrets | non déplacés : `.env` de `AGENT_DATA_DIR` et accès transmis par le manager ; l'API n'en sert aucun |
| Connexion OIDC | `secrets.toml` d'agent-scrum-master, lu sur place (`[secrets] files`) |
| Installation | `pip install -r requirements.txt` (socle `v0.2.0`) ; pendant le chantier `pip install -e ../agent-socle` |
| Tests | `python -m pytest -q` ; `test_independance.py` interdit tout import d'un autre agent |
