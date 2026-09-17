#!/usr/bin/env python3
"""
Génère les PDF du PRI à partir des documents Markdown de docs/.

Chaîne : Markdown -> HTML (mise en page d'impression A4) -> PDF via Chromium.

Deux profils :
    rapport   — le dossier complet (couverture, sommaire, les trois parties)
    synthese  — la note de synthèse, format court sans couverture ni sommaire

Usage :
    python3 tools/build_pdf.py                       # les deux profils
    python3 tools/build_pdf.py --profile synthese
"""

from __future__ import annotations

import argparse
import asyncio
import html
import os
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Chromium pré-installé de l'environnement : la version empaquetée avec Playwright
# ne correspond pas toujours, on pointe donc explicitement le binaire présent.
CHROMIUM = Path(
    os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
)

# Ordre de lecture du rapport : besoins -> ce qui existe -> quels modèles.
PARTS = [
    ("I", "00-cadrage-projet.md", "Cadrage du projet"),
    ("II", "02-etat-des-lieux-et-justification-des-choix.md", "État des lieux de l'existant"),
    ("III", "01-etat-de-l-art-et-comparaison-modeles.md", "État de l'art et comparaison des modèles"),
]

# Renvois inter-documents : en PDF, les fichiers deviennent des parties.
FILE_REFS = {
    "00-cadrage-projet.md": "partie I",
    "02-etat-des-lieux-et-justification-des-choix.md": "partie II",
    "01-etat-de-l-art-et-comparaison-modeles.md": "partie III",
}

TITLE = "IA embarquée pour la perception des véhicules autonomes en logistique hospitalière"
SUBTITLE = "État des lieux, état de l'art et choix technologiques"

SYNTHESIS = "03-synthese.md"

PROFILES = {
    "rapport": "build/PRI_IA_Perception_Rapport.pdf",
    "synthese": "build/PRI_IA_Perception_Synthese.pdf",
}


def clean_markdown(text: str) -> str:
    """Retire ce qui n'a de sens que dans le dépôt (sommaires locaux, liens de navigation)."""
    # Sommaire local en liste (partie III) : du titre jusqu'au séparateur suivant.
    text = re.sub(r"^## Sommaire\n.*?^---\n", "", text, flags=re.S | re.M)
    # Sommaire local en citation (partie II).
    text = re.sub(r"^> \*\*Sommaire\*\*\n(?:^>.*\n)*", "", text, flags=re.M)
    # Pied de page de navigation entre documents.
    text = re.sub(r"^\*Documents? liés? ?:.*$", "", text, flags=re.M)
    text = re.sub(r"^\*Suite ?:.*$", "", text, flags=re.M)

    # Liens vers les autres fichiers -> renvoi textuel à la partie.
    def deref(m: re.Match) -> str:
        label, target = m.group(1), m.group(2)
        for fname, part in FILE_REFS.items():
            if target.startswith(fname):
                return f"{label} ({part})"
        return m.group(0)

    text = re.sub(r"\[([^\]]+)\]\((\d\d-[^)]+\.md[^)]*)\)", deref, text)

    # Une rubrique en gras suivie immédiatement d'une liste (bibliographies) :
    # sans ligne vide, le convertisseur aplatit la liste en paragraphe.
    text = re.sub(r"^(\*\*[^*\n]+\*\*)\n(?=- )", r"\1\n\n", text, flags=re.M)
    return text


def split_title(text: str) -> tuple[str, list[str], str]:
    """Sépare le titre H1, les lignes d'italique de tête, et le corps."""
    lines = text.splitlines()
    title, meta, start = "", [], 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            start = i + 1
            break
    for line in lines[start:]:
        if line.startswith("*") and line.endswith("*") and len(line) > 2:
            meta.append(line.strip("*").strip())
            start += 1
        elif not line.strip():
            start += 1
        else:
            break
    return title, meta, "\n".join(lines[start:])


