import json

ORDER    = ["Promoter", "Ribosome", "Coding sequence", "Terminator"]
ROLE_MAP = {
    "Promoter":        "promoter",
    "Ribosome":        "ribosomeBindingSite",
    "Coding sequence": "cds",
    "Terminator":      "terminator",
    "Insulator":       "insulator",
    "Spacer":          "spacer",
}
PART_TYPE = {
    "Promoter":        "Promoter",
    "Ribosome":        "RBS",
    "Coding sequence": "CDS",
    "Terminator":      "Terminator",
    "Insulator":       "Scar",
    "Spacer":          "Spacer",
}


def build_html(parts: dict) -> str:
    parts_json    = json.dumps(parts)
    order_json    = json.dumps(ORDER)
    role_json     = json.dumps(ROLE_MAP)
    parttype_json = json.dumps(PART_TYPE)

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
  .export-row {{ display: flex; gap: 8px; margin-top: 12px; }}
  .btn-export {{ flex: 1; padding: 7px; background: #1a1d27; border: 1px solid #2a2e3f; border-radius: 6px; color: #8892a4; font-size: 11px; font-weight: 600; cursor: pointer; }}
  .btn-export:hover {{ border-color: #4f8ef7; color: #4f8ef7; }}
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
    <h2>Results <span class="badge" id="count"></span></h2>
    <div id="results"><p class="hint">Select parts and click Generate.</p></div>
    <div class="export-row" id="export-btns" style="display:none">
      <button class="btn-export" onclick="exportPartsCSV()">Export Parts CSV</button>
      <button class="btn-export" onclick="exportDesignsCSV()">Export Designs CSV</button>
    </div>
  </div>
</main>

<script>
const PARTS    = {parts_json};
const ORDER    = {order_json};
const ROLE     = {role_json};
const PARTTYPE = {parttype_json};

const selected  = {{}};
let cassettes   = 1;
let lastDesigns = [];

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

function sanitizeToken(cat) {{
  return cat.replace(/[^A-Za-z0-9]/g, "_").replace(/^_+|_+$/g, "");
}}

function buildGoldbar() {{
  const orderedActive = ORDER.filter(c => selected[c]?.size > 0);
  const extraActive   = cats.filter(c => !ORDER.includes(c) && selected[c]?.size > 0);
  const active        = [...orderedActive, ...extraActive];

  if (!active.length) return null;

  const categories = {{}};
  const tokens = active.map(cat => {{
    const tok  = sanitizeToken(cat);
    const role = ROLE[cat] || "cds";
    categories[tok] = {{ [role]: [...selected[cat]] }};
    return tok;
  }});

  const expr    = tokens.join(" . ");
  const goldbar = cassettes > 1 ? `one-or-more(${{expr}})` : expr;
  return {{ goldbar, categories }};
}}

function refresh() {{
  const g = buildGoldbar();
  document.getElementById("goldbar").textContent = g ? g.goldbar : "—";
  document.getElementById("btn").disabled = !g;
}}

async function importGoldbar(goldbar, categories, spaceId, groupId) {{
  const resp = await fetch("/knox/goldbar/import", {{
    method: "POST",
    headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
    body: new URLSearchParams({{
      goldbar,
      categories: JSON.stringify(categories),
      outputSpaceID: spaceId,
      groupID: groupId,
      weight: "1.0"
    }})
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
        const id    = e.id || e.componentID || "";
        const parts = id.split("/");
        return parts.length > 1 ? parts[parts.length - 2] : id;
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

  btn.disabled       = true;
  status.className   = "status";
  status.textContent = "Sending to Knox...";
  results.innerHTML  = `<div class="spinner"></div>`;
  count.textContent  = "";

  try {{
    await importGoldbar(gb.goldbar, gb.categories, spaceId, groupId);
    const designs = await enumerate(spaceId, n);

    lastDesigns        = designs;
    count.textContent  = designs.length;
    status.textContent = `Done — ${{designs.length}} design(s) found`;

    if (!designs.length) {{
      results.innerHTML = `<p class="hint">Knox returned 0 designs. Try selecting more parts.</p>`;
      return;
    }}

    document.getElementById("export-btns").style.display = "flex";
    results.innerHTML = `<table>
      <thead><tr><th>#</th><th>Design</th></tr></thead>
      <tbody>
        ${{designs.map((parts, i) => `<tr>
          <td style="color:#8892a4;width:30px">${{i + 1}}</td>
          <td>${{parts.map(p => `<span class="chip">${{p}}</span>`).join("")}}</td>
        </tr>`).join("")}}
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

function downloadCSV(rows, filename) {{
  const csv = rows.map(r => r.map(v => `"${{String(v).replace(/"/g, '""')}}"`).join(",")).join("\\n");
  const a   = document.createElement("a");
  a.href     = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
  a.download = filename;
  a.click();
}}

function exportPartsCSV() {{
  const rows = [["Part", "Part Type", "Strength", "Strength_SD", "REU", "REU_SD", "Part Sequence"]];
  cats.forEach(cat => {{
    if (!selected[cat]?.size) return;
    const pt = PARTTYPE[cat] || "CDS";
    selected[cat].forEach(id => rows.push([id, pt, "1.0", "0.0", "1.0", "0.0", ""]));
  }});
  downloadCSV(rows, "doubledutch_parts.csv");
}}

function exportDesignsCSV() {{
  const maxLen = Math.max(...lastDesigns.map(d => d.length));
  const header = ["#", ...Array.from({{length: maxLen}}, (_, i) => `Part ${{i + 1}}`)];
  const rows   = [header, ...lastDesigns.map((d, i) => [i + 1, ...d])];
  downloadCSV(rows, "knox_designs.csv");
}}
</script>
</body>
</html>"""
