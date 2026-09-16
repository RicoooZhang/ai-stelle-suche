from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

from .models import Block, InlineRun, StructuredDocument
from .template_config import DEFAULT_GERMAN_CV_TEMPLATE, LEGACY_RESUME_TEMPLATE

NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
SECTION_LABELS = {
    "Ausgewählte Projekte und Ergebnisse": "Projekte",
    "Relevante Kompetenzen": "Kompetenzen",
}


def _run(run: InlineRun, size: int | None = None, color: str | None = None) -> str:
    props = ['<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial"/>']
    if run.bold:
        props.append("<w:b/>")
    if run.italic:
        props.append("<w:i/>")
    if size:
        props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    text_parts = run.text.split("\t")
    values: list[str] = []
    for index, value in enumerate(text_parts):
        if index:
            values.append("<w:tab/>")
        if value:
            preserve = ' xml:space="preserve"' if value[:1].isspace() or value[-1:].isspace() else ""
            values.append(f"<w:t{preserve}>{escape(value)}</w:t>")
    return f"<w:r><w:rPr>{''.join(props)}</w:rPr>{''.join(values)}</w:r>"


def _paragraph(runs: tuple[InlineRun, ...], style: str = "Normal", bullet: bool = False, keep_next: bool = False, extra_props: str = "") -> str:
    num = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>' if bullet else ""
    keep = "<w:keepNext/>" if keep_next else ""
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{num}{keep}{extra_props}</w:pPr>{"".join(_run(r) for r in runs)}</w:p>'


def _bold_only(block: Block) -> bool:
    meaningful = [run for run in block.runs if run.text.strip()]
    return bool(meaningful) and all(run.bold for run in meaningful)


def _contact_line(value: str) -> str:
    return re.sub(r"\s*[·|]\s*", " | ", value.strip())


def _entry_parts(value: str) -> tuple[str, str]:
    left, separator, right = value.partition(" · ")
    return (left.strip(), right.strip()) if separator else (value.strip(), "")


def _entry_header(primary: str, secondary: str, date: str) -> str:
    tabs = '<w:tabs><w:tab w:val="right" w:pos="9638"/></w:tabs>'
    runs = _run(InlineRun(primary, bold=True), size=23)
    if secondary:
        runs += _run(InlineRun(f" · {secondary}", bold=True), size=20, color="5F6872")
    runs += _run(InlineRun("\t")) + _run(InlineRun(date, bold=True), size=19, color="5F6872")
    return f'<w:p><w:pPr><w:pStyle w:val="EntryHeader"/><w:keepNext/>{tabs}</w:pPr>{runs}</w:p>'


