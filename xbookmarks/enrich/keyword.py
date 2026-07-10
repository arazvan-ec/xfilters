"""Free, offline enrichment by keyword/domain rules (ported from PR #2's enrich.mjs).

Same call signature as ``ai.generate_enrichment`` (returns ``summary``/``topic``/
``tags``) so it can be swapped in as the enricher. No summary is produced — that is
the LLM enricher's job — but it assigns a primary category (``topic``) and all
matching categories as ``tags``, fully locally and for free.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from ..models import Bookmark

# Category rules: keyword regexes + domain hints. Tuned for ES/EN content.
CATEGORIES = [
    {"name": "IA & Machine Learning",
     "kw": [r"\bia\b", r"\bai\b", "llm", "gpt", "claude", "gemini", "openai", "anthropic",
            "machine learning", "aprendizaje", "deep learning", "neural", "modelo", "prompt",
            "agente", "agent", "rag", "embedding", "hugging ?face", "mistral",
            "stable diffusion", "midjourney"],
     "dom": ["huggingface.co", "openai.com", "anthropic.com"]},
    {"name": "Programación & Dev",
     "kw": ["javascript", "typescript", "python", "react", "node", r"rust\b", "golang",
            r"\bgo\b", "código", "code", "programa", "developer", "framework", r"api\b",
            "backend", "frontend", "docker", "kubernetes", "css", "html", "sql", r"git\b",
            "open ?source", "librería", "library", "bug", "deploy"],
     "dom": ["github.com", "gitlab.com", "stackoverflow.com", "npmjs.com", "dev.to",
             "vercel.com"]},
    {"name": "Economía & Finanzas",
     "kw": ["econom", "finanz", "mercado", "bolsa", "inflación", "tipos de interés", "banco",
            "inversión", "invertir", "acciones", "dividendo", "cripto", "bitcoin", "ethereum",
            "startup funding", "valoración", "pib", "déficit"],
     "dom": ["bloomberg.com", "ft.com", "cincodias.elpais.com", "expansion.com"]},
    {"name": "Política & Actualidad",
     "kw": ["gobierno", "política", "elecciones", "ministr", "president", "congreso", "senado",
            r"ley\b", "parlamento", "psoe", r"\bpp\b", r"ue\b", "unión europea", "geopolít",
            "guerra", "ucrania", "gaza"],
     "dom": []},
    {"name": "Ciencia & Salud",
     "kw": ["ciencia", "científic", "estudio", "investigación", "física", "biolog", "química",
            "astronom", "espacio", "nasa", "salud", "medicina", "clínic", "vacuna", "cerebro",
            "neurocienc"],
     "dom": ["nature.com", "science.org", "arxiv.org", "nih.gov"]},
    {"name": "Diseño & UX",
     "kw": ["diseño", "design", r"\bux\b", r"\bui\b", "tipografía", "typography", "figma",
            "branding", "logo", "paleta", "interfaz", "interface", "usabilidad", "wireframe"],
     "dom": ["figma.com", "dribbble.com", "behance.net"]},
    {"name": "Marketing & Redes",
     "kw": ["marketing", r"\bseo\b", r"\bsem\b", "growth", "audiencia", "engagement", "viral",
            "contenido", "content", "newsletter", "copywriting", "publicidad", r"ads\b",
            "campaña", "funnel", "conversión"],
     "dom": []},
    {"name": "Periodismo & Medios",
     "kw": ["periodismo", "periodista", "noticia", "reportaje", r"medios\b", "redacción",
            "titular", "fake news", "desinformación", "fact.?check", "editorial", "crónica"],
     "dom": ["elconfidencial.com", "elpais.com", "elmundo.es", "reuters.com", "apnews.com"]},
    {"name": "Productividad & Herramientas",
     "kw": ["productividad", "herramienta", r"tool\b", r"app\b", "aplicación", "notion",
            "obsidian", "automatiz", "workflow", "flujo de trabajo", "plantilla", "template",
            "atajo", "hack", r"tip\b", "truco"],
     "dom": ["notion.so", "zapier.com"]},
    {"name": "Cultura & Entretenimiento",
     "kw": ["película", "film", r"serie\b", "netflix", "música", "music", r"libro\b",
            r"book\b", "leer", r"arte\b", "museo", "videojuego", r"game\b", "gaming", "cultura",
            "documental"],
     "dom": ["youtube.com", "youtu.be", "spotify.com", "imdb.com"]},
    {"name": "Deportes",
     "kw": ["fútbol", "futbol", "baloncesto", r"\bnba\b", r"liga\b", "champions", "tenis",
            "fórmula 1", r"\bf1\b", "motogp", "deporte", "partido", r"gol\b", "madrid", "barça",
            "barca"],
     "dom": ["marca.com", "as.com"]},
]


def _domains(links: list[str]) -> list[str]:
    out = []
    for u in links or []:
        try:
            host = (urlparse(u).hostname or "").lower()
        except ValueError:
            continue
        if host:
            out.append(host[4:] if host.startswith("www.") else host)
    return out


def categorize(b: Bookmark) -> list[str]:
    """Return matching category names, most-relevant first."""
    hay = "  ".join(
        [
            (b.text or "").lower(),
            " ".join(b.hashtags or []).lower(),
            " ".join(b.links or []).lower(),
            (b.author_handle or "").lower(),
        ]
    )
    domains = _domains(b.links)
    scores = []
    for cat in CATEGORIES:
        score = sum(1 for k in cat["kw"] if re.search(k, hay, re.I))
        score += sum(2 for d in cat["dom"] if any(h == d or h.endswith("." + d) for h in domains))
        if score > 0:
            scores.append((cat["name"], score))
    scores.sort(key=lambda s: s[1], reverse=True)
    return [name for name, _ in scores]


def keyword_enrich(b: Bookmark) -> dict:
    tags = categorize(b)
    return {
        "summary": "",
        "topic": tags[0] if tags else "Sin categoría",
        "tags": tags or ["Sin categoría"],
    }
