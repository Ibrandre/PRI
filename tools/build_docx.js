#!/usr/bin/env node
/**
 * Génère une version Word (.docx) modifiable d'un document Markdown de docs/.
 *
 * Les titres utilisent les styles Word natifs (Titre 1, Titre 2) : le volet de
 * navigation et la table des matières automatique de Word fonctionnent.
 *
 * Usage :
 *   (cd tools && npm install)          # une seule fois
 *   node tools/build_docx.js [docs/03-synthese.md] [build/PRI_IA_Perception_Synthese.docx]
 */

const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, ExternalHyperlink, Footer, HeadingLevel,
  LevelFormat, Packer, PageNumber, Paragraph, ShadingType, Tab, Table, TableCell,
  TableRow, TabStopType, TextRun, WidthType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const INPUT = path.resolve(ROOT, process.argv[2] || "docs/03-synthese.md");
const OUTPUT = path.resolve(ROOT, process.argv[3] || "build/PRI_IA_Perception_Synthese.docx");

const TITLE = "IA embarquée pour la perception des véhicules autonomes en logistique hospitalière";
const KICKER = "PRI 2026 – 2027 · Projet 2 · Note de synthèse";
const FOOTER = "PRI 2026-2027 · Projet 2 — IA embarquée pour la perception des VA";

const C = {
  ink: "16191D", muted: "5B6470", rule: "D7DCE3", accent: "1F4E79",
  soft: "F4F6F9", noteBg: "FFF8E8", noteBar: "D79A2B", noteInk: "8A5A00",
};
const FONT = "Calibri";
const MONO = "Courier New";
const BODY = 21;                 // demi-points : 10,5 pt
const PAGE_W = 11906, MARGIN = 1134;
const CONTENT_W = PAGE_W - 2 * MARGIN;   // 9638 DXA

// ---------------------------------------------------------------- inline

