// mkmanual.js -- VM/370plus Installation, Operation and User's Guide (Word)
// node mkmanual.js out.docx
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageBreak,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, LevelFormat,
  TableOfContents, Header, Footer, PageNumber, TabStopType, TabStopPosition,
} = require('docx');

const BODY = 'Times New Roman', HEAD = 'Arial', MONO = 'Courier New';
const W = 9638; // A4 text width in DXA with 2 cm margins (11906 - 2*1134)

// ---------- inline markup: `code`, **bold**, *italic* ----------
function runs(text, base = {}) {
  const out = [];
  const re = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: BODY, ...base }));
    const t = m[0];
    if (t.startsWith('`')) out.push(new TextRun({ text: t.slice(1, -1), font: MONO, size: 19, ...base }));
    else if (t.startsWith('**')) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: BODY, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: BODY, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: BODY, ...base }));
  return out;
}

const C = [];             // document body
const HEADS = [];         // [level, text] for the contents
let chapNo = 0, figNo = 0, appendix = false, appLetter = 64;
const P = (t, o = {}) => C.push(new Paragraph({ children: runs(t), spacing: { after: 120 }, ...o }));
const H1 = (t) => {
  let label;
  if (appendix) { appLetter++; label = `Appendix ${String.fromCharCode(appLetter)}. ${t}`; }
  else { chapNo++; label = `Chapter ${chapNo}. ${t}`; }
  HEADS.push([1, label]);
  C.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun(label)] }));
};
const H1plain = (t) => HEADS.push([1, t]) && C.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun(t)] }));
const H2 = (t) => HEADS.push([2, t]) && C.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] }));
const H3 = (t) => C.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] }));
const B = (items, ref = 'bullets') => items.forEach(t => C.push(new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 60 } })));
let numList = 0;
const N = (items, cont) => { if (!cont) numList++; items.forEach(t => C.push(new Paragraph({ numbering: { reference: 'steps', level: 0, instance: numList }, children: runs(t), spacing: { after: 60 } }))); };
const NOTE = (t) => C.push(new Paragraph({
  children: [new TextRun({ text: 'Note: ', bold: true, font: BODY }), ...runs(t)],
  indent: { left: 567 }, spacing: { before: 60, after: 120 },
}));
const ATTN = (t) => C.push(new Paragraph({
  children: [new TextRun({ text: 'Attention: ', bold: true, font: BODY }), ...runs(t)],
  indent: { left: 567 }, spacing: { before: 60, after: 120 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: '000000', space: 6 } },
}));
// a "screen" in the IBM manner: monospaced, framed, light shading
function SCREEN(lines, caption) {
  const paras = lines.map(l => new Paragraph({
    children: [new TextRun({ text: l === '' ? ' ' : l, font: MONO, size: 17 })],
    spacing: { after: 0, line: 228 },
  }));
  C.push(new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [W],
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      width: { size: W, type: WidthType.DXA },
      shading: { fill: 'F2F2F2', type: ShadingType.CLEAR, color: 'auto' },
      margins: { top: 100, bottom: 100, left: 140, right: 140 },
      children: paras,
    })] })],
  }));
  if (caption) { figNo++; C.push(new Paragraph({ children: [new TextRun({ text: `Figure ${figNo}. `, bold: true, font: HEAD, size: 18 }), new TextRun({ text: caption, font: HEAD, size: 18 })], spacing: { before: 80, after: 200 } })); }
  else C.push(new Paragraph({ children: [], spacing: { after: 120 } }));
}
// a table with a header row; widths in DXA summing to W
function TABLE(head, rows, widths, caption) {
  const border = { style: BorderStyle.SINGLE, size: 4, color: '808080' };
  const mk = (r, hdr) => new TableRow({ tableHeader: hdr, cantSplit: true, children: r.map((t, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: hdr ? { fill: 'D9D9D9', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: hdr ? [new TextRun({ text: t, bold: true, font: HEAD, size: 18 })] : runs(t, { size: 19 }) })],
  })) });
  C.push(new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    borders: { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border },
    rows: [mk(head, true), ...rows.map(r => mk(r, false))],
  }));
  if (caption) { figNo++; C.push(new Paragraph({ children: [new TextRun({ text: `Figure ${figNo}. `, bold: true, font: HEAD, size: 18 }), new TextRun({ text: caption, font: HEAD, size: 18 })], spacing: { before: 80, after: 200 } })); }
  else C.push(new Paragraph({ children: [], spacing: { after: 120 } }));
}

module.exports = { P, H1, H1plain, H2, H3, B, N, NOTE, ATTN, SCREEN, TABLE, C, setAppendix: () => { appendix = true; } };

// ---------- the content ----------
require('./content.js')(module.exports);

fs.writeFileSync(__dirname + '/headings.json', JSON.stringify(HEADS));

