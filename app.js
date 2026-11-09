/* NC OSA Genie Workshop site: tabs, progress, copy buttons, question list, print, active nav. */
(function () {
  const store = {
    get: (k, d) => { try { return JSON.parse(localStorage.getItem("osa-genie:" + k)) ?? d; } catch (e) { return d; } },
    set: (k, v) => localStorage.setItem("osa-genie:" + k, JSON.stringify(v)),
  };
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* ---------- copy buttons ---------- */
  function copyBtn(getText) {
    const b = document.createElement("button");
    b.className = "copy"; b.type = "button"; b.textContent = "Copy";
    b.addEventListener("click", async (e) => {
      e.preventDefault(); e.stopPropagation();
      try { await navigator.clipboard.writeText(getText()); } catch (err) {
        const t = document.createElement("textarea"); t.value = getText(); document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove();
      }
      b.textContent = "Copied"; b.classList.add("done");
      setTimeout(() => { b.textContent = "Copy"; b.classList.remove("done"); }, 1400);
    });
    return b;
  }
  $$("p.q").forEach((q) => { const t = q.textContent.trim(); q.appendChild(copyBtn(() => t)); });

  /* ---------- tabs ---------- */
  $$(".tabs").forEach((tabs) => {
    const bar = $(".tab-buttons", tabs);
    if (bar && tabs.dataset.label) { const l = document.createElement("span"); l.className = "tab-label"; l.textContent = tabs.dataset.label; bar.prepend(l); }
    const key = "tab:" + tabs.dataset.tabs;
    const show = (id) => {
      $$(".tab-buttons button", tabs).forEach((b) => b.classList.toggle("active", b.dataset.tab === id));
      $$(".tab-panel", tabs).forEach((p) => p.classList.toggle("active", p.id === id));
    };
    $$(".tab-buttons button", tabs).forEach((b) => b.addEventListener("click", () => { show(b.dataset.tab); store.set(key, b.dataset.tab); }));
    const saved = store.get(key, null);
    if (saved && $("#" + saved, tabs)) show(saved);
  });

  /* ---------- checklists + progress ---------- */
  const checks = store.get("checks", {});
  const boxes = $$('input[type="checkbox"][data-id]');
  function updateProgress() {
    const done = boxes.filter((b) => b.checked).length;
    const pct = boxes.length ? Math.round((100 * done) / boxes.length) : 0;
    $("#progress-bar").style.width = pct + "%"; $("#progress-label").textContent = pct + "%";
  }
  boxes.forEach((b) => {
    b.checked = !!checks[b.dataset.id];
    b.addEventListener("change", () => { checks[b.dataset.id] = b.checked; store.set("checks", checks); updateProgress(); });
  });
  updateProgress();

  /* ---------- question list ---------- */
  const FIELDS = [
    ["question", "Question", "textarea"],
    ["team", "Team", "select"],
    ["asked_by", "Who asks it", "input"],
    ["result", "What Genie did", "select"],
    ["notes", "Notes (terms to define, data it needs)", "textarea"],
  ];
  const OPTIONS = {
    team: ["", "Financial Audit", "Performance Audit", "Rapid Response", "Other"],
    result: ["", "Not tried yet", "Right answer", "Close, needed rewording", "Wrong answer", "Data not available"],
  };
  const WIDE = new Set(["question", "notes"]);
  const list = $("#byoq-list");
  let items = store.get("byoq", [{}]);
  if (!items.length) items = [{}];
  function renderByoq() {
    list.innerHTML = "";
    items.forEach((it, idx) => {
      const card = document.createElement("div"); card.className = "byoq-card";
      card.innerHTML = `<div class="head"><strong>Question ${idx + 1}</strong><button class="rm" type="button">Remove</button></div>`;
      const row = document.createElement("div"); row.className = "row";
      FIELDS.forEach(([key, label, kind]) => {
        const box = document.createElement("div");
        if (WIDE.has(key)) box.style.gridColumn = "1 / -1";
        const id = `byoq-${idx}-${key}`;
        box.innerHTML = `<label for="${id}">${esc(label)}</label>`;
        let el;
        if (kind === "select") {
          el = document.createElement("select");
          OPTIONS[key].forEach((o) => { const op = document.createElement("option"); op.value = o; op.textContent = o || "Choose"; el.appendChild(op); });
        } else el = document.createElement(kind);
        el.id = id; el.value = it[key] || "";
        const save = () => { items[idx][key] = el.value; store.set("byoq", items); };
        el.addEventListener("input", save);
        el.addEventListener("change", save);
        box.appendChild(el); row.appendChild(box);
      });
      card.appendChild(row);
      $(".rm", card).addEventListener("click", () => { items.splice(idx, 1); if (!items.length) items = [{}]; store.set("byoq", items); renderByoq(); });
      list.appendChild(card);
    });
  }
  renderByoq();
  $("#byoq-add").addEventListener("click", () => { items.push({}); store.set("byoq", items); renderByoq(); });
  $("#byoq-export-csv").addEventListener("click", () => {
    const rows = items.filter((it) => (it.question || "").trim());
    if (!rows.length) { alert("Add at least one question first."); return; }
    const cell = (v) => `"${String(v || "").replace(/"/g, '""')}"`;
    const csv = [FIELDS.map((f) => cell(f[1])).join(",")]
      .concat(rows.map((it) => FIELDS.map((f) => cell(it[f[0]])).join(","))).join("\r\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = "osa-genie-questions-2026-11-10.csv";
    document.body.appendChild(a); a.click(); a.remove();
  });

  // Email: opens the attendee's mail app with the list filled in, addressed to the workshop team.
  const EMAIL_TO = "amir.lyall@databricks.com";
  $("#byoq-email").addEventListener("click", () => {
    const rows = items.filter((it) => (it.question || "").trim());
    if (!rows.length) { alert("Add at least one question first."); return; }
    const body = "Here are my questions from the Genie workshop on Nov 10, 2026.\n\n" + rows.map((it, i) =>
      FIELDS.map(([k, label]) => (it[k] || "").trim() ? `${k === "question" ? i + 1 + ". " : "   " + label + ": "}${it[k].trim()}` : "")
        .filter(Boolean).join("\n")).join("\n\n");
    location.href = `mailto:${EMAIL_TO}?subject=${encodeURIComponent("OSA Genie workshop: my questions")}&body=${encodeURIComponent(body)}`;
  });

  /* ---------- print ---------- */
  let closedForPrint = [];
  window.addEventListener("beforeprint", () => {
    $$(".tab-panel").forEach((p) => p.classList.add("print-show"));
    closedForPrint = $$("details:not([open])");
    closedForPrint.forEach((d) => d.setAttribute("open", ""));
  });
  window.addEventListener("afterprint", () => {
    $$(".tab-panel").forEach((p) => p.classList.remove("print-show"));
    closedForPrint.forEach((d) => d.removeAttribute("open")); closedForPrint = [];
  });
  $("#print-btn").addEventListener("click", () => window.print());

  /* ---------- active nav ---------- */
  const links = $$(".sidebar a");
  const sections = links.map((a) => document.querySelector(a.getAttribute("href"))).filter(Boolean);
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) links.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === "#" + e.target.id));
    });
  }, { rootMargin: "-40% 0px -55% 0px" });
  sections.forEach((s) => obs.observe(s));
})();
