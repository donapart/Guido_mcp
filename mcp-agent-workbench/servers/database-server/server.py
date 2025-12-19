"""
Database MCP Server

Ein MCP-Server für SQL-Datenbank-Operationen.
Unterstützt PostgreSQL, MySQL, SQLite und SQL Server.
"""

from fastmcp import FastMCP
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Any
import os
import json

mcp = FastMCP("database-server")

# Aktive Verbindungen
_connections: dict[str, Any] = {}


def get_connection_string(db_type: str, **kwargs) -> str:
    """Erstellt einen Connection-String für verschiedene Datenbanken."""
    if db_type == "sqlite":
        return f"sqlite:///{kwargs.get('database', ':memory:')}"
    elif db_type == "postgresql":
        return (
            f"postgresql://{kwargs.get('user', 'postgres')}:"
            f"{kwargs.get('password', '')}@"
            f"{kwargs.get('host', 'localhost')}:"
            f"{kwargs.get('port', 5432)}/"
            f"{kwargs.get('database', 'postgres')}"
        )
    elif db_type == "mysql":
        return (
            f"mysql+pymysql://{kwargs.get('user', 'root')}:"
            f"{kwargs.get('password', '')}@"
            f"{kwargs.get('host', 'localhost')}:"
            f"{kwargs.get('port', 3306)}/"
            f"{kwargs.get('database', '')}"
        )
    elif db_type == "mssql":
        return (
            f"mssql+pyodbc://{kwargs.get('user', 'sa')}:"
            f"{kwargs.get('password', '')}@"
            f"{kwargs.get('host', 'localhost')}:"
            f"{kwargs.get('port', 1433)}/"
            f"{kwargs.get('database', 'master')}?"
            f"driver=ODBC+Driver+17+for+SQL+Server"
        )
    else:
        raise ValueError(f"Unbekannter Datenbanktyp: {db_type}")


# ============================================================================
# CONNECTION TOOLS
# ============================================================================

@mcp.tool
def connect_database(
    connection_name: str,
    db_type: str,
    host: str = "localhost",
    port: int = 0,
    database: str = "",
    user: str = "",
    password: str = ""
) -> dict:
    """
    Verbindet zu einer Datenbank.
    
    Args:
        connection_name: Eindeutiger Name für diese Verbindung
        db_type: Datenbanktyp ("sqlite", "postgresql", "mysql", "mssql")
        host: Hostname (default: localhost)
        port: Port (default: je nach DB-Typ)
        database: Datenbankname oder Dateipfad (bei SQLite)
        user: Benutzername
        password: Passwort
    
    Returns:
        Verbindungsstatus
    """
    try:
        # Default-Ports
        if port == 0:
            port = {"postgresql": 5432, "mysql": 3306, "mssql": 1433}.get(db_type, 0)
        
        conn_str = get_connection_string(
            db_type,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        engine = create_engine(conn_str)
        
        # Verbindung testen
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        _connections[connection_name] = {
            "engine": engine,
            "db_type": db_type,
            "database": database,
        }
        
        return {
            "success": True,
            "connection_name": connection_name,
            "db_type": db_type,
            "database": database,
        }
    except Exception as e:
        return {"error": f"Verbindungsfehler: {str(e)}"}


@mcp.tool
def disconnect_database(connection_name: str) -> dict:
    """
    Trennt eine Datenbankverbindung.
    
    Args:
        connection_name: Name der Verbindung
    
    Returns:
        Status
    """
    if connection_name not in _connections:
        return {"error": f"Verbindung '{connection_name}' nicht gefunden"}
    
    try:
        _connections[connection_name]["engine"].dispose()
        del _connections[connection_name]
        return {"success": True, "message": f"Verbindung '{connection_name}' getrennt"}
    except Exception as e:
        return {"error": f"Fehler beim Trennen: {str(e)}"}


@mcp.tool
def list_connections() -> list[dict]:
    """
    Listet alle aktiven Datenbankverbindungen.
    
    Returns:
        Liste der Verbindungen
    """
    return [
        {
            "name": name,
            "db_type": info["db_type"],
            "database": info["database"],
        }
        for name, info in _connections.items()
    ]


# ============================================================================
# QUERY TOOLS
# ============================================================================

@mcp.tool
def execute_query(
    connection_name: str,
    query: str,
    params: dict = {}
) -> dict:
    """
    Führt eine SQL-Query aus (SELECT, INSERT, UPDATE, DELETE).
    
    Args:
        connection_name: Name der Verbindung
        query: SQL-Query
        params: Parameter für prepared statements (optional)
    
    Returns:
        Query-Ergebnis
    """
    if connection_name not in _connections:
        return {"error": f"Verbindung '{connection_name}' nicht gefunden"}
    
    try:
        engine = _connections[connection_name]["engine"]
        
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            
            # Für SELECT-Queries
            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                }
            else:
                # Für INSERT/UPDATE/DELETE
                conn.commit()
                return {
                    "success": True,
                    "affected_rows": result.rowcount,
                }
    except SQLAlchemyError as e:
        return {"error": f"SQL-Fehler: {str(e)}"}