def slugify(text: str, seen: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
    slug, n = base, 2
    while slug in seen:
        slug, n = f"{base}-{n}", n + 1
    seen.add(slug)
    return slug


def build_synthesis_html(today: str) -> str:
    """Note de synthèse : un seul document, pas de couverture ni de sommaire."""
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    raw = clean_markdown((DOCS / SYNTHESIS).read_text(encoding="utf-8"))
    _title, meta, content = split_title(raw)
    rendered = md.convert(content)
    rendered = link_sources(rendered)

    return SYNTHESIS_TEMPLATE.format(
        title=html.escape(TITLE),
        today=html.escape(today),
        meta="<br>".join(html.escape(m) for m in meta),
        body=rendered,
    )


def link_sources(rendered: str) -> str:
    """Bibliographie : faire apparaître l'URL sous l'intitulé (lecture papier)."""
    return re.sub(
        r'<li><a href="(https?://[^"]+)">(.*?)</a></li>',
        lambda m: f'<li class="src"><a href="{m.group(1)}">{m.group(2)}</a>'
                  f'<span class="src-url">{m.group(1)}</span></li>',
        rendered,
        flags=re.S,
    )


def build_html(today: str) -> str:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    seen: set[str] = set()
    toc: list[tuple[int, str, str]] = []
    body: list[str] = []

    for numeral, fname, part_title in PARTS:
        raw = clean_markdown((DOCS / fname).read_text(encoding="utf-8"))
        _doc_title, meta, content = split_title(raw)

        part_id = slugify(f"partie-{numeral}", seen)
        toc.append((0, part_id, f"Partie {numeral} — {part_title}"))

        md.reset()
        rendered = md.convert(content)

        # Ancres + collecte du sommaire sur les H2.
        def anchor(m: re.Match) -> str:
            text = re.sub(r"<[^>]+>", "", m.group(2))
            sid = slugify(text, seen)
            toc.append((1, sid, text))
            return f'<h2 id="{sid}"{m.group(1)}>{m.group(2)}</h2>'

        rendered = re.sub(r"<h2([^>]*)>(.*?)</h2>", anchor, rendered, flags=re.S)

        rendered = link_sources(rendered)

        meta_html = ""
        if meta:
            meta_html = '<p class="part-meta">' + "<br>".join(html.escape(m) for m in meta) + "</p>"

        body.append(
            f'<section class="part" id="{part_id}">'
            f'<div class="part-head"><span class="part-num">Partie {numeral}</span>'
            f"<h1>{html.escape(part_title)}</h1>{meta_html}</div>\n{rendered}</section>"
        )

    toc_html = "\n".join(
        f'<li class="lvl{lvl}"><a href="#{sid}">{html.escape(text)}</a></li>'
        for lvl, sid, text in toc
    )

    return TEMPLATE.format(
        title=html.escape(TITLE),
        subtitle=html.escape(SUBTITLE),
        today=html.escape(today),
        toc=toc_html,
        body="\n".join(body),
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  :root {{
    --ink: #16191d;
    --muted: #5b6470;
    --rule: #d7dce3;
    --accent: #1f4e79;
    --soft: #f4f6f9;
  }}
  * {{ box-sizing: border-box; }}
  html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{
    font-family: "DejaVu Sans", "Noto Sans", "Liberation Sans", sans-serif;
    font-size: 9.6pt; line-height: 1.5; color: var(--ink); margin: 0;
  }}

  /* ---------- Couverture ---------- */
  .cover {{ height: 247mm; display: flex; flex-direction: column; page-break-after: always; }}
  .cover-top {{ border-top: 3px solid var(--accent); padding-top: 10mm; }}
  .cover-kicker {{ font-size: 10pt; letter-spacing: .14em; text-transform: uppercase;
                   color: var(--accent); font-weight: 700; }}
  .cover-project {{ font-size: 10.5pt; color: var(--muted); margin-top: 2mm; }}
  .cover-mid {{ margin-top: auto; margin-bottom: auto; }}
  .cover h1 {{ font-size: 25pt; line-height: 1.22; margin: 0 0 6mm; border: 0; padding: 0; }}
  .cover h2 {{ font-size: 13.5pt; font-weight: 400; color: var(--muted);
               margin: 0; border: 0; padding: 0; }}
  .cover-rule {{ height: 2px; background: var(--accent); width: 46mm; margin: 8mm 0; }}
  .cover-meta {{ font-size: 10pt; }}
  .cover-meta table {{ border: 0; width: auto; font-size: 10pt; }}
  .cover-meta td {{ border: 0; padding: 1.1mm 9mm 1.1mm 0; vertical-align: top; }}
  .cover-meta td:first-child {{ color: var(--muted); white-space: nowrap; }}
  .cover-foot {{ border-top: 1px solid var(--rule); padding-top: 4mm;
                 font-size: 8.5pt; color: var(--muted); }}
  .todo {{ color: #9aa3ae; font-style: italic; }}

  /* ---------- Sommaire ---------- */
  .toc {{ page-break-after: always; }}
  .toc h2 {{ font-size: 15pt; border-bottom: 2px solid var(--accent);
             padding-bottom: 2.5mm; margin: 0 0 6mm; }}
  .toc ul {{ list-style: none; padding: 0; margin: 0; }}
  .toc li a {{ text-decoration: none; color: var(--ink); }}
  .toc li.lvl0 {{ margin: 5.5mm 0 1.5mm; font-weight: 700; font-size: 10.5pt;
                  color: var(--accent); border-bottom: 1px solid var(--rule);
                  padding-bottom: 1.5mm; }}
  .toc li.lvl0 a {{ color: var(--accent); }}
  .toc li.lvl1 {{ padding-left: 6mm; font-size: 9.2pt; color: #38414c; margin: .9mm 0; }}

  /* ---------- Parties ---------- */
  .part {{ page-break-before: always; }}
  .part-head {{ border-bottom: 2px solid var(--accent); padding-bottom: 4mm; margin-bottom: 8mm; }}
  .part-num {{ font-size: 8.5pt; letter-spacing: .16em; text-transform: uppercase;
               color: var(--accent); font-weight: 700; }}
  .part-head h1 {{ font-size: 19pt; margin: 2mm 0 0; border: 0; padding: 0; line-height: 1.25; }}
  .part-meta {{ font-size: 8.5pt; color: var(--muted); margin: 3mm 0 0; }}

  h2 {{ font-size: 13pt; margin: 9mm 0 3mm; padding-bottom: 1.5mm;
        border-bottom: 1px solid var(--rule); page-break-after: avoid; }}
  h3 {{ font-size: 10.8pt; margin: 6mm 0 2mm; color: var(--accent); page-break-after: avoid; }}
  h4 {{ font-size: 9.8pt; margin: 4.5mm 0 1.5mm; page-break-after: avoid; }}
  p {{ margin: 0 0 2.6mm; text-align: justify; }}
  ul, ol {{ margin: 0 0 2.6mm; padding-left: 5.5mm; }}
  li {{ margin-bottom: 1.1mm; }}
  strong {{ font-weight: 700; }}
  a {{ color: var(--accent); text-decoration: none; word-break: break-word; }}
  hr {{ border: 0; border-top: 1px solid var(--rule); margin: 7mm 0; }}

  /* ---------- Tableaux ---------- */
  table {{ width: 100%; border-collapse: collapse; margin: 3mm 0 5mm;
           font-size: 7.9pt; page-break-inside: avoid; }}
  th, td {{ border: 1px solid var(--rule); padding: 1.5mm 2mm;
            text-align: left; vertical-align: top; line-height: 1.38; }}
  th {{ background: var(--soft); font-weight: 700; font-size: 7.7pt; }}
  tbody tr:nth-child(even) {{ background: #fbfcfd; }}
  td p, th p {{ margin: 0; text-align: left; }}

  /* ---------- Code et schémas ---------- */
  pre {{ background: var(--soft); border: 1px solid var(--rule); border-left: 3px solid var(--accent);
         padding: 3mm 3.5mm; font-size: 6.9pt; line-height: 1.32; overflow: hidden;
         page-break-inside: avoid; white-space: pre; margin: 3mm 0 5mm; }}
  pre code {{ font-family: "DejaVu Sans Mono", "Liberation Mono", monospace; }}
  code {{ font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
          font-size: 8.4pt; background: var(--soft); padding: 0 .8mm;
          border-radius: 2px; word-break: break-word; }}

  /* ---------- Encadrés ---------- */
  blockquote {{ margin: 3mm 0 5mm; padding: 2.5mm 4mm; background: #fff8e8;
                border-left: 3px solid #d79a2b; page-break-inside: avoid; }}
  blockquote p {{ margin: 0 0 1.8mm; }}
  blockquote p:last-child {{ margin-bottom: 0; }}
  blockquote h3 {{ margin-top: 0; color: #8a5a00; }}

  li.src {{ margin-bottom: 1.8mm; }}
  li.src .src-url {{ display: block; font-family: "DejaVu Sans Mono", monospace;
                     font-size: 6.6pt; color: var(--muted); word-break: break-all;
                     line-height: 1.3; }}

  li, tr, h2, h3 {{ page-break-inside: avoid; }}
</style>
</head>
<body>

<div class="cover">
  <div class="cover-top">
    <div class="cover-kicker">PRI 2026 – 2027 · Projet 2</div>
    <div class="cover-project">Projet de Recherche et d'Innovation</div>
  </div>

  <div class="cover-mid">
    <h1>{title}</h1>
    <div class="cover-rule"></div>
    <h2>{subtitle}</h2>
  </div>

  <div class="cover-meta">
    <table>
      <tr><td>Encadrement</td><td><strong>Moïse DJOKO-KOUAM</strong></td></tr>
      <tr><td>Équipe projet</td><td class="todo">à compléter</td></tr>
      <tr><td>Version</td><td>1.0 — document de travail</td></tr>
      <tr><td>Date</td><td>{today}</td></tr>
      <tr><td>Mots clés</td><td>Intelligence artificielle · Perception · Fusion ·
          Suivi · Embarqué</td></tr>
    </table>
  </div>

  <div class="cover-foot">
    Livrables couverts : <strong>analyse des besoins et des contraintes</strong> ·
    <strong>état de l'art et comparaison des modèles</strong> ·
    <strong>choix argumenté du modèle</strong> (proposition, à confirmer par les mesures
    du protocole expérimental).
  </div>
</div>

<div class="toc">
  <h2>Sommaire</h2>
  <ul>
{toc}
  </ul>
</div>

{body}

</body>
</html>
"""


SYNTHESIS_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  :root {{ --ink:#16191d; --muted:#5b6470; --rule:#d7dce3; --accent:#1f4e79; --soft:#f4f6f9; }}
  * {{ box-sizing: border-box; }}
  html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{ font-family:"DejaVu Sans","Noto Sans","Liberation Sans",sans-serif;
          font-size:9.3pt; line-height:1.45; color:var(--ink); margin:0; }}

  .masthead {{ border-top:3px solid var(--accent); padding-top:4mm; margin-bottom:7mm; }}
  .kicker {{ font-size:7.8pt; letter-spacing:.15em; text-transform:uppercase;
             color:var(--accent); font-weight:700; }}
  .masthead h1 {{ font-size:17pt; line-height:1.22; margin:2.5mm 0 2mm; }}
  .masthead .meta {{ font-size:8pt; color:var(--muted); }}

  h2 {{ font-size:12pt; margin:7mm 0 2.5mm; padding-bottom:1.3mm;
        border-bottom:1px solid var(--rule); page-break-after:avoid; }}
  h3 {{ font-size:10pt; margin:5mm 0 1.8mm; color:var(--accent); page-break-after:avoid; }}
  p {{ margin:0 0 2.3mm; text-align:justify; }}
  ul, ol {{ margin:0 0 2.3mm; padding-left:5mm; }}
  li {{ margin-bottom:1mm; }}
  a {{ color:var(--accent); text-decoration:none; word-break:break-word; }}
  hr {{ border:0; border-top:1px solid var(--rule); margin:6mm 0; }}
  em {{ color:inherit; }}

  table {{ width:100%; border-collapse:collapse; margin:2.5mm 0 4mm;
           font-size:7.6pt; page-break-inside:avoid; }}
  th, td {{ border:1px solid var(--rule); padding:1.4mm 1.9mm;
            text-align:left; vertical-align:top; line-height:1.35; }}
  th {{ background:var(--soft); font-weight:700; font-size:7.4pt; }}
  tbody tr:nth-child(even) {{ background:#fbfcfd; }}
  td p {{ margin:0; text-align:left; }}

  pre {{ background:var(--soft); border:1px solid var(--rule); border-left:3px solid var(--accent);
         padding:2.8mm 3mm; font-size:6.7pt; line-height:1.3; white-space:pre;
         overflow:hidden; page-break-inside:avoid; margin:2.5mm 0 4mm; }}
  pre code, code {{ font-family:"DejaVu Sans Mono","Liberation Mono",monospace; }}
  code {{ font-size:8.1pt; background:var(--soft); padding:0 .7mm; border-radius:2px; }}

  blockquote {{ margin:2.5mm 0 4mm; padding:2.2mm 3.5mm; background:#fff8e8;
                border-left:3px solid #d79a2b; page-break-inside:avoid; }}
  blockquote p {{ margin:0 0 1.5mm; }}
  blockquote p:last-child {{ margin-bottom:0; }}
  blockquote h3 {{ margin-top:0; color:#8a5a00; font-size:10.5pt; }}

  li.src {{ margin-bottom:1.5mm; }}
  li.src .src-url {{ display:block; font-family:"DejaVu Sans Mono",monospace;
                     font-size:6.4pt; color:var(--muted); word-break:break-all; }}

  li, tr, h2, h3 {{ page-break-inside:avoid; }}
</style>
</head>
<body>
  <div class="masthead">
    <div class="kicker">PRI 2026 – 2027 · Projet 2 · Note de synthèse</div>
    <h1>{title}</h1>
    <div class="meta">{meta}</div>
  </div>
{body}
</body>
</html>
"""


async def render(html_path: Path, pdf_path: Path) -> None:
    from playwright.async_api import async_playwright

    footer = (
        '<div style="width:100%;font-size:7pt;color:#8a929c;padding:0 14mm;'
        'font-family:DejaVu Sans,sans-serif;display:flex;justify-content:space-between;">'
        "<span>PRI 2026-2027 · Projet 2 — IA embarquée pour la perception des VA</span>"
        '<span class="pageNumber"></span></div>'
    )
    async with async_playwright() as p:
        launch: dict = {"args": ["--no-sandbox", "--font-render-hinting=none"]}
        if CHROMIUM.exists():
            launch["executable_path"] = str(CHROMIUM)
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page()
        await page.goto(html_path.as_uri(), wait_until="networkidle")
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template='<div style="font-size:1pt"></div>',
            footer_template=footer,
            margin={"top": "16mm", "bottom": "17mm", "left": "16mm", "right": "16mm"},
        )
        await browser.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", choices=[*PROFILES, "tous"], default="tous")
    ap.add_argument("-o", "--output", help="chemin de sortie (un seul profil)")
    ap.add_argument("--date", default="Septembre 2026")
    args = ap.parse_args()

    wanted = list(PROFILES) if args.profile == "tous" else [args.profile]
    if args.output and len(wanted) > 1:
        ap.error("--output demande un profil unique (--profile rapport|synthese)")

    for profile in wanted:
        out = (ROOT / (args.output or PROFILES[profile])).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        page = build_html(args.date) if profile == "rapport" else build_synthesis_html(args.date)
        html_path = out.with_suffix(".html")
        html_path.write_text(page, encoding="utf-8")

        asyncio.run(render(html_path, out))
        html_path.unlink()
        print(f"{profile:9s} -> {out.name}  ({out.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    main()
