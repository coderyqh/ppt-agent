const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const [inputPath, outputPath] = process.argv.slice(2);

if (!inputPath || !outputPath) {
  console.error("Usage: node scripts/render_deck.cjs <deck.json> <output.pptx>");
  process.exit(2);
}

const deck = JSON.parse(fs.readFileSync(inputPath, "utf8"));
const pptx = new pptxgen();
pptx.defineLayout({ name: "LAYOUT_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "LAYOUT_WIDE";
pptx.author = "PPT Agent";
pptx.subject = deck.audience || "";
pptx.title = deck.title || "Presentation";
pptx.company = "PPT Agent";
pptx.lang = "zh-CN";

const theme = normalizeTheme(deck.theme || {});
pptx.theme = {
  headFontFace: theme.headerFont,
  bodyFontFace: theme.bodyFont,
  lang: "zh-CN",
};

const slides = Array.isArray(deck.slides) ? deck.slides : [];
slides.forEach((model, idx) => {
  const slide = pptx.addSlide();
  paintBackground(slide, theme, idx);

  if (model.layout === "title") {
    renderCover(slide, model, deck, theme);
  } else if (model.layout === "diagram") {
    renderFlow(slide, model, theme, idx);
  } else if (model.kind === "closing") {
    renderClosing(slide, model, theme, idx);
  } else {
    renderEditorial(slide, model, theme, idx);
  }

  addFooter(slide, model.index || idx + 1, slides.length, theme);
  if (model.speaker_notes && typeof slide.addNotes === "function") {
    slide.addNotes(model.speaker_notes);
  }
});

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
pptx.writeFile({ fileName: outputPath });

function normalizeTheme(raw) {
  return {
    style: raw.deerStyle || "dark-premium",
    primary: cleanHex(raw.primary, "0A0A0A"),
    secondary: cleanHex(raw.secondary, "1D1D1F"),
    accent: cleanHex(raw.accent, "00D4FF"),
    bg: cleanHex(raw.background, "0A0A0A"),
    surface: cleanHex(raw.surface, "141414"),
    text: cleanHex(raw.text, "FFFFFF"),
    muted: cleanHex(raw.muted, "A1A1AA"),
    headerFont: raw.headerFont || "Arial Black",
    bodyFont: raw.bodyFont || "Arial",
  };
}

function cleanHex(value, fallback) {
  if (typeof value !== "string") return fallback;
  const cleaned = value.replace(/^#/, "").trim();
  return /^[0-9a-fA-F]{6}$/.test(cleaned) ? cleaned.toUpperCase() : fallback;
}

function paintBackground(slide, theme, idx) {
  slide.background = { color: theme.bg };

  if (theme.style === "minimal-swiss" || theme.style === "editorial" || theme.style === "3d-isometric") {
    slide.addShape(pptx.ShapeType.rect, {
      x: 0,
      y: 0,
      w: 13.333,
      h: 7.5,
      fill: { color: theme.bg },
      line: { color: theme.bg },
    });
    slide.addShape(pptx.ShapeType.rect, {
      x: 0.65,
      y: 0.52,
      w: 0.12,
      h: 0.58,
      fill: { color: theme.accent },
      line: { color: theme.accent },
    });
    return;
  }

  const glowA = theme.style === "glassmorphism" ? "667EEA" : theme.accent;
  const glowB = theme.style === "gradient-modern" ? "EC4899" : theme.secondary;
  const offset = (idx % 3) * 0.55;

  slide.addShape(pptx.ShapeType.ellipse, {
    x: 7.9 - offset,
    y: -1.0,
    w: 5.3,
    h: 5.3,
    fill: { color: glowA, transparency: 58 },
    line: { color: glowA, transparency: 100 },
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: -1.2 + offset,
    y: 3.9,
    w: 4.8,
    h: 4.8,
    fill: { color: glowB, transparency: 68 },
    line: { color: glowB, transparency: 100 },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 7.5,
    fill: { color: theme.bg, transparency: theme.style === "glassmorphism" ? 18 : 8 },
    line: { color: theme.bg, transparency: 100 },
  });
}

function renderCover(slide, model, deck, theme) {
  addKicker(slide, "PRESENTATION", 0.82, 0.72, theme);

  slide.addText(model.title || deck.title || "Presentation", {
    x: 0.82,
    y: 1.45,
    w: 8.9,
    h: 1.8,
    margin: 0,
    fit: "shrink",
    fontFace: theme.headerFont,
    fontSize: theme.style === "minimal-swiss" ? 42 : 48,
    bold: true,
    color: theme.text,
    breakLine: false,
  });

  slide.addText((model.bullets || []).slice(0, 2).join(" / ") || deck.audience || "", {
    x: 0.86,
    y: 3.55,
    w: 6.9,
    h: 0.45,
    margin: 0,
    fit: "shrink",
    fontFace: theme.bodyFont,
    fontSize: 18,
    color: theme.muted,
  });

  addHeroObject(slide, theme, 8.65, 1.25);

  slide.addShape(pptx.ShapeType.rect, {
    x: 0.86,
    y: 5.78,
    w: 3.0,
    h: 0.5,
    fill: { color: theme.accent },
    line: { color: theme.accent },
  });
  slide.addText(`${deck.audience || ""} | ${deck.style || "deck"}`, {
    x: 1.05,
    y: 5.93,
    w: 2.62,
    h: 0.14,
    margin: 0,
    fit: "shrink",
    fontFace: theme.bodyFont,
    fontSize: 10,
    bold: true,
    color: isLight(theme.accent) ? "111111" : "FFFFFF",
    align: "center",
  });
}

function renderEditorial(slide, model, theme, idx) {
  addKicker(slide, (model.kind || "INSIGHT").toUpperCase(), 0.82, 0.62, theme);
  addClaim(slide, model.title || "", 0.82, 1.04, 7.3, theme);

  const bullets = (model.bullets || []).slice(0, 4);
  const lead = bullets[0] || model.intent || "";

  slide.addText(lead, {
    x: 0.88,
    y: 2.45,
    w: 5.1,
    h: 0.95,
    margin: 0,
    fit: "shrink",
    fontFace: theme.bodyFont,
    fontSize: 20,
    bold: true,
    color: theme.text,
    breakLine: false,
  });

  bullets.slice(1).forEach((bullet, i) => {
    const y = 3.72 + i * 0.6;
    slide.addShape(pptx.ShapeType.rect, {
      x: 0.9,
      y: y + 0.06,
      w: 0.18,
      h: 0.18,
      fill: { color: theme.accent },
      line: { color: theme.accent },
    });
    slide.addText(bullet, {
      x: 1.22,
      y,
      w: 5.8,
      h: 0.36,
      margin: 0,
      fit: "shrink",
      fontFace: theme.bodyFont,
      fontSize: 14,
      color: theme.muted,
    });
  });

  if (idx % 2 === 0) {
    addMetricStack(slide, bullets, theme);
  } else {
    addProofPanel(slide, model, theme);
  }
}

function renderFlow(slide, model, theme) {
  addKicker(slide, "SYSTEM MAP", 0.82, 0.62, theme);
  addClaim(slide, model.title || "", 0.82, 1.04, 9.0, theme);

  const items = (model.bullets || []).slice(0, 5);
  const startX = 0.88;
  const w = items.length >= 5 ? 2.1 : 2.45;

  items.forEach((item, i) => {
    const x = startX + i * (w + 0.24);
    const y = 3.0 + (i % 2) * 0.38;
    addGlassPanel(slide, x, y, w, 1.35, theme, i === 0 ? 7 : 14);
    slide.addText(String(i + 1).padStart(2, "0"), {
      x: x + 0.18,
      y: y + 0.18,
      w: 0.48,
      h: 0.2,
      margin: 0,
      fontFace: theme.bodyFont,
      fontSize: 10,
      bold: true,
      color: theme.accent,
    });
    slide.addText(item, {
      x: x + 0.18,
      y: y + 0.55,
      w: w - 0.36,
      h: 0.5,
      margin: 0,
      fit: "shrink",
      fontFace: theme.bodyFont,
      fontSize: 14,
      bold: true,
      color: theme.text,
      align: "center",
    });
    if (i < items.length - 1) {
      slide.addShape(pptx.ShapeType.rightArrow, {
        x: x + w + 0.03,
        y: y + 0.54,
        w: 0.18,
        h: 0.26,
        fill: { color: theme.accent, transparency: 8 },
        line: { color: theme.accent, transparency: 100 },
      });
    }
  });

  slide.addText(model.intent || "", {
    x: 0.9,
    y: 5.82,
    w: 9.2,
    h: 0.36,
    margin: 0,
    fit: "shrink",
    fontFace: theme.bodyFont,
    fontSize: 13,
    color: theme.muted,
  });
}

function renderClosing(slide, model, theme) {
  addKicker(slide, "NEXT MOVE", 0.82, 0.72, theme);
  addClaim(slide, model.title || "", 0.82, 1.35, 8.8, theme, 42);

  const bullets = (model.bullets || []).slice(0, 3);
  bullets.forEach((bullet, i) => {
    addGlassPanel(slide, 0.92 + i * 3.85, 4.42, 3.25, 1.0, theme, 12);
    slide.addText(bullet, {
      x: 1.17 + i * 3.85,
      y: 4.75,
      w: 2.75,
      h: 0.28,
      margin: 0,
      fit: "shrink",
      fontFace: theme.bodyFont,
      fontSize: 14,
      bold: true,
      color: theme.text,
      align: "center",
    });
  });
  addHeroObject(slide, theme, 9.15, 1.1);
}

function addKicker(slide, text, x, y, theme) {
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y: y + 0.07,
    w: 0.34,
    h: 0.12,
    fill: { color: theme.accent },
    line: { color: theme.accent },
  });
  slide.addText(text, {
    x: x + 0.48,
    y,
    w: 2.5,
    h: 0.25,
    margin: 0,
    fontFace: theme.bodyFont,
    fontSize: 9,
    bold: true,
    charSpacing: 1.4,
    color: theme.accent,
  });
}

function addClaim(slide, text, x, y, w, theme, size = 30) {
  slide.addText(text, {
    x,
    y,
    w,
    h: 0.95,
    margin: 0,
    fit: "shrink",
    fontFace: theme.headerFont,
    fontSize: size,
    bold: true,
    color: theme.text,
    breakLine: false,
  });
}

function addGlassPanel(slide, x, y, w, h, theme, transparency = 10) {
  const fill = theme.style === "minimal-swiss" || theme.style === "editorial" ? theme.surface : "FFFFFF";
  const textLine = theme.style === "minimal-swiss" || theme.style === "editorial" ? "D4D4D4" : "FFFFFF";
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: fill, transparency },
    line: { color: textLine, transparency: theme.style === "minimal-swiss" ? 65 : 78, width: 1 },
    shadow: shadow(theme.style === "minimal-swiss" ? 0.02 : 0.16),
  });
}

