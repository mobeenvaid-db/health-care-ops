"""Dual-mode auth: local profile vs Databricks App service principal."""

import os
from databricks.sdk import WorkspaceClient

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))

# Lakebase connection info - DB_ vars from app resource, PG vars as fallback
LAKEBASE_HOST = os.environ.get("DB_HOST") or os.environ.get(
    "PGHOST", "localhost"
)
_port_str = os.environ.get("DB_PORT") or os.environ.get("PGPORT", "5432")
LAKEBASE_PORT = int(_port_str) if _port_str.isdigit() else 5432
LAKEBASE_DATABASE = os.environ.get("DB_NAME") or os.environ.get("PGDATABASE", "care_ops_db")
LAKEBASE_USER = os.environ.get("DB_USER") or os.environ.get("PGUSER", "")
LAKEBASE_PASSWORD = os.environ.get("DB_PASSWORD", "")

DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "")
DATABRICKS_PROFILE = os.environ.get("DATABRICKS_CONFIG_PROFILE", "DEFAULT")


def get_workspace_client() -> WorkspaceClient:
    if IS_DATABRICKS_APP:
        return WorkspaceClient()
    return WorkspaceClient(profile=DATABRICKS_PROFILE)


def get_oauth_token() -> str:
    w = get_workspace_client()
    auth_headers = w.config.authenticate()
    if auth_headers and "Authorization" in auth_headers:
        return auth_headers["Authorization"].replace("Bearer ", "")
    if w.config.token:
        return w.config.token
    raise RuntimeError("Could not obtain OAuth token")


def get_workspace_host() -> str:
    if IS_DATABRICKS_APP:
        host = os.environ.get("DATABRICKS_HOST", "")
        if host and not host.startswith("http"):
            host = f"https://{host}"
        return host
    w = get_workspace_client()
    return w.config.host