const ESC = "\u0000";
const PATTERNS = [
  { kind: "link", re: /\[([^\]]+)\]\(([^)\s]+)\)/ },
  { kind: "bold", re: /\*\*(.+?)\*\*/ },
  { kind: "code", re: /`([^`]+)`/ },
  { kind: "italic", re: /(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])/ },
];

/** Découpe une ligne Markdown en segments {text, bold, italics, code, link}. */
function parseInline(text, style = {}) {
  const out = [];
  let rest = text;
  while (rest.length) {
    let best = null;
    for (const p of PATTERNS) {
      const m = p.re.exec(rest);
      if (m && (best === null || m.index < best.m.index)) best = { p, m };
    }
    if (!best) { out.push({ text: rest, ...style }); break; }
    const { p, m } = best;
    if (m.index > 0) out.push({ text: rest.slice(0, m.index), ...style });
    if (p.kind === "link") out.push(...parseInline(m[1], { ...style, link: m[2] }));
    else if (p.kind === "bold") out.push(...parseInline(m[1], { ...style, bold: true }));
    else if (p.kind === "italic") out.push(...parseInline(m[1], { ...style, italics: true }));
    else out.push({ text: m[1], ...style, code: true });
    rest = rest.slice(m.index + m[0].length);
  }
  return out;
}

function runs(text, base = {}) {
  const clean = text.replace(/\\\*/g, ESC).replace(/<\/?small>/g, "");
  const children = [];
  for (const seg of parseInline(clean)) {
    const t = seg.text.replace(new RegExp(ESC, "g"), "*");
    const run = new TextRun({
      text: t,
      bold: seg.bold || base.bold,
      italics: seg.italics || base.italics,
      font: seg.code ? MONO : base.font || FONT,
      size: base.size || BODY,
      color: seg.link ? C.accent : base.color || C.ink,
      underline: seg.link ? {} : undefined,
    });
    children.push(seg.link ? new ExternalHyperlink({ link: seg.link, children: [run] }) : run);
  }
  return children;
}

// ---------------------------------------------------------------- blocs

let numberingInstance = 0;
const spacers = new Set();

/** Paragraphe vide d'espacement entre deux blocs (retiré s'il termine le document). */
function spacer(after) {
  const p = new Paragraph({ spacing: { after } });
  spacers.add(p);
  return p;
}

function para(text, opts = {}) {
  return new Paragraph({
    children: runs(text, opts.run || {}),
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: opts.after ?? 120, line: 276 },
    ...opts.extra,
  });
}

function heading(text, level) {
  return new Paragraph({
    heading: level === 2 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    children: runs(text, { bold: true, color: level === 2 ? C.ink : C.accent, size: level === 2 ? 26 : 22 }),
    keepNext: true,
  });
}

function rule() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.rule, space: 1 } },
    spacing: { before: 120, after: 240 },
  });
}

function listItem(text, ordered) {
  return new Paragraph({
    children: runs(text),
    numbering: ordered
      ? { reference: "numbers", level: 0, instance: numberingInstance }
      : { reference: "bullets", level: 0 },
    spacing: { after: 60, line: 264 },
  });
}

function note(lines) {
  // Encadré : bande colorée à gauche, fond clair.
  const border = { left: { style: BorderStyle.SINGLE, size: 18, color: C.noteBar, space: 8 } };
  const shading = { type: ShadingType.CLEAR, color: "auto", fill: C.noteBg };
  return lines.filter((l) => l.trim()).map((l) => {
    const h = /^#{2,3}\s+(.*)$/.exec(l);
    return new Paragraph({
      children: runs(h ? h[1] : l, h ? { bold: true, size: 24, color: C.noteInk } : {}),
      border, shading, indent: { left: 170 },
      spacing: { after: 60, line: 276 },
    });
  });
}

function codeBlock(lines) {
  const border = { left: { style: BorderStyle.SINGLE, size: 18, color: C.accent, space: 8 } };
  const shading = { type: ShadingType.CLEAR, color: "auto", fill: C.soft };
  return lines.map((l) => new Paragraph({
    children: [new TextRun({ text: l.length ? l : " ", font: MONO, size: 15, color: C.ink })],
    border, shading, indent: { left: 170 }, spacing: { after: 0, line: 240 }, keepLines: true, keepNext: true,
  }));
}

function table(rows) {
  const cells = rows.map((r) => r.replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));
  const header = cells[0];
  const body = cells.slice(2);                       // ligne 1 = séparateur ---
  const n = header.length;

  // Largeurs : chaque colonne reçoit au moins la place de son mot le plus long
  // (pas de mot coupé en plein milieu), puis le reste est réparti selon la
  // longueur du contenu.
  const plain = (t) => t.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/[*`\\]|<\/?small>/g, "");
  const CH = 100, PAD = 240;                                  // DXA par caractère, marges de cellule
  const sum = (a) => a.reduce((x, y) => x + y, 0);
  const texts = header.map((_, j) => [header, ...body].map((r) => plain(r[j] || "")));
  const minW = texts.map((ts) => Math.max(...ts.flatMap((t) => t.split(/\s+/)).map((w) => w.length)) * CH + PAD);
  const wantW = texts.map((ts, j) => Math.max(minW[j], Math.min(45, Math.max(...ts.map((t) => t.length))) * CH + PAD));
  let widths;
  if (sum(minW) >= CONTENT_W) {
    widths = minW.map((w) => Math.floor((w * CONTENT_W) / sum(minW)));
  } else {
    const extra = CONTENT_W - sum(minW);
    const gaps = wantW.map((w, j) => w - minW[j]);
    widths = minW.map((w, j) => w + Math.floor(sum(gaps) ? (extra * gaps[j]) / sum(gaps) : extra / n));
  }
  widths[n - 1] += CONTENT_W - sum(widths);

  const border = { style: BorderStyle.SINGLE, size: 4, color: C.rule };
  const borders = { top: border, bottom: border, left: border, right: border };
  const mkRow = (r, isHeader) => new TableRow({
    tableHeader: isHeader,
    cantSplit: true,
    children: r.map((txt, j) => new TableCell({
      width: { size: widths[j], type: WidthType.DXA },
      borders,
      shading: isHeader ? { type: ShadingType.CLEAR, color: "auto", fill: C.soft } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({
        children: runs(txt, { size: 17, bold: isHeader }),
        spacing: { after: 0, line: 252 },
      })],
    })),
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [mkRow(header, true), ...body.map((r) => mkRow(r, false))],
  });
}

// ---------------------------------------------------------------- document

