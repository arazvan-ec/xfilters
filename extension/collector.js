/*
 * xfilters — X/Twitter Bookmarks collector
 * ----------------------------------------
 * Runs in the MAIN world of x.com / twitter.com (see manifest.json).
 *
 * How it works:
 *  1. It patches window.fetch and XMLHttpRequest so it can read the JSON
 *     responses of the "Bookmarks" GraphQL endpoint that the X web app itself
 *     requests as you scroll. This is far more robust than scraping the DOM
 *     (which X deliberately obfuscates) because we get the raw, structured
 *     tweet objects: full text, author, media, metrics, dates, entities…
 *  2. It shows a small floating panel with a live counter and controls.
 *  3. "Iniciar" auto-scrolls your Bookmarks page so X loads every page; the
 *     hook captures each batch and de-duplicates by tweet id.
 *  4. "Descargar JSON" saves a clean, normalized array to a file.
 *
 * Nothing is sent anywhere. No cookies or tokens are read or transmitted.
 * Everything happens locally in your browser.
 */
(function () {
  "use strict";

  // Guard against double-injection on SPA re-navigations.
  if (window.__XFILTERS_BOOKMARKS_ACTIVE__) return;
  window.__XFILTERS_BOOKMARKS_ACTIVE__ = true;

  /** id -> normalized bookmark record */
  const store = new Map();
  let capturing = false;
  let panel = null;
  let statusEl = null;
  let countEl = null;

  // ---------------------------------------------------------------------------
  // Network interception
  // ---------------------------------------------------------------------------
  const isBookmarksUrl = (url) =>
    typeof url === "string" && /\/graphql\/[^/]+\/Bookmarks\b/.test(url);

  function ingest(jsonText) {
    let data;
    try {
      data = typeof jsonText === "string" ? JSON.parse(jsonText) : jsonText;
    } catch (_) {
      return;
    }
    const before = store.size;
    for (const result of findTweetResults(data)) {
      const rec = normalizeTweet(result);
      if (rec && rec.id && !store.has(rec.id)) store.set(rec.id, rec);
    }
    if (store.size !== before) render();
  }

  // Patch fetch
  const origFetch = window.fetch;
  if (typeof origFetch === "function") {
    window.fetch = function (input, init) {
      const p = origFetch.apply(this, arguments);
      try {
        const url = typeof input === "string" ? input : input && input.url;
        if (isBookmarksUrl(url)) {
          p.then((res) => {
            res.clone().text().then(ingest).catch(() => {});
          }).catch(() => {});
        }
      } catch (_) {}
      return p;
    };
  }

  // Patch XHR (belt-and-suspenders; X mostly uses fetch)
  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    this.__xf_url = url;
    return origOpen.apply(this, arguments);
  };
  const origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function () {
    try {
      if (isBookmarksUrl(this.__xf_url)) {
        this.addEventListener("load", function () {
          try {
            ingest(this.responseText);
          } catch (_) {}
        });
      }
    } catch (_) {}
    return origSend.apply(this, arguments);
  };

  // ---------------------------------------------------------------------------
  // Extraction / normalization
  // ---------------------------------------------------------------------------

  /** Recursively find every `tweet_results.result` object in the payload. */
  function findTweetResults(node, out = [], seen = new Set()) {
    if (!node || typeof node !== "object") return out;
    if (seen.has(node)) return out;
    seen.add(node);
    if (node.tweet_results && node.tweet_results.result) {
      out.push(node.tweet_results.result);
    }
    for (const k in node) {
      const v = node[k];
      if (v && typeof v === "object") findTweetResults(v, out, seen);
    }
    return out;
  }

  function bestVideoUrl(media) {
    const variants = (media.video_info && media.video_info.variants) || [];
    const mp4 = variants
      .filter((v) => v.content_type === "video/mp4")
      .sort((a, b) => (b.bitrate || 0) - (a.bitrate || 0));
    return (mp4[0] && mp4[0].url) || media.media_url_https || "";
  }

  function normalizeTweet(result) {
    if (!result || typeof result !== "object") return null;
    // Unwrap tweets that come inside a visibility wrapper
    let t = result;
    if (t.__typename === "TweetWithVisibilityResults" && t.tweet) t = t.tweet;
    const legacy = t.legacy || {};
    const id = t.rest_id || legacy.id_str;
    if (!id) return null;

    // Author (X has been migrating fields from user.legacy -> user.core)
    const user = (t.core && t.core.user_results && t.core.user_results.result) || {};
    const uLegacy = user.legacy || {};
    const uCore = user.core || {};
    const handle = uCore.screen_name || uLegacy.screen_name || "";
    const name = uCore.name || uLegacy.name || "";
    const avatar =
      (user.avatar && user.avatar.image_url) ||
      uLegacy.profile_image_url_https ||
      "";

    // Text: long-form "note tweet" wins over the truncated legacy text
    const note =
      t.note_tweet &&
      t.note_tweet.note_tweet_results &&
      t.note_tweet.note_tweet_results.result;
    const text = (note && note.text) || legacy.full_text || legacy.text || "";

    const entities = (note && note.entity_set) || legacy.entities || {};
    const hashtags = (entities.hashtags || []).map((h) => h.text).filter(Boolean);
    const mentions = (entities.user_mentions || [])
      .map((m) => m.screen_name)
      .filter(Boolean);
    const links = (entities.urls || [])
      .map((u) => u.expanded_url || u.url)
      .filter(Boolean);

    const mediaList =
      (legacy.extended_entities && legacy.extended_entities.media) ||
      (legacy.entities && legacy.entities.media) ||
      [];
    const media = mediaList.map((m) => ({
      type: m.type, // photo | video | animated_gif
      url: m.type === "photo" ? m.media_url_https : bestVideoUrl(m),
      thumb: m.media_url_https,
    }));

    let created_at = null;
    if (legacy.created_at) {
      const d = new Date(legacy.created_at);
      if (!isNaN(d)) created_at = d.toISOString();
    }

    const metrics = {
      likes: legacy.favorite_count || 0,
      retweets: legacy.retweet_count || 0,
      replies: legacy.reply_count || 0,
      quotes: legacy.quote_count || 0,
      bookmarks: legacy.bookmark_count || 0,
      views: (t.views && Number(t.views.count)) || 0,
    };

    return {
      id: String(id),
      url: handle
        ? `https://x.com/${handle}/status/${id}`
        : `https://x.com/i/status/${id}`,
      text,
      lang: legacy.lang || null,
      created_at,
      author: { name, handle, avatar },
      media,
      metrics,
      hashtags,
      mentions,
      links,
      is_quote: !!legacy.is_quote_status,
      captured_at: new Date().toISOString(),
      source: "x-bookmarks",
    };
  }

  // ---------------------------------------------------------------------------
  // Auto-scroll loop
  // ---------------------------------------------------------------------------
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function autoScroll() {
    let stagnant = 0;
    let lastCount = -1;
    let lastHeight = -1;
    // Start from the top so the very first batch is (re)loaded and captured.
    window.scrollTo(0, 0);
    await sleep(800);

    while (capturing) {
      window.scrollTo(0, document.documentElement.scrollHeight);
      setStatus("Cargando marcadores… (scroll automático)");
      await sleep(1400);

      const grew = store.size > lastCount;
      const heightGrew = document.documentElement.scrollHeight > lastHeight;
      lastCount = store.size;
      lastHeight = document.documentElement.scrollHeight;

      if (!grew && !heightGrew) {
        stagnant++;
        setStatus(`Comprobando el final… (${stagnant}/6)`);
        // Nudge up and down to shake loose any lazy loading.
        window.scrollBy(0, -400);
        await sleep(400);
      } else {
        stagnant = 0;
      }

      if (stagnant >= 6) {
        capturing = false;
        setStatus(`✅ Terminado: ${store.size} marcadores capturados.`);
        updateButtons();
        break;
      }
    }
  }

  // ---------------------------------------------------------------------------
  // UI
  // ---------------------------------------------------------------------------
  function download() {
    const arr = Array.from(store.values()).sort((a, b) =>
      (b.created_at || "").localeCompare(a.created_at || "")
    );
    const blob = new Blob([JSON.stringify(arr)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 10);
    a.href = url;
    a.download = `x-bookmarks-${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    setStatus(`⬇ Descargado x-bookmarks-${stamp}.json (${arr.length})`);
  }

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }
  function render() {
    if (countEl) countEl.textContent = String(store.size);
  }
  function updateButtons() {
    if (!panel) return;
    const start = panel.querySelector("#xf-start");
    const stop = panel.querySelector("#xf-stop");
    if (start) start.style.display = capturing ? "none" : "";
    if (stop) stop.style.display = capturing ? "" : "none";
  }

  function buildPanel() {
    if (panel || !document.body) return;
    panel = document.createElement("div");
    panel.id = "xf-panel";
    panel.innerHTML = `
      <style>
        #xf-panel{position:fixed;top:16px;right:16px;z-index:2147483647;width:260px;
          font:13px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
          background:#15202b;color:#e7e9ea;border:1px solid #38444d;border-radius:14px;
          box-shadow:0 8px 28px rgba(0,0,0,.45);overflow:hidden}
        #xf-panel .xf-h{display:flex;align-items:center;gap:8px;padding:12px 14px;
          background:linear-gradient(135deg,#1d9bf0,#0f6fbf);font-weight:700;color:#fff}
        #xf-panel .xf-b{padding:14px}
        #xf-panel .xf-count{font-size:34px;font-weight:800;line-height:1;color:#1d9bf0}
        #xf-panel .xf-count small{font-size:12px;font-weight:600;color:#8b98a5;margin-left:6px}
        #xf-panel .xf-status{margin:10px 0 12px;min-height:34px;color:#8b98a5;font-size:12px}
        #xf-panel button{width:100%;padding:9px 12px;margin-top:8px;border:0;border-radius:9px;
          font-weight:700;font-size:13px;cursor:pointer}
        #xf-start{background:#1d9bf0;color:#fff}
        #xf-stop{background:#f4212e;color:#fff;display:none}
        #xf-dl{background:#eff3f4;color:#0f1419}
        #xf-panel button:hover{filter:brightness(1.08)}
        #xf-panel .xf-tip{margin-top:10px;font-size:11px;color:#8b98a5}
        #xf-min{position:absolute;top:10px;right:12px;background:transparent;width:auto;
          margin:0;padding:0;color:#fff;font-size:16px;line-height:1}
      </style>
      <div class="xf-h">🔖 xfilters<button id="xf-min" title="Minimizar">–</button></div>
      <div class="xf-b">
        <div><span class="xf-count" id="xf-count">0</span><small>marcadores</small></div>
        <div class="xf-status" id="xf-status">Ve a tu página de Marcadores y pulsa Iniciar.</div>
        <button id="xf-start">▶ Iniciar captura</button>
        <button id="xf-stop">⏸ Detener</button>
        <button id="xf-dl">⬇ Descargar JSON</button>
        <div class="xf-tip">Todo ocurre en tu navegador. No se envía nada.</div>
      </div>`;
    document.body.appendChild(panel);
    statusEl = panel.querySelector("#xf-status");
    countEl = panel.querySelector("#xf-count");

    panel.querySelector("#xf-start").addEventListener("click", () => {
      if (capturing) return;
      if (!/\/i\/bookmarks/.test(location.pathname)) {
        setStatus("⚠ Abre x.com/i/bookmarks primero.");
      }
      capturing = true;
      updateButtons();
      autoScroll();
    });
    panel.querySelector("#xf-stop").addEventListener("click", () => {
      capturing = false;
      updateButtons();
      setStatus(`Pausado: ${store.size} capturados. Puedes descargar o reanudar.`);
    });
    panel.querySelector("#xf-dl").addEventListener("click", download);
    panel.querySelector("#xf-min").addEventListener("click", () => {
      const body = panel.querySelector(".xf-b");
      body.style.display = body.style.display === "none" ? "" : "none";
    });
    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", buildPanel);
  } else {
    buildPanel();
  }
  // X is a SPA; make sure the panel survives client-side re-renders.
  const iv = setInterval(() => {
    if (!document.getElementById("xf-panel") && document.body) {
      panel = null;
      buildPanel();
    }
  }, 2000);
  window.addEventListener("beforeunload", () => clearInterval(iv));
})();