function addMetricStack(slide, bullets, theme) {
  const values = ["10x", "3", "90d"];
  const labels = ["speed", "moves", "window"];
  [0, 1, 2].forEach((i) => {
    addGlassPanel(slide, 8.25, 1.65 + i * 1.45, 3.55, 1.02, theme, 14);
    slide.addText(values[i], {
      x: 8.55,
      y: 1.86 + i * 1.45,
      w: 1.15,
      h: 0.35,
      margin: 0,
      fontFace: theme.headerFont,
      fontSize: 24,
      bold: true,
      color: theme.accent,
    });
    slide.addText(bullets[i] || labels[i], {
      x: 9.78,
      y: 1.88 + i * 1.45,
      w: 1.7,
      h: 0.32,
      margin: 0,
      fit: "shrink",
      fontFace: theme.bodyFont,
      fontSize: 12,
      color: theme.muted,
    });
  });
}

function addProofPanel(slide, model, theme) {
  addGlassPanel(slide, 8.15, 1.65, 3.75, 4.25, theme, 12);
  slide.addText("PROOF OBJECT", {
    x: 8.48,
    y: 1.95,
    w: 2.4,
    h: 0.22,
    margin: 0,
    fontFace: theme.bodyFont,
    fontSize: 9,
    bold: true,
    charSpacing: 1.2,
    color: theme.accent,
  });
  slide.addText(model.visual || "One clear visual proof object", {
    x: 8.48,
    y: 2.42,
    w: 2.95,
    h: 0.92,
    margin: 0,
    fit: "shrink",
    fontFace: theme.bodyFont,
    fontSize: 14,
    bold: true,
    color: theme.text,
  });

  [0, 1, 2].forEach((i) => {
    const barW = 0.9 + i * 0.55;
    slide.addShape(pptx.ShapeType.rect, {
      x: 8.55,
      y: 4.55 - i * 0.42,
      w: barW,
      h: 0.22,
      fill: { color: i === 2 ? theme.accent : theme.muted, transparency: i === 2 ? 0 : 40 },
      line: { color: i === 2 ? theme.accent : theme.muted, transparency: 100 },
    });
  });
}

