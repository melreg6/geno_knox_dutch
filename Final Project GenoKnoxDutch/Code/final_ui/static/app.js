
const ROLE  = { Promoter:"promoter", Ribosome:"ribosomeBindingSite", "Coding sequence":"cds", Terminator:"terminator", Insulator:"assemblyScar", Spacer:"spacer" };
const ORDER = ["Promoter","Ribosome","Coding sequence","Terminator"];
let lastDesigns = [];

const selected = {};
let cassettes = 1;
const PART_LOOKUP = {};

Object.keys(PARTS).forEach(cat => {
  PARTS[cat].forEach(p => {
    PART_LOOKUP[p.id] = p;
  });
});

// build part checkboxes
const nav = document.getElementById("part-nav");
const display = document.getElementById("part-display");

const cats = [
  ...ORDER.filter(c => PARTS[c]),
  ...Object.keys(PARTS).filter(c => !ORDER.includes(c))
];
cats.forEach(cat => {
  selected[cat] = new Set();

  // LEFT SIDE (button + selected)
  const section = document.createElement("div");
  section.className = "part-section";

  const toggle = document.createElement("button");
  toggle.className = "part-toggle";
  toggle.textContent = cat;

  const selectedBox = document.createElement("div");
  selectedBox.className = "part-selected";

  section.appendChild(toggle);
  section.appendChild(selectedBox);
  nav.appendChild(section);

  // RIGHT SIDE (actual parts list)
  const list = document.createElement("div");
  list.className = "part-list";
  list.dataset.cat = cat;

  PARTS[cat].forEach(p => {
    const row = document.createElement("label");
    row.className = "part";
    row.innerHTML = `
      <input type="checkbox" data-cat="${cat}" data-id="${p.id}">
      <span>
        <span class="pid">${p.id}</span>
        ${p.desc ? `<br><span class="pdesc">${p.desc}</span>` : ""}
      </span>
    `;
    list.appendChild(row);
  });

  display.appendChild(list);

  // toggle behavior → show in RIGHT panel
  toggle.addEventListener("click", () => {
    document.querySelectorAll(".part-list").forEach(l => {
      l.classList.remove("active");
    });
    list.classList.add("active");
  });
});

display.addEventListener("change", e => {
  if (e.target.tagName !== "INPUT") return;

  const cb = e.target;
  const cat = cb.dataset.cat;
  const id = cb.dataset.id;

  if (cb.checked) {
    selected[cat].add(id);
  } else {
    selected[cat].delete(id);
  }

  updateSelectedUI(cat);
  updateSelectedColumn(); 
  refresh();
});

updateSelectedColumn();

document.getElementById("selected-list").addEventListener("click", e => {
  if (!e.target.classList.contains("chip")) return;

  const id = e.target.textContent;

  for (const cat in selected) {
    if (selected[cat].has(id)) {
      selected[cat].delete(id);

      // uncheck checkbox in UI
      const cb = document.querySelector(`input[data-id="${id}"]`);
      if (cb) cb.checked = false;

      updateSelectedUI(cat);
    }
  }

  updateSelectedColumn();
  refresh();
});

function updateSelectedUI(cat) {
  const section = [...document.querySelectorAll(".part-section")]
    .find(s => s.querySelector(".part-toggle").textContent === cat);

  const box = section.querySelector(".part-selected");

  const items = [...selected[cat]].map(p =>
    `<span class="chip">${p}</span>`
  ).join("");

  box.innerHTML = items || `<span class="hint">None selected</span>`;
}

cats.forEach(updateSelectedUI);

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".cass").forEach(b => {
    b.addEventListener("click", () => {
      document.querySelectorAll(".cass").forEach(x => x.classList.remove("on"));
      b.classList.add("on");
      cassettes = Number(b.dataset.val);
      refresh();
    });
  });
});

