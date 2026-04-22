
const ROLE  = { Promoter:"promoter", Ribosome:"ribosomeBindingSite", "Coding sequence":"cds", Terminator:"terminator", Insulator:"assemblyScar", Spacer:"spacer" };
const ORDER = ["Promoter","Ribosome","Coding sequence","Terminator"];

const selected = {};
let cassettes = 1;

// build part checkboxes
const panel = document.getElementById("part-panel");
const cats  = [...ORDER.filter(c => PARTS[c]), ...Object.keys(PARTS).filter(c => !ORDER.includes(c))];

cats.forEach(cat => {
  selected[cat] = new Set();
  const h = document.createElement("div");
  h.className   = "cat-name";
  h.textContent = cat;
  panel.appendChild(h);
  PARTS[cat].forEach(p => {
    const row = document.createElement("label");
    row.className = "part";
    row.innerHTML = `<input type="checkbox" data-cat="${cat}" data-id="${p.id}">
      <span><span class="pid">${p.id}</span>${p.desc ? `<br><span class="pdesc">${p.desc}</span>` : ""}</span>`;
    panel.appendChild(row);
  });
});

panel.querySelectorAll("input").forEach(cb => {
  cb.addEventListener("change", () => {
    cb.checked ? selected[cb.dataset.cat].add(cb.dataset.id)
               : selected[cb.dataset.cat].delete(cb.dataset.id);
    refresh();
  });
});

document.querySelectorAll(".cass").forEach(b => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".cass").forEach(x => x.classList.remove("on"));
    b.classList.add("on");
    cassettes = Number(b.dataset.val);
    refresh();
  });
});

function buildGoldbar() {
  const active = cats.filter(c => selected[c]?.size > 0);
  if (!active.length) return null;
  const cats2 = {};
  const tokens = active.map(cat => {
    const tok = cat.replace(/[^A-Za-z0-9]/g,"_").replace(/^_+|_+$/g,"");
    cats2[tok] = { [ROLE[cat]||"cds"]: [...selected[cat]] };
    return tok;
  });
  const expr   = tokens.join(" . ");
  const goldbar = cassettes > 1 ? `one-or-more(${{expr}})` : expr;
  return { goldbar, categories: cats2 };
}

function refresh() {
  const g = buildGoldbar();
  document.getElementById("goldbar").textContent = g ? g.goldbar : "—";
  document.getElementById("btn").disabled = !g;
}

// API calls go through the local proxy (no CORS issues)
async function importGoldbar(goldbar, categories, spaceId, groupId) {
  const resp = await fetch("/knox/goldbar/import", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ goldbar, categories: JSON.stringify(categories), outputSpaceID: spaceId, groupID: groupId, weight:"1.0" })
  });
  if (!resp.ok) throw new Error(`Import failed (${resp.status})`);
}

async function enumerate(spaceId, n) {{
  const resp = await fetch("/knox/designSpace/enumerate?" + new URLSearchParams({
    targetSpaceID: spaceId, numDesigns: n, bfs: false, allDesigns: true
  }));
  if (!resp.ok) throw new Error(`Enumerate failed (${resp.status})`);
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
    status.textContent = `Done - ${designs.length} design(s) found`;

    if (!designs.length) {
      results.innerHTML = `<p class="hint">Knox returned 0 designs. Try selecting more parts.</p>`;
      return;
    }

    results.innerHTML = `<table>
      <thead><tr><th>#</th><th>Design</th></tr></thead>
      <tbody>
        ${designs.map((parts,i) => `<tr><td style="color:#8892a4;width:30px">${i+1}</td>
          <td>${parts.map(p=>`<span class="chip">${p}</span>`).join("")}</td></tr>`).join("")}
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