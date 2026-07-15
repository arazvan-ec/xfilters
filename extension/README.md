# xfilters — extensión para capturar tus marcadores de X

Extensión de Chrome (Manifest V3) que exporta **todos** tus marcadores de
X/Twitter a un JSON limpio. Corre entera en tu navegador; **no envía nada** ni
lee cookies o tokens.

## Instalar (modo desarrollador, sin tienda)

1. Abre `chrome://extensions` en Chrome (o Edge/Brave: `edge://extensions`).
2. Activa **«Modo de desarrollador»** (arriba a la derecha).
3. Pulsa **«Cargar descomprimida»** / «Load unpacked».
4. Selecciona esta carpeta `extension/`.

> Requiere Chrome/Edge/Brave 111 o superior (usa content scripts en el «MAIN
> world»).

## Instalar en Android (Kiwi / Lemur / Mises Browser)

Chrome/Safari de móvil **no** admiten extensiones, pero los navegadores basados
en Chromium que sí lo hacen te permiten capturar desde el propio teléfono. Kiwi
Browser está descontinuado; sus forks **Lemur Browser** o **Mises Browser**
funcionan igual y siguen mantenidos (usa una versión basada en Chromium ≥ 111).

1. Descarga el paquete **`dist/xfilters-extension.zip`** del repo en el teléfono
   (en GitHub: abre el archivo → «Download raw file»). Se guarda en *Descargas*.
2. Abre Kiwi/Lemur/Mises → menú **⋮** → **Extensiones**.
3. Activa **«Modo de desarrollador»** (arriba a la derecha).
4. Pulsa **«+ (from .zip/.crx/.user.js)»** y elige el `.zip` de *Descargas*.
5. Confirma. La extensión queda instalada.

Luego inicia sesión en X dentro de ese navegador y sigue los pasos de «Usar».
Como en el móvil no puedes ejecutar el pipeline de Python, cuando descargues el
JSON **súbelo a Google Drive** (o compártelo): descárgalo después en un
ordenador y sigue el mismo flujo de «Usar» (`python -m xbookmarks ingest ...` +
`make build`) para enriquecerlo y montar el sitio.

> Consejo móvil: si el contador se para antes de tiempo, arrastra con el dedo
> hacia arriba y abajo en la página de marcadores mientras la captura está
> activa; se siguen capturando igual (el scroll automático es solo una ayuda).

## Usar

1. Inicia sesión en X y ve a tu página de marcadores:
   **https://x.com/i/bookmarks**
2. Verás arriba a la derecha un panel **🔖 xfilters**.
3. Pulsa **«▶ Iniciar captura»**. La extensión hará scroll automático y el
   contador irá subiendo a medida que carga cada página de marcadores.
4. Cuando llegue al final se detiene solo (o púlsalo tú con «⏸ Detener»).
5. Pulsa **«⬇ Descargar JSON»**. Se guarda `x-bookmarks-AAAA-MM-DD.json`.

Luego, en la raíz del repo:

```bash
python -m xbookmarks ingest ~/Descargas/x-bookmarks-*.json
make build          # equivale a: python -m xbookmarks build --enricher keyword
```

y abre `site/index.html`.

## Cómo captura los datos (por qué es fiable)

En vez de leer el HTML de la página (que X ofusca a propósito y además recicla
al hacer scroll), la extensión **intercepta las respuestas de la API GraphQL
`Bookmarks`** que tu propio navegador descarga. De ahí saca los objetos
completos de cada tweet: texto (incluidos hilos/notas largas), autor, media,
métricas, fecha, hashtags, menciones y enlaces. Cada tweet se de-duplica por id.

## Consejos y resolución de problemas

- **Se detiene demasiado pronto**: X a veces tarda en cargar. Pulsa «▶ Iniciar»
  otra vez; sigue acumulando (no duplica) y continúa desde donde estaba.
- **El contador no sube**: asegúrate de estar en `x.com/i/bookmarks` y de que la
  pestaña esté visible (algunos navegadores pausan el scroll en pestañas en
  segundo plano). Deja la pestaña en primer plano durante la captura.
- **Muchísimos marcadores**: es normal que tarde varios minutos; deja que haga
  su trabajo. Puedes descargar por lotes: detener, descargar, seguir.
- **No aparece el panel**: recarga la página de marcadores tras instalar la
  extensión.

## Privacidad

Todo ocurre localmente. El código está en `collector.js` (un único archivo, sin
dependencias) para que puedas auditarlo. No hay llamadas de red salientes ni
permisos de almacenamiento; el único permiso es ejecutarse en `x.com`/
`twitter.com`.
