/* Cook Me: pick what you have, get dishes to cook. Data comes from recipes.js (window.RANEA). */
(() => {
  const D = window.RANEA;
  const root = document.getElementById("cookme");
  if (!D || !root) return;

  const TEXT = {
    ms: {
      title: "Masak apa <em>hari ini?</em>",
      lede: "Pilih bahan yang ada di dapur anda. Kami cadangkan hidangan yang boleh dimasak dengan Ranéa.",
      chips: "Bahan-bahan",
      clear: "Kosongkan pilihan",
      empty: "Pilih sekurang-kurangnya satu bahan untuk bermula.",
      results: (n) => `${n} cadangan untuk anda`,
      note: "Termasuk hidangan ringkas dari almari dapur.",
      have: (a, b) => `Anda ada ${a} daripada ${b} bahan`,
      view: "Lihat resipi",
      ing: "Bahan-bahan",
      how: "Cara-cara",
      bit: "Sentuhan Ranéa",
      all: "Semua <em>resipi</em>",
    },
    en: {
      title: "What's in <em>your kitchen?</em>",
      lede: "Pick what you have. We will suggest dishes you can cook with Ranéa.",
      chips: "Ingredients",
      clear: "Clear selection",
      empty: "Pick at least one ingredient to begin.",
      results: (n) => `${n} ideas for you`,
      note: "Including simple dishes from the store cupboard.",
      have: (a, b) => `You have ${a} of ${b} ingredients`,
      view: "See recipe",
      ing: "Ingredients",
      how: "How to cook",
      bit: "The Ranéa bit",
      all: "All <em>recipes</em>",
    },
  };

  let lang = "ms";
  try {
    const saved = localStorage.getItem("ranea-lang");
    if (saved === "en" || saved === "ms") lang = saved;
  } catch (e) {}
  const picked = new Set();
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // A list of lines; a line starting with "#" is a sub-heading (e.g. "For the rice").
  function lines(items, ordered) {
    const tag = ordered ? "ol" : "ul";
    let out = "";
    let open = false;
    for (const it of items) {
      if (it[0] === "#") {
        if (open) out += `</${tag}>`;
        open = false;
        out += `<h5>${esc(it.slice(1))}</h5>`;
      } else {
        if (!open) out += `<${tag}>`;
        open = true;
        out += `<li>${esc(it)}</li>`;
      }
    }
    return out + (open ? `</${tag}>` : "");
  }

  // The photo sits over a name plate. Recipes without a photo yet (photo: false in recipes.js) show
  // the plate alone. Save a photo into images/ under the exact file name, then re-run tools/gen.py.
  function card(r, hit) {
    const T = TEXT[lang];
    const L = r[lang];
    const have = hit && hit.m.length ? `<p class="have">${esc(T.have(hit.m.length, r.tags.length))}</p>` : "";
    return `<article class="card">
      <div class="ph"><div class="plate" aria-hidden="true">${esc(L.n)}</div>${r.photo ? `<img src="images/${esc(r.img)}" alt="${esc(L.n)}" loading="lazy" onerror="this.remove()">` : ""}</div>
      <h3>${esc(L.n)}</h3>
      <p class="meta">${esc(r.t[lang])} · ${esc(r.s[lang])}</p>
      <p class="blurb">${esc(L.b)}</p>${have}
      <details><summary>${esc(T.view)}</summary>
        <h4>${esc(T.ing)}</h4>${lines(L.i, false)}
        <h4>${esc(T.how)}</h4>${lines(L.h, true)}
        <p class="bit"><strong>${esc(T.bit)}.</strong> ${esc(L.r)}</p>
      </details>
    </article>`;
  }

  // Dishes whose main ingredient you have come first, then the most ingredients matched.
  // With fewer than three matches, the sheet's pantry-fallback dishes fill the gap.
  function match() {
    const scored = D.recipes
      .map((r) => {
        const m = r.tags.filter((t) => picked.has(t));
        const hero = r.hero.some((h) => picked.has(h));
        return { r, m, hero, score: (hero ? 100 : 0) + m.length * 10 + (m.length / r.tags.length) * 5 };
      })
      .filter((x) => x.m.length)
      .sort((a, b) => b.score - a.score || a.r.en.n.localeCompare(b.r.en.n));
    const list = scored.slice(0, 6);
    let note = false;
    if (list.length < 3) {
      for (const r of D.recipes) {
        if (list.length >= 3) break;
        if (r.pantry && !list.some((x) => x.r === r)) {
          list.push({ r, m: [], hero: false });
          note = true;
        }
      }
    }
    return { list, note };
  }

  function renderChips() {
    $("chips").setAttribute("aria-label", TEXT[lang].chips);
    $("chips").innerHTML = D.keys
      .map((k) => `<button type="button" class="chip" data-k="${esc(k.k)}" aria-pressed="${picked.has(k.k)}">${esc(k[lang])}</button>`)
      .join("");
  }

  function renderResults() {
    const T = TEXT[lang];
    $("clear").hidden = picked.size === 0;
    if (!picked.size) {
      $("results").innerHTML = `<p class="results-note">${esc(T.empty)}</p>`;
      return;
    }
    const { list, note } = match();
    $("results").innerHTML =
      `<p class="results-head">${esc(T.results(list.length))}</p>` +
      (note ? `<p class="results-note">${esc(T.note)}</p>` : "") +
      `<div class="cards three">${list.map((x) => card(x.r, x)).join("")}</div>`;
  }

  function renderAll() {
    $("all").innerHTML = D.recipes.filter((r) => r.show).map((r) => card(r, null)).join("");
  }

  function render() {
    const T = TEXT[lang];
    root.lang = lang;
    for (const el of root.querySelectorAll("[data-t]")) el.innerHTML = T[el.dataset.t];
    for (const b of root.querySelectorAll(".lang button")) b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
    $("clear").textContent = T.clear;
    renderChips();
    renderResults();
    renderAll();
  }

  root.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip) {
      const k = chip.dataset.k;
      picked.has(k) ? picked.delete(k) : picked.add(k);
      chip.setAttribute("aria-pressed", String(picked.has(k)));
      renderResults();
      return;
    }
    const lb = e.target.closest(".lang button");
    if (lb) {
      lang = lb.dataset.lang;
      try {
        localStorage.setItem("ranea-lang", lang);
      } catch (err) {}
      render();
      return;
    }
    if (e.target.closest("#clear")) {
      picked.clear();
      renderChips();
      renderResults();
    }
  });

  render();
})();
