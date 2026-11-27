"""IHM d'agent-projets (port 8504) : registre des projets (lecture) et tests de connexion.

Le registre est une façade sans migration (agent_socle.projets) ; les tests de connexion sont ceux de la page
Configuration d'agent-scrum-master, repris tels quels. L'API en lecture (8512) est démarrée en fond si elle ne tourne
pas déjà. Les secrets restent dans le .env de AGENT_DATA_DIR (et ceux que transmet le manager).
"""
import logging
import os

import streamlit as st
from dotenv import load_dotenv

import api
from agent_socle import auth_tools, config_commune, knowledge_tools, mcp_servers, projets
from agent_socle.chemins import DATA_DIR
from agent_socle.db_tools import test_connection

st.set_page_config(page_title="Projets et connexions", page_icon="🗂️", layout="wide")

# Même chargement que les autres agents : .env de AGENT_DATA_DIR, puis les accès transmis par le manager
ENV_PATH = os.path.join(DATA_DIR, ".env")
os.environ.setdefault("AGENT_SHELL_CLAUDE_CONFIG_DIR", os.environ.get("CLAUDE_CONFIG_DIR", ""))
logging.getLogger("dotenv.main").setLevel(logging.ERROR)
load_dotenv(ENV_PATH, override=True)
config_commune.reappliquer()
if not os.getenv("CLAUDE_CONFIG_DIR", "").strip():
    os.environ["CLAUDE_CONFIG_DIR"] = os.environ["AGENT_SHELL_CLAUDE_CONFIG_DIR"]

# Connexion OIDC (AGENT_AUTH) : rien n'est affiché ni exécuté avant elle
CONNECTED = auth_tools.require_login(st)


@st.cache_resource
def api_en_fond():
    """API en lecture (8512), une fois par serveur Streamlit ; None si elle tourne déjà ailleurs."""
    return api.demarrer_en_fond()


def render_registre() -> None:
    """Registre des projets : projets Cucumber et applications du manager, sans fusion (lecture seule)."""
    registre = projets.registre()
    st.subheader("🗂️ Projets")
    st.caption("Lecture seule : projets Cucumber (réglages d'agent-cucumber) et applications du manager "
               f"(commun.toml de {projets.dossier_manager()}). API : {projets.api()}/projets")
    if not registre:
        st.info("Aucun projet connu.", icon=":material/info:")
        return
    st.dataframe([{"Projet": nom,
                   "Cucumber": "oui" if p["cucumber"] is not None else "",
                   "Dépôt client": (p["cucumber"] or {}).get("client_repo", ""),
                   "Application (manager)": "oui" if p["application"] is not None else "",
                   "Projet Jira": (p["application"] or {}).get("jira_projet", ""),
                   "Job Jenkins": (p["application"] or {}).get("jenkins_job", "")}
                  for nom, p in registre.items()], hide_index=True, width="stretch")
    choix = st.selectbox("Détail", list(registre), index=None, placeholder="Choisir un projet", key="projet_detail")
    if choix:
        st.json(registre[choix])


def render_groundcover_mcp() -> None:
    """Serveurs MCP : état de Groundcover, « Se connecter à Groundcover » (console Claude Code) et « Tester »."""
    state = mcp_servers.status()
    label = mcp_servers.STATUS_LABELS.get(state["statut"], state["statut"])
    with st.container(horizontal=True, vertical_alignment="center"):
        connect_clicked = st.button("Se connecter à Groundcover", icon=":material/login:",
                                    disabled=not mcp_servers.configured(), key="groundcover_mcp_login")
        test_clicked = st.button("Tester", icon=":material/lan:", disabled=not mcp_servers.configured(),
                                 key="groundcover_mcp_test")
        st.caption(f"Groundcover (MCP) : {label}" + (f" — {state['date'].replace('T', ' ')}" if state.get("date") else "")
                   + (f" — {state['message']}" if state.get("message") else "")
                   + (f" — {len(mcp_servers.allowed_tools())} outil(s) de lecture autorisé(s)"
                      if state["statut"] in ("connecté", "désactivé") and mcp_servers.allowed_tools() else ""))
    if connect_clicked:
        try:
            st.info(mcp_servers.open_login_console(), icon=":material/login:")
        except (OSError, ValueError) as e:
            st.error(f"Console non ouverte : {e}", icon=":material/error:")
    if test_clicked:
        with st.spinner("Test de Groundcover (démarrage de Claude Code, puis un appel de lecture)…"):
            try:
                result = mcp_servers.test_connection()
            except ValueError as e:
                result = {"statut": "erreur", "message": str(e)}
        message = f"Groundcover : {mcp_servers.STATUS_LABELS.get(result['statut'], result['statut'])}" + (
            f" — {result['message']}" if result.get("message") else "")
        if result["statut"] == "connecté":
            st.success(message, icon=":material/check_circle:")
        elif result["statut"] == "expiré":
            st.warning(message + " Cliquez « Se connecter à Groundcover ».", icon=":material/key_off:")
        else:
            st.error(message, icon=":material/error:")