@mcp.tool
def execute_script(connection_name: str, script: str) -> dict:
    """
    Führt ein SQL-Skript mit mehreren Statements aus.
    
    Args:
        connection_name: Name der Verbindung
        script: SQL-Skript (mehrere Statements, getrennt durch ;)
    
    Returns:
        Ausführungsstatus
    """
    if connection_name not in _connections:
        return {"error": f"Verbindung '{connection_name}' nicht gefunden"}
    
    try:
        engine = _connections[connection_name]["engine"]
        results = []
        
        with engine.connect() as conn:
            # Statements aufteilen und ausführen
            statements = [s.strip() for s in script.split(";") if s.strip()]
            
            for stmt in statements:
                result = conn.execute(text(stmt))
                results.append({
                    "statement": stmt[:50] + "..." if len(stmt) > 50 else stmt,
                    "affected_rows": result.rowcount if not result.returns_rows else 0,
                })
            
            conn.commit()
        
        return {
            "success": True,
            "statements_executed": len(results),
            "results": results,
        }
    except SQLAlchemyError as e:
        return {"error": f"SQL-Fehler: {str(e)}"}


# ============================================================================
# SCHEMA TOOLS
# ============================================================================

@mcp.tool
def list_tables(connection_name: str, schema: str = None) -> list[str]:
    """
    Listet alle Tabellen in der Datenbank.
    
    Args:
        connection_name: Name der Verbindung
        schema: Schema-Name (optional)
    
    Returns:
        Liste der Tabellennamen
    """
    if connection_name not in _connections:
        return [f"Fehler: Verbindung '{connection_name}' nicht gefunden"]
    
    try:
        engine = _connections[connection_name]["engine"]
        inspector = inspect(engine)
        return inspector.get_table_names(schema=schema)
    except Exception as e:
        return [f"Fehler: {str(e)}"]


@mcp.tool
def describe_table(connection_name: str, table_name: str, schema: str = None) -> dict:
    """
    Beschreibt die Struktur einer Tabelle.
    
    Args:
        connection_name: Name der Verbindung
        table_name: Tabellenname
        schema: Schema-Name (optional)
    
    Returns:
        Tabellenstruktur mit Spalten, Keys etc.
    """
    if connection_name not in _connections:
        return {"error": f"Verbindung '{connection_name}' nicht gefunden"}
    
    try:
        engine = _connections[connection_name]["engine"]
        inspector = inspect(engine)
        
        columns = []
        for col in inspector.get_columns(table_name, schema=schema):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default")) if col.get("default") else None,
            })
        
        pk = inspector.get_pk_constraint(table_name, schema=schema)
        fks = inspector.get_foreign_keys(table_name, schema=schema)
        indexes = inspector.get_indexes(table_name, schema=schema)
        
        return {
            "table_name": table_name,
            "columns": columns,
            "primary_key": pk.get("constrained_columns", []),
            "foreign_keys": [
                {
                    "columns": fk["constrained_columns"],
                    "references": f"{fk['referred_table']}.{fk['referred_columns']}",
                }
                for fk in fks
            ],
            "indexes": [
                {
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx.get("unique", False),
                }
                for idx in indexes
            ],
        }
    except Exception as e:
        return {"error": f"Fehler: {str(e)}"}


@mcp.tool
def get_table_sample(
    connection_name: str, 
    table_name: str, 
    limit: int = 10
) -> dict:
    """
    Holt Beispieldaten aus einer Tabelle.
    
    Args:
        connection_name: Name der Verbindung
        table_name: Tabellenname
        limit: Anzahl Zeilen (default: 10)
    
    Returns:
        Beispieldaten
    """
    return execute_query(
        connection_name,
        f"SELECT * FROM {table_name} LIMIT {limit}"
    )


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("db://connections")
def get_connections_info() -> str:
    """Liste aller aktiven Datenbankverbindungen"""
    return json.dumps(list_connections(), indent=2)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    import io
    
    # Fix für Windows-Konsole und Unicode
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    mcp.run()