def render_docx(doc: StructuredDocument, output: Path, preview: bool = False, template_id: str = "") -> None:
    effective_template = template_id or (DEFAULT_GERMAN_CV_TEMPLATE if doc.document_type == "cv" and doc.language == "de" else LEGACY_RESUME_TEMPLATE)
    if doc.document_type == "cv" and effective_template not in {DEFAULT_GERMAN_CV_TEMPLATE, LEGACY_RESUME_TEMPLATE}:
        raise ValueError(f"unsupported DOCX resume template: {effective_template}")
    paragraphs: list[str] = []
    if preview:
        paragraphs.append(_paragraph((InlineRun("DRAFT – PREVIEW ONLY", bold=True),), "Draft"))
    current_section = ""
    title_seen = False
    index = 0
    while index < len(doc.blocks):
        block = doc.blocks[index]
        if block.kind == "heading":
            if doc.document_type == "cv" and block.level == 1 and not title_seen:
                paragraphs.append(_paragraph(block.runs, "Title", keep_next=True))
                title_seen = True
            elif doc.document_type == "cv" and block.level == 2:
                current_section = SECTION_LABELS.get(block.text, block.text)
                paragraphs.append(_paragraph((InlineRun(current_section),), "Heading1", keep_next=True))
            elif (
                doc.document_type == "cv"
                and block.level == 3
                and current_section in {"Berufserfahrung", "Ausbildung"}
                and index + 1 < len(doc.blocks)
                and doc.blocks[index + 1].kind == "paragraph"
                and _bold_only(doc.blocks[index + 1])
            ):
                primary, secondary = _entry_parts(block.text)
                paragraphs.append(_entry_header(primary, secondary, doc.blocks[index + 1].text))
                index += 1
            elif block.level == 1:
                paragraphs.append(_paragraph(block.runs, "Title", keep_next=True))
            else:
                style = f"Heading{min(max(block.level - 1, 1), 3)}"
                paragraphs.append(_paragraph(block.runs, style, keep_next=True))
        elif block.kind == "bullet":
            paragraphs.append(_paragraph(block.runs, bullet=True))
        elif block.kind == "quote":
            paragraphs.append(_paragraph(block.runs, "Quote"))
        elif doc.document_type == "cv" and title_seen and block.text == doc.contact_line:
            paragraphs.append(_paragraph((InlineRun(_contact_line(block.text)),), "Contact", keep_next=True))
        elif (
            doc.document_type == "cv"
            and current_section == "Kompetenzen"
            and _bold_only(block)
            and index + 1 < len(doc.blocks)
            and doc.blocks[index + 1].kind == "paragraph"
        ):
            paragraphs.append(_paragraph(block.runs, "SkillGroup", keep_next=True))
            another_group_follows = (
                index + 2 < len(doc.blocks)
                and doc.blocks[index + 2].kind == "paragraph"
                and _bold_only(doc.blocks[index + 2])
            )
            paragraphs.append(_paragraph(doc.blocks[index + 1].runs, "SkillValues", keep_next=another_group_follows))
            index += 1
        else:
            paragraphs.append(_paragraph(block.runs))
        index += 1
    body = "".join(paragraphs)
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{NS}"><w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="964" w:right="1134" w:bottom="964" w:left="1134" w:header="600" w:footer="600" w:gutter="0"/></w:sectPr></w:body></w:document>'''
    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{NS}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:color w:val="20252B"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="70" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Contact"/><w:qFormat/><w:pPr><w:spacing w:after="30"/><w:keepNext/></w:pPr><w:rPr><w:b/><w:sz w:val="44"/><w:szCs w:val="44"/><w:color w:val="263746"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Contact"><w:name w:val="Contact"/><w:basedOn w:val="Normal"/><w:next w:val="Heading1"/><w:pPr><w:spacing w:after="220" w:line="240" w:lineRule="auto"/><w:keepNext/><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="7" w:color="D6DADE"/></w:pBdr></w:pPr><w:rPr><w:sz w:val="19"/><w:szCs w:val="19"/><w:color w:val="5F6872"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="240" w:after="95"/><w:keepNext/><w:outlineLvl w:val="0"/><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="5" w:color="D6DADE"/></w:pBdr></w:pPr><w:rPr><w:b/><w:sz w:val="26"/><w:szCs w:val="26"/><w:color w:val="263746"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="135" w:after="45"/><w:keepNext/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="22"/><w:szCs w:val="22"/><w:color w:val="20252B"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="100" w:after="30"/><w:keepNext/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="EntryHeader"><w:name w:val="Entry Header"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:spacing w:before="130" w:after="55"/><w:keepNext/><w:keepLines/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="SkillGroup"><w:name w:val="Skill Group"/><w:basedOn w:val="Normal"/><w:next w:val="SkillValues"/><w:pPr><w:spacing w:before="45" w:after="15"/><w:keepNext/><w:keepLines/></w:pPr><w:rPr><w:b/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="SkillValues"><w:name w:val="Skill Values"/><w:basedOn w:val="Normal"/><w:next w:val="SkillGroup"/><w:pPr><w:spacing w:after="70" w:line="260" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="19"/><w:szCs w:val="19"/><w:color w:val="343B43"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360"/><w:spacing w:after="80"/></w:pPr><w:rPr><w:i/><w:color w:val="555555"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Draft"><w:name w:val="Draft"/><w:basedOn w:val="Normal"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="80"/></w:pPr><w:rPr><w:b/><w:color w:val="6B7280"/><w:sz w:val="17"/></w:rPr></w:style></w:styles>'''
    numbering = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering xmlns:w="{NS}"><w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:tabs><w:tab w:val="num" w:pos="360"/></w:tabs><w:ind w:left="360" w:hanging="180"/><w:spacing w:after="45" w:line="270" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="20"/></w:rPr></w:lvl></w:abstractNum><w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>'''
    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/></Relationships>'''
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{escape(doc.title)}</dc:title><dc:creator>ai-job-suche local export</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created></cp:coreProperties>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)
        archive.writestr("word/numbering.xml", numbering)
        archive.writestr("word/_rels/document.xml.rels", doc_rels)
        archive.writestr("docProps/core.xml", core)