function parse(md) {
  const lines = md.split("\n");
  const out = [];
  let i = 0;

  // En-tête : titre H1 et lignes en italique qui le suivent.
  const meta = [];
  while (i < lines.length && !lines[i].startsWith("# ")) i++;
  i++;
  while (i < lines.length && (!lines[i].trim() || /^\*[^*].*\*$/.test(lines[i]))) {
    if (lines[i].trim()) meta.push(lines[i].replace(/^\*|\*$/g, ""));
    i++;
  }
  out.push(new Paragraph({
    border: { top: { style: BorderStyle.SINGLE, size: 18, color: C.accent, space: 8 } },
    children: [new TextRun({ text: KICKER.toUpperCase(), bold: true, size: 16, color: C.accent, font: FONT, characterSpacing: 30 })],
    spacing: { after: 80 },
  }));
  out.push(new Paragraph({
    heading: HeadingLevel.TITLE,
    children: [new TextRun({ text: TITLE, bold: true, size: 34, color: C.ink, font: FONT })],
    spacing: { after: 100 },
  }));
  meta.forEach((m) => out.push(para(m, { run: { size: 17, color: C.muted }, after: 20, align: AlignmentType.LEFT })));
  out.push(new Paragraph({ spacing: { after: 200 } }));

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) { i++; continue; }
    if (/^---\s*$/.test(line)) { out.push(rule()); i++; continue; }

    let m;
    if ((m = /^(#{2,3})\s+(.*)$/.exec(line))) { out.push(heading(m[2], m[1].length)); i++; continue; }

    if (line.startsWith("```")) {
      const block = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) block.push(lines[i++]);
      i++;
      out.push(...codeBlock(block));
      out.push(spacer(120));
      continue;
    }

    if (line.startsWith("|")) {
      const block = [];
      while (i < lines.length && lines[i].startsWith("|")) block.push(lines[i++]);
      out.push(table(block));
      out.push(spacer(120));
      continue;
    }

    if (line.startsWith(">")) {
      const block = [];
      while (i < lines.length && lines[i].startsWith(">")) block.push(lines[i++].replace(/^>\s?/, ""));
      // Regroupe les lignes d'un même paragraphe de citation.
      const paras = [];
      let cur = [];
      for (const b of block) {
        if (!b.trim()) { if (cur.length) paras.push(cur.join(" ")); cur = []; }
        else if (/^#{2,3}\s/.test(b)) { if (cur.length) paras.push(cur.join(" ")); paras.push(b); cur = []; }
        else cur.push(b.trim());
      }
      if (cur.length) paras.push(cur.join(" "));
      out.push(...note(paras));
      out.push(spacer(120));
      continue;
    }

    const bullet = /^- (.*)$/.exec(line);
    const ordered = /^\d+\.\s+(.*)$/.exec(line);
    if (bullet || ordered) {
      if (ordered) numberingInstance++;
      const isOrdered = !!ordered;
      while (i < lines.length) {
        const b = /^- (.*)$/.exec(lines[i]);
        const o = /^\d+\.\s+(.*)$/.exec(lines[i]);
        const item = isOrdered ? o : b;
        if (!item) break;
        let text = item[1];
        i++;
        while (i < lines.length && /^\s{2,}\S/.test(lines[i])) text += " " + lines[i++].trim();
        out.push(listItem(text, isOrdered));
      }
      out.push(spacer(60));
      continue;
    }

    // Paragraphe : lignes consécutives non vides.
    const block = [];
    while (i < lines.length && lines[i].trim() && !/^(#{2,3}\s|\||>|```|- |\d+\.\s|---\s*$)/.test(lines[i])) {
      block.push(lines[i++].trim());
    }
    const text = block.join(" ");
    if (text.startsWith("<small>")) {
      out.push(para(text, { run: { size: 16, italics: true, color: C.muted } }));
    } else {
      out.push(para(text));
    }
  }
  while (out.length && spacers.has(out[out.length - 1])) out.pop();
  return out;
}

const doc = new Document({
  creator: "PRI 2026-2027 — Projet 2",
  title: TITLE,
  styles: {
    default: { document: { run: { font: FONT, size: BODY, color: C.ink } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true, color: C.ink },
        paragraph: { spacing: { before: 320, after: 120 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.rule, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 22, bold: true, color: C.accent },
        paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 1 } },
      { id: "PiedDePage", name: "Pied de page PRI", basedOn: "Normal",
        run: { font: FONT, size: 14, color: "8A929C" }, paragraph: { spacing: { after: 0 } } },
      { id: "Title", name: "Title", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 34, bold: true, color: C.ink },
        paragraph: { spacing: { after: 100 } } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 360, hanging: 240 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 360, hanging: 300 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: PAGE_W, height: 16838 },
              margin: { top: 1020, bottom: 1080, left: MARGIN, right: MARGIN, footer: 500 } },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          style: "PiedDePage",
          tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
          children: [
            new TextRun({ text: FOOTER }),
            new TextRun({ children: [new Tab(), PageNumber.CURRENT] }),
          ],
        })],
      }),
    },
    children: parse(fs.readFileSync(INPUT, "utf8")),
  }],
});

fs.mkdirSync(path.dirname(OUTPUT), { recursive: true });
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUTPUT, buf);
  console.log(`Word : ${OUTPUT}  (${Math.round(buf.length / 1024)} Ko)`);
});
