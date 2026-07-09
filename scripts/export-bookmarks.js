// Export your X bookmarks to JSON — no API key, using your own logged-in session.
//
// How to use:
//   1. Open https://x.com/i/bookmarks in your browser (logged in).
//   2. Open DevTools → Console, paste this whole file, press Enter.
//   3. It auto-scrolls to load bookmarks, then copies a JSON array to your
//      clipboard (and logs it). Save it as bookmarks.json and run:
//        python -m xbookmarks ingest bookmarks.json
//
// This only reads what your session already renders (no automation of X beyond
// scrolling your own bookmarks page). Selectors may need updating if X changes
// its DOM — this is the fragile-by-nature acquisition step.

(async () => {
  const byId = new Map();

  const parseArticle = (art) => {
    const statusLink = art.querySelector('a[href*="/status/"]');
    if (!statusLink) return;
    const m = statusLink.getAttribute("href").match(/\/([^/]+)\/status\/(\d+)/);
    if (!m) return;
    const [, handle, id] = m;
    if (byId.has(id)) return;

    const nameEl = art.querySelector('[data-testid="User-Name"]');
    const author_name = nameEl ? nameEl.querySelector("span")?.innerText || "" : "";
    const text = art.querySelector('[data-testid="tweetText"]')?.innerText || "";
    const created_at = art.querySelector("time")?.getAttribute("datetime") || "";
    const media = [...art.querySelectorAll('img[src*="twimg.com/media"]')].map((img) => ({
      type: "photo",
      url: img.src,
    }));

    byId.set(id, {
      id,
      url: `https://x.com/${handle}/status/${id}`,
      author_handle: handle,
      author_name,
      text,
      created_at,
      media,
    });
  };

  const collect = () => document.querySelectorAll("article").forEach(parseArticle);

  let last = -1;
  let stable = 0;
  while (stable < 5) {
    collect();
    window.scrollBy(0, window.innerHeight * 2);
    await new Promise((r) => setTimeout(r, 800));
    if (byId.size === last) stable++;
    else {
      stable = 0;
      last = byId.size;
    }
  }

  const out = JSON.stringify([...byId.values()], null, 2);
  window.__bookmarks = out;
  try {
    await navigator.clipboard.writeText(out);
    console.log(`Exported ${byId.size} bookmarks — copied to clipboard.`);
  } catch {
    console.log(`Exported ${byId.size} bookmarks — copy from window.__bookmarks below:`);
  }
  console.log(out);
})();