// ---------- title page and front matter ----------
const title = [
  new Paragraph({ children: [], spacing: { before: 1800 } }),
  new Paragraph({ children: [new TextRun({ text: 'VM/370plus', font: HEAD, bold: true, size: 72 })] }),
  new Paragraph({ children: [new TextRun({ text: 'Virtual Machine Facility/370, ESA/390 Edition', font: HEAD, size: 30 })], spacing: { after: 600 } }),
  new Paragraph({ children: [new TextRun({ text: 'Introduction, Installation', font: HEAD, bold: true, size: 40 })] }),
  new Paragraph({ children: [new TextRun({ text: 'and User’s Guide', font: HEAD, bold: true, size: 40 })], spacing: { after: 400 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 24, color: '000000', space: 8 } } }),
  new Paragraph({ children: [new TextRun({ text: 'Release 1  •  Kit Build 5, updated 10 October 2026', font: HEAD, size: 24 })], spacing: { after: 120 } }),
  new Paragraph({ children: [new TextRun({ text: 'based on VM/370 Community Edition V1 R1.2', font: HEAD, size: 22 })], spacing: { after: 2400 } }),
  new Paragraph({ children: [new TextRun({ text: 'Publication VMP-0001-0', font: HEAD, size: 22 })] }),
  new Paragraph({ children: [new TextRun({ text: 'File No. S370-34', font: HEAD, size: 22 })] }),
  new Paragraph({ children: [new PageBreak()] }),
];
const edition = [
  new Paragraph({ children: [new TextRun({ text: 'First Edition, revised (October 2026)', font: HEAD, bold: true, size: 24 })], spacing: { after: 200 } }),
  ...['This edition applies to VM/370plus Release 1 (kit build 5, 9 October 2026), an ESA/390 conversion of the VM/370 Community Edition V1 R1.2, and to all subsequent builds until otherwise indicated in new editions.',
     'VM/370plus is a hobbyist project. It is not a product of, and this manual is not a publication of, International Business Machines Corporation. IBM, System/370, ESA/390, z/Architecture and VM/370 are names of IBM products and architectures, used here only to identify the systems this software runs on and descends from.',
     'VM/370 itself is in the public domain. The VM/370 Community Edition is maintained by its community. Hercules is an open-source emulator. Linux and Debian are trademarks of their respective owners. cREXX is an open-source REXX implementation.',
     'The project repository holds the update decks, the build tools, the issue register and the test runs from which every statement in this manual can be checked. Comments on this publication may be addressed to the project.'].map(t => new Paragraph({ children: runs(t), spacing: { after: 160 } })),
  new Paragraph({ children: [new PageBreak()] }),
];
// static contents from a first pass (TOCJSON: [[level, text, page], ...])
const tocItems = process.env.TOCJSON ? JSON.parse(fs.readFileSync(process.env.TOCJSON)) : [];
const toc = [
  new Paragraph({ children: [new TextRun({ text: 'Contents', font: HEAD, bold: true, size: 32 })], spacing: { after: 240 } }),
  ...tocItems.map(([lvl, text, page]) => new Paragraph({
    tabStops: [{ type: TabStopType.RIGHT, position: W, leader: 'dot' }],
    indent: { left: lvl === 1 ? 0 : 400 },
    spacing: { before: lvl === 1 ? 160 : 20, after: 20 },
    children: [new TextRun({ text, font: lvl === 1 ? HEAD : BODY, bold: lvl === 1, size: lvl === 1 ? 21 : 20 }),
               new TextRun({ text: '\t' + page, font: lvl === 1 ? HEAD : BODY, bold: lvl === 1, size: lvl === 1 ? 21 : 20 })] })),
];

const doc = new Document({
  creator: 'VM/370plus project', title: 'VM/370plus Introduction, Installation and User’s Guide',
  styles: {
    default: { document: { run: { font: BODY, size: 21 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, font: HEAD }, paragraph: { spacing: { before: 0, after: 360 }, outlineLevel: 0,
        border: { bottom: { style: BorderStyle.SINGLE, size: 18, color: '000000', space: 6 } } } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: HEAD }, paragraph: { spacing: { before: 320, after: 140 }, outlineLevel: 1, keepNext: true } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 22, bold: true, font: HEAD }, paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [
    { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 567, hanging: 283 } } } }] },
    { reference: 'steps', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 567, hanging: 397 } } } }] },
  ] },
  sections: [
    { properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
      children: [...title, ...edition, ...toc] },
    { properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1134, left: 1134, right: 1134 }, pageNumbers: { start: 1 } } },
      headers: { default: new Header({ children: [new Paragraph({ children: [new TextRun({ text: 'VM/370plus Introduction, Installation and User’s Guide', font: HEAD, size: 16 })],
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '000000', space: 4 } } })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        children: [new TextRun({ text: 'VMP-0001-0', font: HEAD, size: 16 }), new TextRun({ children: ['\t', PageNumber.CURRENT], font: HEAD, size: 18 })] })] }) },
      children: C },
  ],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2] || 'VM370PLUS-Guide.docx', b); console.log('written'); });
