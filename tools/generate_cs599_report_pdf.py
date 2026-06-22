from __future__ import annotations

import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "CS599_大作业报告.md"
OUTPUT = ROOT / "docs" / "CS599_大作业报告.pdf"
SIMSUN = Path(r"C:\Windows\Fonts\simsun.ttc")
SIMHEI = Path(r"C:\Windows\Fonts\simhei.ttf")


class ReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
        self.addPageTemplates([PageTemplate(id="content", frames=[frame], onPage=self._draw_page)])

    def afterFlowable(self, flowable):
        title = getattr(flowable, "_bookmark_title", None)
        level = getattr(flowable, "_bookmark_level", None)
        key = getattr(flowable, "_bookmark_key", None)
        if title and level is not None and key:
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=level, closed=False)

    def _draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("SimSun", 9)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(doc.leftMargin, 1.2 * cm, "DeepResearch Agent - CS599 大作业报告")
        canvas.drawRightString(A4[0] - doc.rightMargin, 1.2 * cm, f"第 {doc.page} 页")
        canvas.restoreState()


def register_fonts() -> tuple[str, str]:
    if SIMSUN.exists():
        pdfmetrics.registerFont(TTFont("SimSun", str(SIMSUN)))
    if SIMHEI.exists():
        pdfmetrics.registerFont(TTFont("SimHei", str(SIMHEI)))
    return "SimSun", "SimHei"


def make_styles() -> dict[str, ParagraphStyle]:
    body_font, heading_font = register_fonts()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCN",
            parent=base["Title"],
            fontName=heading_font,
            fontSize=22,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "Heading1CN",
            parent=base["Heading1"],
            fontName=heading_font,
            fontSize=17,
            leading=24,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=14,
            spaceAfter=8,
            wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "Heading2CN",
            parent=base["Heading2"],
            fontName=heading_font,
            fontSize=13.5,
            leading=20,
            textColor=colors.HexColor("#374151"),
            spaceBefore=10,
            spaceAfter=6,
            wordWrap="CJK",
        ),
        "h3": ParagraphStyle(
            "Heading3CN",
            parent=base["Heading3"],
            fontName=heading_font,
            fontSize=11.5,
            leading=17,
            textColor=colors.HexColor("#4b5563"),
            spaceBefore=8,
            spaceAfter=4,
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "BodyCN",
            parent=base["BodyText"],
            fontName=body_font,
            fontSize=10.5,
            leading=17,
            firstLineIndent=18,
            alignment=TA_LEFT,
            spaceAfter=5,
            wordWrap="CJK",
        ),
        "bullet": ParagraphStyle(
            "BulletCN",
            parent=base["BodyText"],
            fontName=body_font,
            fontSize=10.5,
            leading=17,
            leftIndent=18,
            firstLineIndent=-10,
            spaceAfter=3,
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "CodeCN",
            parent=base["Code"],
            fontName=body_font,
            fontSize=7.4,
            leading=10,
            leftIndent=6,
            rightIndent=6,
            spaceBefore=4,
            spaceAfter=6,
        ),
        "table": ParagraphStyle(
            "TableCN",
            parent=base["BodyText"],
            fontName=body_font,
            fontSize=8.4,
            leading=11,
            wordWrap="CJK",
        ),
    }


def inline_markup(text: str) -> str:
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='SimHei'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def normalize_code(code: str) -> str:
    lines = []
    for line in code.splitlines():
        if len(line) <= 62:
            lines.append(line)
            continue
        current = line
        while len(current) > 62:
            lines.append(current[:62])
            current = "    " + current[62:]
        lines.append(current)
    return "\n".join(lines)


def is_table(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return lines[index].strip().startswith("|") and re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[index + 1])


def consume_table(lines: list[str], index: int, styles: dict[str, ParagraphStyle]) -> tuple[Table, int]:
    raw_rows = []
    i = index
    while i < len(lines) and lines[i].strip().startswith("|"):
        raw = lines[i].strip().strip("|")
        raw_rows.append([cell.strip() for cell in raw.split("|")])
        i += 1
    rows = [raw_rows[0]] + raw_rows[2:]
    data = [
        [Paragraph(inline_markup(cell), styles["table"]) for cell in row]
        for row in rows
    ]
    col_count = max(len(row) for row in data) if data else 1
    table = Table(data, colWidths=[(A4[0] - 4 * cm) / col_count] * col_count, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table, i


def build_story(markdown: str, styles: dict[str, ParagraphStyle]):
    lines = markdown.splitlines()
    story = []
    i = 0
    bookmark_index = 0
    in_code = False
    code_lines: list[str] = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                story.append(Preformatted(normalize_code("\n".join(code_lines)), styles["code"]))
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        if is_table(lines, i):
            table, i = consume_table(lines, i, styles)
            story.append(table)
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith("# "):
            text = stripped[2:].strip()
            para = Paragraph(inline_markup(text), styles["title"] if not story else styles["h1"])
            if story:
                story.append(PageBreak())
            para._bookmark_title = text
            para._bookmark_level = 0
            para._bookmark_key = f"bookmark_{bookmark_index}"
            bookmark_index += 1
            story.append(para)
            i += 1
            continue

        if stripped.startswith("## "):
            text = stripped[3:].strip()
            para = Paragraph(inline_markup(text), styles["h2"])
            para._bookmark_title = text
            para._bookmark_level = 1
            para._bookmark_key = f"bookmark_{bookmark_index}"
            bookmark_index += 1
            story.append(para)
            i += 1
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(inline_markup(stripped[4:].strip()), styles["h3"]))
            i += 1
            continue

        if re.match(r"^(\d+\.|- )", stripped):
            story.append(Paragraph(inline_markup(stripped), styles["bullet"]))
            i += 1
            continue

        story.append(Paragraph(inline_markup(stripped), styles["body"]))
        i += 1

    return story


def main() -> None:
    styles = make_styles()
    markdown = SOURCE.read_text(encoding="utf-8")
    story = build_story(markdown, styles)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = ReportDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.9 * cm,
        title="CS599 大作业报告",
        author="DeepResearch Agent",
    )
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