function updateSelectedColumn() {
  const container = document.getElementById("selected-list");

  const groups = Object.entries(selected)
    .filter(([_, set]) => set.size > 0)
    .map(([cat, set]) => {
      const chips = [...set]
        .map(id => `<span class="chip">${id}</span>`)
        .join("");

      return `
        <div class="selected-group">
          <div class="selected-title">${cat}</div>
          ${chips}
        </div>
      `;
    });

  container.innerHTML = groups.length
    ? groups.join("")
    : `<span class="hint">No parts selected</span>`;
}

function buildGoldbar() {
  const active = cats.filter(c => selected[c]?.size > 0);
  if (!active.length) return null;
  const cats2 = {};
  const tokens = active.map(cat => {
    const tok = cat.replace(/[^A-Za-z0-9]/g,"_").replace(/^_+|_+$/g,"");
    cats2[tok] = { [ROLE[cat]||"cds"]: [...selected[cat]] };
    return tok;
  });
  const expr   = tokens.join(" then ");
  const goldbar = cassettes > 1 ? `one-or-more(${expr})` : expr;
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

async function enumerate(spaceId, n) {
  

  const resp = await fetch("/knox/designSpace/enumerate?" + new URLSearchParams({
    targetSpaceID: spaceId,
    numDesigns: n,
    bfs: false,
    allDesigns: true
  }));

  const text = await resp.text();
  console.log("RAW ENUM RESPONSE:", text);

  let data;
  try {
    data = JSON.parse(text);
  } catch (e) {
    throw new Error("Invalid JSON from Knox enumerate");
  }

  const raw = Array.isArray(data)
    ? data
    : (data.designs || data.results || []);

  return raw.map(d => {
    const elems = Array.isArray(d) ? d : (d.design || []);
    return elems
      .filter(e => String(e.isBlank) !== "true")
      .map(e => {
        const id = e.id || e.componentID || "";
        const parts = id.split("/");
        return parts.length > 1 ? parts[parts.length - 2] : id;
      });
  });
}

document.getElementById("btn").addEventListener("click", async () => {
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
  document.getElementById("export-btns").style.display = "none";
  count.textContent  = "";

  try {
    await importGoldbar(gb.goldbar, gb.categories, spaceId, groupId);
    const designs = await enumerate(spaceId, n);
    lastDesigns = designs;

    count.textContent  = designs.length;
    status.textContent = `Done - ${designs.length} design(s) found`;

    const exportBtns = document.getElementById("export-btns");

if (!designs.length) {
  exportBtns.style.display = "none"; // hide if nothing
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

    exportBtns.style.display = "flex";

  } catch (err) {
    status.className   = "status err";
    status.textContent = err.message;
    results.innerHTML  = `<p class="hint">Something went wrong. Is Knox running?</p>`;
  } finally {
    btn.disabled = false;
  }
});

function downloadCSV(rows, filename) {
  const csv = rows
    .map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(","))
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url  = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();

  URL.revokeObjectURL(url);
}

// match your Python PART_TYPE mapping
const PARTTYPE = {
  "Promoter": "Promoter",
  "Ribosome": "RBS",
  "Coding sequence": "CDS",
  "Terminator": "Terminator",
  "Insulator": "Scar",
  "Spacer": "Spacer"
};

function exportPartsCSV() {
  const rows = [
    ["Part", "Part Type", "Strength", "Strength_SD", "REU", "REU_SD", "Part Sequence"]
  ];

  Object.keys(selected).forEach(cat => {
    if (!selected[cat] || selected[cat].size === 0) return;

    const pt = PARTTYPE[cat] || "CDS";

    selected[cat].forEach(id => {
      const part = PART_LOOKUP[id] || {};
      const seq  = part.sequence || "";
      rows.push([id, pt, "1.0", "0.0", "1.0", "0.0", seq]);
    });
  });

  downloadCSV(rows, "doubledutch_parts.csv");
}

function exportDesignsCSV() {
  if (!lastDesigns.length) return;

  const maxLen = Math.max(...lastDesigns.map(d => d.length));

  const header = ["#", ...Array.from({ length: maxLen }, (_, i) => `Part ${i + 1}`)];

  const rows = [
    header,
    ...lastDesigns.map((d, i) => [i + 1, ...d])
  ];

  downloadCSV(rows, "knox_designs.csv");
}