function addHeroObject(slide, theme, x, y) {
  slide.addShape(pptx.ShapeType.ellipse, {
    x,
    y,
    w: 2.5,
    h: 2.5,
    fill: { color: theme.accent, transparency: 18 },
    line: { color: theme.accent, transparency: 100 },
    shadow: shadow(0.24),
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: x + 0.58,
    y: y + 0.48,
    w: 1.45,
    h: 1.45,
    fill: { color: theme.secondary, transparency: 22 },
    line: { color: "FFFFFF", transparency: 82 },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: x - 0.38,
    y: y + 2.75,
    w: 3.3,
    h: 0.16,
    fill: { color: theme.accent, transparency: 55 },
    line: { color: theme.accent, transparency: 100 },
  });
}

function addFooter(slide, index, total, theme) {
  slide.addText(`${String(index).padStart(2, "0")} / ${String(total).padStart(2, "0")}`, {
    x: 11.0,
    y: 7.03,
    w: 1.45,
    h: 0.18,
    margin: 0,
    align: "right",
    fontFace: theme.bodyFont,
    fontSize: 9,
    color: theme.muted,
  });
}

function shadow(opacity) {
  return { type: "outer", color: "000000", blur: 7, offset: 1.2, angle: 45, opacity };
}

function isLight(hex) {
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 170;
}
