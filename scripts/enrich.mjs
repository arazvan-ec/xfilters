#!/usr/bin/env node
/*
 * xfilters — enrichment / categorization
 * --------------------------------------
 * Reads the raw bookmarks captured by the browser extension and adds the
 * "extra information" needed to filter them:
 *   - category   : a single primary category tag (what the frontend filters on)
 *   - tags       : every category that matched (a bookmark can touch several)
 *   - domain     : primary linked domain (if any)
 *   - has_media  : convenience boolean
 *   - year       : year of the tweet (handy secondary filter)
 *
 * Categorization is keyword/domain based and fully local. Tune CATEGORIES
 * below to taste — re-run the script and the frontend updates.
 *
 * Usage:
 *   node scripts/enrich.mjs [input.json]
 *   # default input: data/raw-bookmarks.json, falling back to data/bookmarks.sample.json
 *
 * Outputs:
 *   data/bookmarks.json   canonical enriched array (portable, for any tool)
 *   data/bookmarks.js     window.__XFILTERS__ = {...}  (so index.html works from file://)
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const DATA = path.join(ROOT, "data");

// --- category rules --------------------------------------------------------
// Order matters only for display; scoring picks the highest match count.
const CATEGORIES = [
  { name: "IA & Machine Learning", kw: ["\\bia\\b","\\bai\\b","llm","gpt","claude","gemini","openai","anthropic","machine learning","aprendizaje","deep learning","neural","modelo","prompt","agente","agent","rag","embedding","hugging ?face","mistral","stable diffusion","midjourney"], dom: ["huggingface.co","openai.com","anthropic.com"] },
  { name: "Programación & Dev", kw: ["javascript","typescript","python","react","node","rust\\b","golang","\\bgo\\b","código","code","programa","developer","framework","api\\b","backend","frontend","docker","kubernetes","css","html","sql","git\\b","open ?source","librería","library","bug","deploy"], dom: ["github.com","gitlab.com","stackoverflow.com","npmjs.com","dev.to","vercel.com"] },
  { name: "Economía & Finanzas", kw: ["econom","finanz","mercado","bolsa","inflación","tipos de interés","banco","inversión","invertir","acciones","dividendo","cripto","bitcoin","ethereum","startup funding","valoración","pib","déficit"], dom: ["bloomberg.com","ft.com","cincodias.elpais.com","expansion.com"] },
  { name: "Política & Actualidad", kw: ["gobierno","política","elecciones","ministr","president","congreso","senado","ley\\b","parlamento","psoe","\\bpp\\b","ue\\b","unión europea","geopolít","guerra","ucrania","gaza"], dom: [] },
  { name: "Ciencia & Salud", kw: ["ciencia","científic","estudio","investigación","física","biolog","química","astronom","espacio","nasa","salud","medicina","clínic","vacuna","cerebro","neurocienc"], dom: ["nature.com","science.org","arxiv.org","nih.gov"] },
  { name: "Diseño & UX", kw: ["diseño","design","\\bux\\b","\\bui\\b","tipografía","typography","figma","branding","logo","paleta","interfaz","interface","usabilidad","wireframe"], dom: ["figma.com","dribbble.com","behance.net"] },
  { name: "Marketing & Redes", kw: ["marketing","\\bseo\\b","\\bsem\\b","growth","audiencia","engagement","viral","contenido","content","newsletter","copywriting","publicidad","ads\\b","campaña","funnel","conversión"], dom: [] },
  { name: "Periodismo & Medios", kw: ["periodismo","periodista","noticia","reportaje","medios\\b","redacción","titular","fake news","desinformación","fact.?check","editorial","crónica"], dom: ["elconfidencial.com","elpais.com","elmundo.es","reuters.com","apnews.com"] },
  { name: "Productividad & Herramientas", kw: ["productividad","herramienta","tool\\b","app\\b","aplicación","notion","obsidian","automatiz","workflow","flujo de trabajo","plantilla","template","atajo","hack","tip\\b","truco"], dom: ["notion.so","zapier.com"] },
  { name: "Cultura & Entretenimiento", kw: ["película","film","serie\\b","netflix","música","music","libro\\b","book\\b","leer","arte\\b","museo","videojuego","game\\b","gaming","cultura","documental"], dom: ["youtube.com","youtu.be","spotify.com","imdb.com"] },
  { name: "Deportes", kw: ["fútbol","futbol","baloncesto","\\bnba\\b","liga\\b","champions","tenis","fórmula 1","\\bf1\\b","motogp","deporte","partido","gol\\b","madrid","barça","barca"], dom: ["marca.com","as.com"] },
];

const norm = (s) => (s || "").toLowerCase();

function categorize(bm) {
  const hay = [
    norm(bm.text),
    (bm.hashtags || []).map(norm).join(" "),
    (bm.links || []).map(norm).join(" "),
    norm(bm.author && bm.author.handle),
  ].join("  ");
  const domains = (bm.links || [])
    .map((u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return ""; } })
    .filter(Boolean);

  const scores = [];
  for (const cat of CATEGORIES) {
    let score = 0;
    for (const k of cat.kw) if (new RegExp(k, "i").test(hay)) score++;
    for (const d of cat.dom) if (domains.some((h) => h === d || h.endsWith("." + d))) score += 2;
    if (score > 0) scores.push({ name: cat.name, score });
  }
  scores.sort((a, b) => b.score - a.score);
  const tags = scores.map((s) => s.name);
  return {
    category: tags[0] || "Sin categoría",
    tags: tags.length ? tags : ["Sin categoría"],
  };
}

function enrich(bm) {
  const { category, tags } = categorize(bm);
  let domain = null;
  if (bm.links && bm.links[0]) {
    try { domain = new URL(bm.links[0]).hostname.replace(/^www\./, ""); } catch {}
  }
  const year = bm.created_at ? new Date(bm.created_at).getUTCFullYear() : null;
  return {
    ...bm,
    category,
    tags,
    domain,
    has_media: Array.isArray(bm.media) && bm.media.length > 0,
    year,
  };
}

// --- run -------------------------------------------------------------------
function pickInput() {
  const arg = process.argv[2];
  const candidates = [
    arg,
    path.join(DATA, "raw-bookmarks.json"),
    path.join(DATA, "bookmarks.sample.json"),
  ].filter(Boolean);
  for (const c of candidates) {
    const p = path.isAbsolute(c) ? c : path.join(ROOT, c);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

const input = pickInput();
if (!input) {
  console.error("No input found. Pass a file: node scripts/enrich.mjs <capture>.json");
  process.exit(1);
}

const rawText = fs.readFileSync(input, "utf8");
let raw;
try {
  raw = JSON.parse(rawText);
} catch (e) {
  console.error("Input is not valid JSON:", e.message);
  process.exit(1);
}
if (!Array.isArray(raw)) {
  // tolerate {bookmarks:[...]} shape
  raw = raw.bookmarks || raw.data || [];
}

// De-dupe by id (in case several captures are concatenated) and enrich.
const byId = new Map();
for (const bm of raw) if (bm && bm.id) byId.set(String(bm.id), bm);
const enriched = Array.from(byId.values()).map(enrich).sort((a, b) =>
  (b.created_at || "").localeCompare(a.created_at || "")
);

const counts = {};
for (const b of enriched) counts[b.category] = (counts[b.category] || 0) + 1;

const payload = {
  generated_at: new Date().toISOString(),
  source: path.relative(ROOT, input),
  count: enriched.length,
  categories: Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([name, count]) => ({ name, count })),
  bookmarks: enriched,
};

fs.mkdirSync(DATA, { recursive: true });
fs.writeFileSync(path.join(DATA, "bookmarks.json"), JSON.stringify(payload, null, 2));
fs.writeFileSync(
  path.join(DATA, "bookmarks.js"),
  "// Auto-generated by scripts/enrich.mjs — do not edit by hand.\n" +
    "window.__XFILTERS__ = " + JSON.stringify(payload) + ";\n"
);

console.log(`Enriched ${enriched.length} bookmarks from ${path.relative(ROOT, input)}`);
console.log("Categories:");
for (const { name, count } of payload.categories) console.log(`  ${String(count).padStart(4)}  ${name}`);
console.log("\nWrote data/bookmarks.json and data/bookmarks.js");