def render_tests_connexion() -> None:
    """Tests de connexion (repris de la page Configuration d'agent-scrum-master, inchangés)."""
    # Hors formulaire : teste la configuration base déjà enregistrée dans le .env
    with st.container(horizontal=True, vertical_alignment="center"):
        test_db_clicked = st.button("Tester la connexion", icon=":material/lan:")
        st.caption("Teste la connexion base enregistrée (et le schéma DB_SCHEMA s'il est renseigné).")
    if test_db_clicked:
        with st.spinner("Connexion à la base…"):
            db_ok, db_message = test_connection(os.getenv("DB_SCHEMA", "").strip(), profile="")
        if db_ok:
            st.success(db_message, icon=":material/check_circle:")
        else:
            st.error(db_message, icon=":material/error:")
    if os.getenv("CUCUMBER_DB_HOST", "").strip() or os.getenv("CUCUMBER_DB_NAME", "").strip():
        if st.button("Tester la base Cucumber", icon=":material/lan:"):
            with st.spinner("Connexion à la base Cucumber…"):
                db_ok, db_message = test_connection(os.getenv("CUCUMBER_DB_SCHEMA", "").strip(), profile="cucumber")
            if db_ok:
                st.success(db_message, icon=":material/check_circle:")
            else:
                st.error(db_message, icon=":material/error:")

    # Hors formulaire : teste les logs groundcover enregistrés (clé, filtre de l'environnement de test)
    if os.getenv("GROUNDCOVER_API_KEY", "").strip():
        if st.button("Tester groundcover", icon=":material/lan:", key="test_groundcover"):
            from datetime import datetime as _dt, timedelta as _td, timezone as _tz
            from agent_socle import groundcover_tools
            try:
                now = _dt.now(_tz.utc)
                with st.spinner("Lecture des logs groundcover…"):
                    rows = groundcover_tools.search(now - _td(minutes=15), now, limit=3)
                st.success(f"groundcover joignable : {len(rows)} ligne(s) sur les 15 dernières minutes avec le filtre "
                           f"« {groundcover_tools.config()['filter']} »."
                           + (f" Dernière : {groundcover_tools.format_row(rows[-1])[:200]}" if rows else
                              " Aucune ligne : filtre trop strict, ou environnement inactif."),
                           icon=":material/check_circle:")
            except groundcover_tools.GroundcoverError as e:
                st.error(str(e), icon=":material/error:")

    # Hors formulaire : connexion (navigateur, dans Claude Code) et test du serveur MCP Groundcover enregistré
    render_groundcover_mcp()

    # Hors formulaire : teste le répertoire partagé enregistré (existence, écriture, temps d'accès)
    with st.container(horizontal=True, vertical_alignment="center"):
        test_knowledge_clicked = st.button("Tester le répertoire partagé", icon=":material/folder_shared:",
                                           disabled=not knowledge_tools.enabled())
        st.caption(f"Teste AGENT_KNOWLEDGE_DIR enregistré : {knowledge_tools.knowledge_dir()}"
                   if knowledge_tools.enabled() else "AGENT_KNOWLEDGE_DIR vide : connaissances partagées désactivées.")
    if test_knowledge_clicked:
        with st.spinner("Test du répertoire partagé…"):
            knowledge_test = knowledge_tools.test_dir()
        (st.success if knowledge_test["ok"] else st.error)(
            knowledge_test["message"], icon=":material/check_circle:" if knowledge_test["ok"] else ":material/error:")
        for step, step_ok, detail in knowledge_test["etapes"]:
            st.caption(f"{'✅' if step_ok else '❌'} {step} : {detail}")


st.title("🗂️ Projets et connexions")
if CONNECTED:
    st.caption(f"Connecté : {auth_tools.label(CONNECTED)}")
api_en_fond()
render_registre()
st.divider()
st.subheader("🔌 Tests de connexion")
render_tests_connexion()
