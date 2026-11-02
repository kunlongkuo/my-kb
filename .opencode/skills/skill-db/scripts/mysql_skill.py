#!/usr/bin/env python3
"""Local MySQL helper for the OpenCode skill-db skill.

Commands:
  verify                   Load config and test connection.
  schema                   Show tables/columns for the active database.
  tables                   Print the editable tables.json map.
  run --sql SQL            Execute one allowed SQL statement.
  batch --sql SQL [...]    Execute multiple allowed statements on one connection.

The helper intentionally blocks schema-destructive SQL.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pymysql
from pymysql.cursors import DictCursor

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SETUP = SKILL_DIR / "setup.json"
DEFAULT_TABLES = SKILL_DIR / "tables.json"

FORBIDDEN_PATTERNS = [
    r"\bdrop\s+database\b",
    r"\bdrop\s+table\b",
    r"\btruncate\s+table\b",
    r"\balter\s+table\b",
    r"\bcreate\s+table\b",
    r"\brename\s+table\b",
]

ALLOWED_PREFIXES = (
    "select",
    "with",
    "insert",
    "update",
    "delete",
    "begin",
    "start transaction",
    "commit",
    "rollback",
    "show",
    "describe",
    "desc",
    "explain",
    "use",
    "set",
)


@dataclass
class Config:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306
    charset: str = "utf8mb4"
    autocommit: bool = False


class SkillDBError(RuntimeError):
    pass


def read_json(path: Path) -> Any:
    if not path.exists():
        raise SkillDBError(f"Missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise SkillDBError(f"Invalid JSON in {path}: {exc}") from exc


def load_config(path: Path) -> Config:
    data = read_json(path)
    try:
        return Config(
            host=data["host"],
            user=data["user"],
            password=data["password"],
            database=data["database"],
            port=int(data.get("port", 3306)),
            charset=data.get("charset", "utf8mb4"),
            autocommit=bool(data.get("autocommit", False)),
        )
    except KeyError as exc:
        raise SkillDBError(f"Missing required config key: {exc.args[0]}") from exc


def normalize_sql(sql: str) -> str:
    sql = sql.strip()
    sql = re.sub(r"^\s*(?:--[^\n]*\n|/\*.*?\*/\s*)+", "", sql, flags=re.S)
    return sql.strip()


def is_allowed_sql(sql: str) -> tuple[bool, str]:
    compact = normalize_sql(sql)
    low = compact.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, low, flags=re.I):
            return False, f"Blocked forbidden SQL: {pattern}"
    if not any(low.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return False, "Blocked SQL: statement type is not in the allowed set"
    return True, "ok"


def split_prefix(sql: str) -> str:
    compact = normalize_sql(sql)
    return compact.split(None, 1)[0].lower() if compact else ""


def connect(cfg: Config):
    return pymysql.connect(
        host=cfg.host,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        port=cfg.port,
        charset=cfg.charset,
        autocommit=cfg.autocommit,
        cursorclass=DictCursor,
    )


def fetch_schema(conn) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute("SELECT DATABASE() AS database_name")
        current_db = cur.fetchone()["database_name"]
        cur.execute(
            """
            SELECT TABLE_NAME
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            ORDER BY TABLE_NAME
            """
        )
        tables = [row["TABLE_NAME"] for row in cur.fetchall()]

        details = []
        for table in tables:
            cur.execute(
                """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA, COLUMN_COMMENT, ORDINAL_POSITION
                FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = %s
                ORDER BY ORDINAL_POSITION
                """,
                (table,),
            )
            cols = [
                {
                    "name": row["COLUMN_NAME"],
                    "type": row["DATA_TYPE"],
                    "nullable": row["IS_NULLABLE"] == "YES",
                    "key": row["COLUMN_KEY"],
                    "default": row["COLUMN_DEFAULT"],
                    "extra": row["EXTRA"],
                    "comment": row["COLUMN_COMMENT"],
                }
                for row in cur.fetchall()
            ]
            details.append({"table": table, "columns": cols})
    return {"database": current_db, "tables": details}


def merge_tables_map(schema: dict[str, Any], tables_map: dict[str, Any] | None) -> dict[str, Any]:
    indexed = {}
    if isinstance(tables_map, dict):
        for item in tables_map.get("tables", []):
            if isinstance(item, dict) and item.get("name"):
                indexed[item["name"]] = item

    out_tables = []
    for item in schema["tables"]:
        meta = indexed.get(item["table"], {})
        out_tables.append(
            {
                "name": item["table"],
                "meaning": meta.get("meaning", ""),
                "description": meta.get("description", ""),
                "fields": meta.get("fields", []),
                "columns": item["columns"],
            }
        )
    return {"database": schema["database"], "tables": out_tables}


def execute_sql(conn, sql: str) -> dict[str, Any]:
    ok, reason = is_allowed_sql(sql)
    if not ok:
        raise SkillDBError(reason)

    statement = normalize_sql(sql)
    prefix = split_prefix(statement)
    with conn.cursor() as cur:
        affected = cur.execute(statement)
        if prefix in {"select", "with", "show", "describe", "desc", "explain"}:
            rows = cur.fetchall()
            return {"statement": statement, "kind": "resultset", "rows": rows, "row_count": len(rows)}
        return {"statement": statement, "kind": "write", "affected_rows": affected}


def run_batch(conn, statements: Iterable[str]) -> list[dict[str, Any]]:
    results = []
    with conn.cursor() as cur:
        for sql in statements:
            ok, reason = is_allowed_sql(sql)
            if not ok:
                raise SkillDBError(reason)
            statement = normalize_sql(sql)
            prefix = split_prefix(statement)
            affected = cur.execute(statement)
            if prefix in {"select", "with", "show", "describe", "desc", "explain"}:
                rows = cur.fetchall()
                results.append({"statement": statement, "kind": "resultset", "rows": rows, "row_count": len(rows)})
            else:
                results.append({"statement": statement, "kind": "write", "affected_rows": affected})
    return results


def cmd_verify(args) -> int:
    cfg = load_config(args.setup)
    tables_map = read_json(args.tables) if args.tables.exists() else None
    conn = connect(cfg)
    try:
        schema = fetch_schema(conn)
        payload = merge_tables_map(schema, tables_map)
        print(json.dumps({
            "ok": True,
            "config": {"host": cfg.host, "user": cfg.user, "database": cfg.database, "port": cfg.port},
            "schema": payload,
        }, ensure_ascii=False, indent=2, default=str))
    finally:
        conn.close()
    return 0


def cmd_schema(args) -> int:
    cfg = load_config(args.setup)
    tables_map = read_json(args.tables) if args.tables.exists() else None
    conn = connect(cfg)
    try:
        payload = merge_tables_map(fetch_schema(conn), tables_map)
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    finally:
        conn.close()
    return 0


def cmd_tables(args) -> int:
    data = read_json(args.tables)
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_run(args) -> int:
    cfg = load_config(args.setup)
    conn = connect(cfg)
    try:
        result = execute_sql(conn, args.sql)
        if conn.get_autocommit():
            pass
        elif result["kind"] == "write":
            conn.commit()
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    except Exception:
        if not conn.get_autocommit():
            conn.rollback()
        raise
    finally:
        conn.close()
    return 0


def cmd_batch(args) -> int:
    cfg = load_config(args.setup)
    conn = connect(cfg)
    try:
        results = run_batch(conn, args.sql)
        if not conn.get_autocommit():
            conn.commit()
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2, default=str))
    except Exception:
        if not conn.get_autocommit():
            conn.rollback()
        raise
    finally:
        conn.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Local MySQL helper for skill-db")
    p.add_argument("--setup", type=Path, default=DEFAULT_SETUP, help="Path to setup.json")
    p.add_argument("--tables", type=Path, default=DEFAULT_TABLES, help="Path to tables.json")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("verify", help="Load config and test connection")
    sub.add_parser("schema", help="Show database tables and columns")
    sub.add_parser("tables", help="Print tables.json")

    run = sub.add_parser("run", help="Execute one SQL statement")
    run.add_argument("--sql", required=True, help="SQL to execute")

    batch = sub.add_parser("batch", help="Execute multiple SQL statements on one connection")
    batch.add_argument("--sql", action="append", required=True, help="SQL to execute (repeatable)")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "verify": cmd_verify,
        "schema": cmd_schema,
        "tables": cmd_tables,
        "run": cmd_run,
        "batch": cmd_batch,
    }
    try:
        return handlers[args.command](args)
    except SkillDBError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
