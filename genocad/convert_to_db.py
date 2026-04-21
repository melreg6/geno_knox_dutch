"""
convert_to_db.py
Converts genocad MySQL .sql dump to a SQLite .db file.

Usage:
    python3 convert_to_db.py

Expects genocad.sql to be in the same directory.
Outputs genocad.db in the same directory.
"""

import re
import sqlite3
import os

SQL_PATH = os.path.join(os.path.dirname(__file__), 'genocad.sql')
DB_PATH  = os.path.join(os.path.dirname(__file__), 'genocad.db')


MANUAL_DDL = {
    'categories': """
        CREATE TABLE IF NOT EXISTS "categories" (
            "category_id"          INTEGER NOT NULL PRIMARY KEY,
            "letter"               TEXT    NOT NULL,
            "description"          TEXT    NOT NULL DEFAULT '',
            "grammar_id"           INTEGER,
            "icon_name"            TEXT,
            "genbank_qualifier_id" INTEGER,
            "description_text"     TEXT
        )
    """,
    'parts': """
        CREATE TABLE IF NOT EXISTS "parts" (
            "id"               INTEGER NOT NULL PRIMARY KEY,
            "part_id"          TEXT    NOT NULL DEFAULT '',
            "description"      TEXT    NOT NULL DEFAULT '',
            "segment"          TEXT,
            "user_id"          INTEGER NOT NULL DEFAULT 0,
            "description_text" TEXT,
            "last_modified"    TEXT,
            "date_created"     TEXT
        )
    """,
    'categories_parts': """
        CREATE TABLE IF NOT EXISTS "categories_parts" (
            "id"            INTEGER NOT NULL PRIMARY KEY,
            "part_id"       INTEGER NOT NULL,
            "category_id"   INTEGER NOT NULL,
            "user_id"       INTEGER NOT NULL,
            "last_modified" TEXT
        )
    """,
    'libraries': """
        CREATE TABLE IF NOT EXISTS "libraries" (
            "library_id"    INTEGER NOT NULL PRIMARY KEY,
            "user_id"       INTEGER NOT NULL DEFAULT 0,
            "name"          TEXT    NOT NULL DEFAULT '',
            "description"   TEXT,
            "last_modified" TEXT,
            "grammar_id"    INTEGER NOT NULL,
            "complete"      INTEGER
        )
    """,
    'library_part_join': """
        CREATE TABLE IF NOT EXISTS "library_part_join" (
            "library_id" INTEGER NOT NULL DEFAULT 0,
            "part_id"    TEXT    NOT NULL DEFAULT ''
        )
    """,
    'rules': """
        CREATE TABLE IF NOT EXISTS "rules" (
            "rule_id"     INTEGER NOT NULL PRIMARY KEY,
            "code"        TEXT,
            "category_id" INTEGER NOT NULL,
            "grammar_id"  INTEGER NOT NULL
        )
    """,
    'rule_transform': """
        CREATE TABLE IF NOT EXISTS "rule_transform" (
            "id"              INTEGER NOT NULL PRIMARY KEY,
            "rule_id"         INTEGER NOT NULL,
            "category_id"     INTEGER NOT NULL,
            "transform_order" INTEGER
        )
    """,
    'grammars': """
        CREATE TABLE IF NOT EXISTS "grammars" (
            "grammar_id"           INTEGER NOT NULL PRIMARY KEY,
            "name"                 TEXT,
            "description"          TEXT,
            "starting_category_id" INTEGER,
            "is_compilable"        INTEGER DEFAULT 1,
            "icon_set"             TEXT,
            "user_id"              INTEGER NOT NULL DEFAULT 0
        )
    """,
    'designs': """
        CREATE TABLE IF NOT EXISTS "designs" (
            "design_id"         INTEGER NOT NULL PRIMARY KEY,
            "name"              TEXT    NOT NULL DEFAULT '',
            "description"       TEXT,
            "design_json"       TEXT,
            "user_id"           INTEGER,
            "last_modification" TEXT,
            "terminals_json"    TEXT,
            "library_id"        INTEGER NOT NULL,
            "is_public"         INTEGER NOT NULL DEFAULT 0,
            "sequence"          TEXT,
            "is_validated"      INTEGER DEFAULT 0
        )
    """,
}


def load_all_tables(conn, content):
    for table, ddl in MANUAL_DDL.items():
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        conn.execute(ddl)
    conn.commit()
    print("  All tables created.")

    for table in MANUAL_DDL:
        pattern = rf"INSERT INTO `{table}`.*?;"
        matches = re.findall(pattern, content, re.DOTALL)
        ok = errors = 0
        for m in matches:
            stmt = re.sub(r'`', '"', m)
            try:
                conn.execute(stmt)
                ok += 1
            except Exception as e:
                errors += 1
        conn.commit()
        print(f"  {table}: {ok} inserts, {errors} errors")


def main():
    print(f"Reading {SQL_PATH} ...")
    with open(SQL_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    print("Creating and loading all tables ...")
    load_all_tables(conn, content)

    print("\n=== VERIFICATION ===")
    cur = conn.cursor()
    for t in ['categories', 'parts', 'categories_parts',
              'libraries', 'rules', 'rule_transform', 'grammars']:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            print(f"  {t}: {cur.fetchone()[0]} rows")
        except Exception as e:
            print(f"  {t}: ERROR - {e}")

    print("\nSample PRO parts (grammar 1237):")
    cur.execute("""
        SELECT p.part_id, p.description, c.letter
        FROM parts p
        JOIN categories_parts cp ON p.id = cp.part_id
        JOIN categories c ON cp.category_id = c.category_id
        WHERE c.letter = 'PRO' AND c.grammar_id = 1237
    """)
    for row in cur.fetchall():
        print(f"  {row}")

    print("\nGrammar rules:")
    cur.execute("SELECT rule_id, code, grammar_id FROM rules")
    for row in cur.fetchall():
        print(f"  {row}")

    conn.close()
    print(f"\nDone! Database saved to: {DB_PATH}")


if __name__ == '__main__':
    main()