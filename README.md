# GenoCAD → Knox Grammar Rule Engine

### EC552 Project — `geno_knox_dutch` (finalized)

A pipeline and web UI that extracts construct grammar from a GenoCAD database, translates it into Goldbar rules, submits those rules to a running Knox server, and enumerates the valid designs Knox returns.

---

## What It Does

1. **Converts** the GenoCAD MySQL dump (`genocad.sql`) into a portable SQLite database (`genocad.db`).
2. **Loads** parts and categories out of the SQLite DB, filtering structural/non-biological symbols (brackets, `S`, `CAS`, `TP`, etc.).
3. **Serves** a Flask web UI that lists available parts by category and shows enumerated designs returned by Knox.
4. **Proxies** browser requests to a locally running Knox server (`http://localhost:8080`) so the front-end can hit Knox endpoints (`/rules`, `/designSpace/enumerate`, …) without CORS issues.

---

## Repository Contents

```
geno_knox_dutch/
│
├── app.py                       Flask web app (routes "/" and "/knox/<path>")
├── config.py                    KNOX_URL, PORT, DB path, category filter list
├── db.py                        load_parts() — joins categories ↔ parts, cleans sequences
├── knox_proxy.py                Thin HTTP proxy from Flask to the Knox server
│
├── convert_to_db.py             MySQL .sql dump → SQLite .db converter
├── genocad.sql                  Original GenoCAD MySQL dump (input)
├── genocad.db                   Converted SQLite database (output)
│
├── testing_things.py            Scratch script for direct MySQL inspection
│
├── test_db_conversion.py        Row-count checks against expected values
├── test_sequence_integrity.py   Verifies DNA sequence lengths survived conversion
├── test_goldbar_validation.py   Validates Goldbar expressions for 1- and N-cassette designs
├── test_known_designs.py        Checks against published "Switch LacI/TetR" design
├── test_integration.py          End-to-end run of all the checks above with a summary
│
├── requirements.txt
└── README.md                    ← this file
```

> **Note on the test files:** several tests import from `grammar_rule_engine.genocad_grammar_extractor` and `grammar_rule_engine.goldbar_translator`. Those modules live in a sibling `grammar_rule_engine/` package that the tests expect to be on the Python path. If you're running the tests, make sure that package is present alongside this repo (the imports use `sys.path.append('..')`).

---

## Pipeline Flow

```
genocad.sql  (MySQL dump)
      ↓  convert_to_db.py
genocad.db  (SQLite)
      ↓  db.load_parts()
parts grouped by category
      ↓  grammar_rule_engine.extract / translate_all
Goldbar expression  (e.g. "PRO . RBS . CDS . TER")
      ↓  POST /rules  via knox_proxy
Knox server
      ↓  GET /designSpace/enumerate
Valid designs rendered in the Flask UI
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Build the SQLite database

The Flask app reads from `genocad.db`. If you only have the SQL dump, generate the DB first:

```bash
python3 convert_to_db.py
```

This drops and recreates `categories`, `parts`, `categories_parts`, `libraries`, `library_part_join`, `rules`, `rule_transform`, `grammars`, and `designs`, then prints row counts and a sample of `PRO` parts for grammar 1237.

### 3. Start a Knox server

The proxy expects Knox running at `http://localhost:8080` (configurable via `KNOX_URL` in `config.py`). Start your Knox instance before launching the app — the index route will fail to populate designs otherwise.

### 4. Run the Flask app

```bash
python3 app.py
```

The UI is served at `http://localhost:5050`. The port is set in `config.py`.

---

## Configuration (`config.py`)

| Setting        | Default                                  | Purpose                                                |
| -------------- | ---------------------------------------- | ------------------------------------------------------ |
| `KNOX_URL`     | `http://localhost:8080`                  | Base URL of the Knox server the proxy forwards to.     |
| `PORT`         | `5050`                                   | Port the Flask app listens on.                         |
| `DB_PATH`      | `<parent>/genocad/genocad.db`            | SQLite database loaded by `db.load_parts()`.           |
| `SKIP_LETTERS` | `S`, `[`, `]`, `(`, `)`, `{`, `}`, `CAS`, `TP` | Category letters excluded when loading parts. |

---

## Routes

| Route                     | Method     | Description                                                                 |
| ------------------------- | ---------- | --------------------------------------------------------------------------- |
| `/`                       | `GET`      | Renders `index.html` with parts grouped by category and the design list returned from Knox's enumerate endpoint. |
| `/knox/<path:endpoint>`   | `GET/POST` | Generic proxy — forwards to `KNOX_URL/<endpoint>` preserving query string, body, and content type. |

---

## Tests

Each test runs as a standalone script. From the project root:

```bash
python3 test_db_conversion.py        # row-count validation
python3 test_sequence_integrity.py   # DNA sequence length checks
python3 test_goldbar_validation.py   # Goldbar expression validation
python3 test_known_designs.py        # Switch LacI/TetR known-design check
python3 test_integration.py          # all of the above + a summary
```

The integration test currently expects:

- 24 categories, 54 parts, 54 category-part joins, 2 libraries, 8 rules, 20 rule transforms, 2 grammars
- Specific sequence lengths for `a069g`, `a069h`, `a069i`, `a069m`, `a069n`
- Single-cassette Goldbar `PRO . RBS . CDS . TER`
- Multi-cassette Goldbar `one-or-more(PRO . RBS . CDS . TER)`
- Switch LacI/TetR (design 673) and Repressilator (design 674) parts present in the right categories

---

## Team

Varsha Athreya · Melissa Regalado · Paulina Garcia · Denalda Gashi
