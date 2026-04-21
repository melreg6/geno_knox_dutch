import json
import os
import sqlite3
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

# ── config ────────────────────────────────────────────────────────────────────

KNOX_URL = "http://localhost:8080"
PORT     = 5050
DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "geno_knox_dutch", "genocad.db") # Change this to the directory where the genocad database is

SKIP_LETTERS = {"S", "[", "]", "(", ")", "{", "}", "CAS", "TP"}

# ── load parts from genocad.db ────────────────────────────────────────────────

def load_parts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT c.description as cat, c.letter, p.part_id as id, p.description as desc
        FROM categories c
        JOIN categories_parts cp ON c.category_id = cp.category_id
        JOIN parts p ON p.id = cp.part_id
        WHERE c.letter NOT IN ('S','[',']','(',')','{{','}}','CAS','TP')
        ORDER BY c.description, p.part_id
    """)
    parts = {}
    for row in cur.fetchall():
        if row["letter"] in SKIP_LETTERS:
            continue
        parts.setdefault(row["cat"], []).append({
            "id": row["id"],
            "desc": row["desc"] or ""
        })
    conn.close()
    return parts

# ── request handler ───────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    html_content = None  # set before server starts

    def log_message(self, format, *args):
        print(f"  {self.path}  →  {args[1] if len(args) > 1 else ''}")

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(Handler.html_content.encode())

        elif path.startswith("/knox"):
            self.proxy_to_knox("GET", path[5:], self.path[5:])

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = self.path
        if path.startswith("/knox"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            self.proxy_to_knox("POST", path[5:], path[5:], body,
                               self.headers.get("Content-Type", ""))
        else:
            self.send_response(404)
            self.end_headers()

    def proxy_to_knox(self, method, knox_path, full_path, body=None, content_type=""):
        # rebuild the full Knox URL including query string
        qs = self.path[5 + len(knox_path.split("?")[0]):]
        url = KNOX_URL + full_path

        headers = {}
        if content_type:
            headers["Content-Type"] = content_type

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
                self.send_response(resp.status)
                ct = resp.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ct)
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Could not reach Knox: {e}".encode())

# ── build the HTML page ───────────────────────────────────────────────────────

def build_html(parts):
    parts_json = json.dumps(parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GenoCAD - Knox Design Explorer</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e2e8f0; height: 100vh; display: flex; flex-direction: column; }}
  header {{ padding: 16px 28px; background: #1a1d27; border-bottom: 1px solid #2a2e3f; }}
  header h1 {{ font-size: 1.2rem; color: #fff; }}
  header p  {{ color: #8892a4; font-size: 12px; margin-top: 3px; }}
  main {{ display: grid; grid-template-columns: 260px 260px 1fr; flex: 1; overflow: hidden; }}
  .col {{ padding: 16px; border-right: 1px solid #2a2e3f; overflow-y: auto; }}
  .col:last-child {{ border-right: none; }}
  h2 {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #8892a4; margin-bottom: 14px; }}
  .cat-name {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: #4f8ef7; border-bottom: 1px solid #2a2e3f; padding-bottom: 3px; margin: 12px 0 6px; }}
  .cat-name:first-of-type {{ margin-top: 0; }}
  .part {{ display: flex; align-items: flex-start; gap: 7px; padding: 4px 5px; border-radius: 4px; cursor: pointer; font-size: 12px; }}
  .part:hover {{ background: rgba(79,142,247,.07); }}
  .part input {{ accent-color: #4f8ef7; margin-top: 2px; }}
  .pid {{ font-weight: 600; }}
  .pdesc {{ color: #8892a4; font-size: 11px; }}
  .lbl {{ display: block; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: #8892a4; margin-bottom: 5px; }}
  .cass-row {{ display: flex; gap: 6px; margin-bottom: 14px; }}
  .cass {{ flex: 1; padding: 6px; border: 1px solid #2a2e3f; border-radius: 5px; background: #1a1d27; color: #8892a4; font-weight: 600; font-size: 13px; cursor: pointer; }}
  .cass.on {{ border-color: #4f8ef7; background: rgba(79,142,247,.1); color: #4f8ef7; }}
  input[type=text], input[type=number] {{ width: 100%; padding: 7px 9px; background: #1a1d27; border: 1px solid #2a2e3f; border-radius: 5px; color: #e2e8f0; font-size: 13px; margin-bottom: 12px; }}
  input:focus {{ outline: 2px solid #4f8ef7; border-color: transparent; }}
  hr {{ border: none; border-top: 1px solid #2a2e3f; margin: 8px 0 14px; }}
  .goldbar {{ background: #0d1117; border: 1px solid #2a2e3f; border-radius: 5px; padding: 9px 11px; font-family: monospace; font-size: 11px; color: #34d399; white-space: pre-wrap; word-break: break-all; min-height: 40px; margin-bottom: 12px; }}
  #btn {{ width: 100%; padding: 10px; background: #4f8ef7; color: #fff; font-size: 14px; font-weight: 700; border: none; border-radius: 7px; cursor: pointer; }}
  #btn:disabled {{ opacity: .35; cursor: not-allowed; }}
  #btn:not(:disabled):hover {{ opacity: .87; }}
  #status {{ margin-top: 8px; font-size: 12px; color: #8892a4; min-height: 16px; }}
  #status.err {{ color: #f87171; }}
  .badge {{ background: rgba(52,211,153,.12); color: #34d399; border-radius: 99px; padding: 1px 9px; font-size: 11px; font-weight: 700; margin-left: 6px; }}
  .hint {{ color: #8892a4; font-size: 13px; padding: 10px 0; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{ text-align: left; padding: 7px 9px; border-bottom: 2px solid #2a2e3f; color: #8892a4; font-size: 11px; text-transform: uppercase; position: sticky; top: 0; background: #1a1d27; }}
  td {{ padding: 6px 9px; border-bottom: 1px solid #2a2e3f; vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: rgba(255,255,255,.02); }}
  .chip {{ display: inline-block; background: rgba(79,142,247,.1); color: #4f8ef7; border-radius: 3px; padding: 1px 5px; margin: 1px 2px 1px 0; font-size: 11px; font-weight: 600; font-family: monospace; }}
  .spinner {{ width: 18px; height: 18px; border: 2px solid #2a2e3f; border-top-color: #4f8ef7; border-radius: 50%; animation: spin .7s linear infinite; margin: 20px auto; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
</style>
</head>
<body>

<header>
  <h1>GenoCAD &rarr; Knox Design Explorer</h1>
  <p>Select parts and constraints to generate valid genetic designs.</p>
</header>

<main>
  <div class="col" id="part-panel"><h2>Parts</h2></div>

  <div class="col">
    <h2>Options</h2>
    <span class="lbl">Cassettes</span>
    <div class="cass-row">
      <button class="cass on" data-val="1">1</button>
      <button class="cass" data-val="2">2+</button>
    </div>
    <label class="lbl" for="ndesigns">Max Designs</label>
    <input type="number" id="ndesigns" value="100" min="1" max="10000">
    <label class="lbl" for="spaceid">Space ID</label>
    <input type="text" id="spaceid" value="ui_design">
    <label class="lbl" for="groupid">Group ID</label>
    <input type="text" id="groupid" value="ui_group">
    <hr>
    <span class="lbl">Goldbar</span>
    <pre class="goldbar" id="goldbar">&#x2014;</pre>
    <button id="btn" disabled>Generate</button>
    <p id="status"></p>
  </div>

  <div class="col">
    <h2 style="display:inline">Results</h2><span class="badge" id="count"></span>
    <div id="results" style="margin-top:14px"><p class="hint">Results appear here after generation.</p></div>
  </div>
</main>

<script>
const PARTS = {parts_json};
const ROLE  = {{ Promoter:"promoter", Ribosome:"ribosomeBindingSite", "Coding sequence":"cds", Terminator:"terminator", Insulator:"assemblyScar", Spacer:"spacer" }};
const ORDER = ["Promoter","Ribosome","Coding sequence","Terminator"];

const selected = {{}};
let cassettes = 1;

// build part checkboxes
const panel = document.getElementById("part-panel");
const cats  = [...ORDER.filter(c => PARTS[c]), ...Object.keys(PARTS).filter(c => !ORDER.includes(c))];

cats.forEach(cat => {{
  selected[cat] = new Set();
  const h = document.createElement("div");
  h.className   = "cat-name";
  h.textContent = cat;
  panel.appendChild(h);
  PARTS[cat].forEach(p => {{
    const row = document.createElement("label");
    row.className = "part";
    row.innerHTML = `<input type="checkbox" data-cat="${{cat}}" data-id="${{p.id}}">
      <span><span class="pid">${{p.id}}</span>${{p.desc ? `<br><span class="pdesc">${{p.desc}}</span>` : ""}}</span>`;
    panel.appendChild(row);
  }});
}});

panel.querySelectorAll("input").forEach(cb => {{
  cb.addEventListener("change", () => {{
    cb.checked ? selected[cb.dataset.cat].add(cb.dataset.id)
               : selected[cb.dataset.cat].delete(cb.dataset.id);
    refresh();
  }});
}});

document.querySelectorAll(".cass").forEach(b => {{
  b.addEventListener("click", () => {{
    document.querySelectorAll(".cass").forEach(x => x.classList.remove("on"));
    b.classList.add("on");
    cassettes = Number(b.dataset.val);
    refresh();
  }});
}});

function buildGoldbar() {{
  const active = cats.filter(c => selected[c]?.size > 0);
  if (!active.length) return null;
  const cats2 = {{}};
  const tokens = active.map(cat => {{
    const tok = cat.replace(/[^A-Za-z0-9]/g,"_").replace(/^_+|_+$/g,"");
    cats2[tok] = {{ [ROLE[cat]||"cds"]: [...selected[cat]] }};
    return tok;
  }});
  const expr   = tokens.join(" . ");
  const goldbar = cassettes > 1 ? `one-or-more(${{expr}})` : expr;
  return {{ goldbar, categories: cats2 }};
}}

function refresh() {{
  const g = buildGoldbar();
  document.getElementById("goldbar").textContent = g ? g.goldbar : "—";
  document.getElementById("btn").disabled = !g;
}}

// API calls go through the local proxy (no CORS issues)
async function importGoldbar(goldbar, categories, spaceId, groupId) {{
  const resp = await fetch("/knox/goldbar/import", {{
    method: "POST",
    headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
    body: new URLSearchParams({{ goldbar, categories: JSON.stringify(categories), outputSpaceID: spaceId, groupID: groupId, weight:"1.0" }})
  }});
  if (!resp.ok) throw new Error(`Import failed (${{resp.status}})`);
}}

async function enumerate(spaceId, n) {{
  const resp = await fetch("/knox/designSpace/enumerate?" + new URLSearchParams({{
    targetSpaceID: spaceId, numDesigns: n, bfs: false, allDesigns: true
  }}));
  if (!resp.ok) throw new Error(`Enumerate failed (${{resp.status}})`);
  const data = await resp.json();
  return (data.designs || []).map(d => {{
    const elems = Array.isArray(d) ? d : (d.design || []);
    return elems
      .filter(e => String(e.isBlank) !== "true")
      .map(e => {{
        const id = e.id || e.componentID || "";
        const parts = id.split("/");
        return parts.length > 1 ? parts[parts.length-2] : id;
      }});
  }});
}}

document.getElementById("btn").addEventListener("click", async () => {{
  const btn     = document.getElementById("btn");
  const status  = document.getElementById("status");
  const results = document.getElementById("results");
  const count   = document.getElementById("count");
  const spaceId = document.getElementById("spaceid").value.trim() || "ui_design";
  const groupId = document.getElementById("groupid").value.trim() || "ui_group";
  const n       = Number(document.getElementById("ndesigns").value) || 100;
  const gb      = buildGoldbar();

  btn.disabled      = true;
  status.className  = "status";
  status.textContent = "Sending to Knox...";
  results.innerHTML  = `<div class="spinner"></div>`;
  count.textContent  = "";

  try {{
    await importGoldbar(gb.goldbar, gb.categories, spaceId, groupId);
    const designs = await enumerate(spaceId, n);

    count.textContent  = designs.length;
    status.textContent = `Done - ${{designs.length}} design(s) found`;

    if (!designs.length) {{
      results.innerHTML = `<p class="hint">Knox returned 0 designs. Try selecting more parts.</p>`;
      return;
    }}

    results.innerHTML = `<table>
      <thead><tr><th>#</th><th>Design</th></tr></thead>
      <tbody>
        ${{designs.map((parts,i) => `<tr><td style="color:#8892a4;width:30px">${{i+1}}</td>
          <td>${{parts.map(p=>`<span class="chip">${{p}}</span>`).join("")}}</td></tr>`).join("")}}
      </tbody>
    </table>`;

  }} catch (err) {{
    status.className   = "status err";
    status.textContent = err.message;
    results.innerHTML  = `<p class="hint">Something went wrong. Is Knox running?</p>`;
  }} finally {{
    btn.disabled = false;
  }}
}});
</script>
</body>
</html>"""


# ── start everything ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    parts = load_parts()
    print(f"Loaded {sum(len(v) for v in parts.values())} parts from {len(parts)} categories")

    Handler.html_content = build_html(parts)

    server = HTTPServer(("localhost", PORT), Handler)

    # open the browser after a short delay
    def open_browser():
        import time
        time.sleep(0.8)
        webbrowser.open(f"http://localhost:{PORT}")

    threading.Thread(target=open_browser, daemon=True).start()

    print(f"\nOpen http://localhost:{PORT} in your browser (opening automatically...)")
    print("Press Ctrl+C to stop.\n")
    server.serve_forever()
