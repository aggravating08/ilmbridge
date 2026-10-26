"""Generate the three-page Hacktoberfest report (ReportLab required)."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/IlmBridge_Project_Report.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
W,H = 595.28,841.89
c = canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('IlmBridge | Hacktoberfest Project Report | Asiya Ali')
c.setAuthor('Asiya Ali')
ink='#292638'; purple='#7560bc'; muted='#777181'
body = ParagraphStyle('body', fontName='Helvetica', fontSize=10.4, leading=16, textColor=HexColor(ink))
small = ParagraphStyle('small', parent=body, fontSize=8.3, leading=12, textColor=HexColor(muted))
y=0

def p(text, style=body, gap=11):
    global y
    item=Paragraph(text, style); _, height=item.wrap(W-88, H)
    if y-height < 57: raise ValueError(f'Report content overflows page at {text[:50]}')
    item.drawOn(c,44,y-height); y-=height+gap

def heading(text):
    global y
    y-=6; c.setFont('Helvetica-Bold',12); c.setFillColor(HexColor(purple)); c.drawString(44,y,text); y-=22

def page(number, label, title, subtitle):
    global y
    c.setFillColor(HexColor('#fbfaf7'));c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(HexColor(purple)); c.roundRect(44,H-70,25,25,6,fill=1,stroke=0)
    c.setFillColor(white);c.setFont('Times-Bold',23);c.drawString(52,H-65,'i')
    c.setFillColor(HexColor(ink));c.setFont('Helvetica-Bold',17);c.drawString(77,H-65,'ilmbridge.')
    c.setFont('Helvetica',8);c.setFillColor(HexColor(muted));c.drawRightString(W-44,H-60,'HACKTOBERFEST 2026 / NSTP, ISLAMABAD')
    c.setStrokeColor(HexColor('#e3dfe8'));c.line(44,H-86,W-44,H-86)
    c.setFont('Helvetica-Bold',8);c.setFillColor(HexColor(purple));c.drawString(44,H-111,label.upper())
    c.setFillColor(HexColor(ink));c.setFont('Times-Roman',28);c.drawString(44,H-149,title)
    c.setFont('Helvetica',10);c.setFillColor(HexColor(muted));c.drawString(44,H-170,subtitle)
    c.setStrokeColor(HexColor('#e3dfe8'));c.line(44,44,W-44,44)
    c.setFont('Helvetica',8);c.drawString(44,29,'ASIYA ALI  /  OPEN SOURCE STUDY COMPANION');c.drawRightString(W-44,29,f'{number} / 3')
    y=H-197

page(1,'01 / Purpose and sustainable development','A bridge from notes to understanding.','IlmBridge - local study tools, with an open-source AI companion.')
heading('Relevant UN Sustainable Development Goals')
p('<b>SDG 4 - Quality Education.</b><br/>IlmBridge turns course material into inspectable explanations and recall practice.<br/>It supports self-directed revision without requiring a paid cloud API subscription.<br/>Students can compare responses with source passages and practise missing terms.<br/>These are intended benefits; improved learning outcomes have not been measured.')
p('<b>SDG 10 - Reduced Inequalities.</b><br/>Free source code and source-only operation aim to lower financial barriers.<br/>English, Urdu and Roman Urdu explanation options aim to widen language access.<br/>Local inference can work without internet after the initial installation and download.<br/>Compatible hardware is still required; translation quality needs further evaluation.')
heading('The problem and intended users')
p('Students may have lecture notes but struggle to convert them into a focused revision routine. Generic chat tools can produce answers without an easy path back to the supplied material. IlmBridge is designed for students who want to ask questions, inspect evidence and practise in one private local workspace.')
heading('The working solution')
p('Paste notes or import a TXT/Markdown file. Search original passages, request a local AI explanation, flip revision cards, complete a scored gap-fill exercise, and export a Markdown study pack. A sample biology lesson makes the complete workflow demonstrable immediately.')
p('<b>Participant:</b> Asiya Ali<br/><b>Suggested track:</b> Education &amp; Accessibility / AI &amp; Intelligent Applications<br/><b>Application license:</b> MIT. <b>Model:</b> Qwen2.5 0.5B Instruct, Apache-2.0.',small)
c.showPage()

page(2,'02 / Implementation and experience','One source. Three ways to learn.','Understand the idea. Recall the detail. Check what stayed.')
heading('Technical approach')
p('<b>1. Retrieve:</b> Python splits notes into bounded numbered passages and ranks lexical matches using a BM25-style formula. The top two passages are retrieved; questions with no matching terms receive an explicit no-match response.<br/><b>2. Explain:</b> Selected passages and the question go to local Ollama, running Qwen2.5 0.5B Instruct. The prompt requests source references and supports three explanation languages. Invalid citation numbers are rejected.<br/><b>3. Practise:</b> Revision cards and quiz answers come directly from source sentences. Quiz marking uses case-insensitive exact matching rather than an AI judgment.')
heading('A small, inspectable stack')
p('Python 3.10+ standard library serves the API on 127.0.0.1. Vanilla HTML, CSS and JavaScript provide a responsive interface. Ollama is an optional separate local runtime; its approximately 398 MB model download enables AI explanations. Source search, cards, quizzes and export work without that download.')
image=ROOT/'docs/desktop.jpg'
if image.exists():
    iw,ih=ImageReader(str(image)).getSize(); width=W-88; height=min(195,width*ih/iw)
    c.drawImage(str(image),44,y-height,width=width,height=height,preserveAspectRatio=True,anchor='c',mask='auto');y-=height+11
    p('Actual prototype interface. The status banner indicates whether the local model is connected.',small,gap=5)
heading('A three-minute demonstration')
p('Load the biology sample. Ask how light-dependent reactions support the Calvin cycle. Inspect the original source passages. Flip a revision card, enter a quiz answer, check the score, and download a study pack. Explain which text is retrieved verbatim and which is generated by the model.',gap=5)
c.showPage()

page(3,'03 / Verification and submission','Built to demonstrate. Open to improve.','A functional prototype with explicit limits and reproducible checks.')
heading('Validation and reproducibility')
p('<b>19 automated tests passed.</b> Coverage includes passage ranking, two-stage retrieval, no-match abstention, Unicode, source-derived quiz answers, invalid citations, model failures, API validation and cross-origin protection. Unit tests mock the model boundary; live results are recorded in docs/VALIDATION.md.')
p('Browser checks verified the study interface, source answers, flip cards and quiz feedback. The first sample answer was marked correct and the five blank answers incorrect, producing 1/6. Source tools remain usable if Ollama is unavailable. Live Qwen inference succeeded in 0.65 seconds; missing inline citations were flagged.')
heading('Original contribution and open-source quality')
p('This standalone project was created for the hackathon. Its original application work combines local retrieval, inspectable model responses, deterministic recall practice, a responsive interface, export, and tests. Asiya Ali is the named participant. Codex assisted with code, design, prompts, tests and documentation; no Kiro usage or unverified team collaboration is claimed.')
p('The package includes an MIT license, README, architecture explanation, contribution guide, CI workflow, presenter script and source code. Third-party model/runtime licenses are acknowledged; model weights and runtime binaries are not bundled in the submission ZIP.')
heading('Boundaries and next steps')
p('Citations check source identifiers, not factual entailment. Lexical retrieval misses paraphrases; small-model answers and translations can be wrong. English gap-fill generation is a prototype, with no PDF ingestion or measured educational outcomes. Next steps are teacher-reviewed evaluation, stronger multilingual tests and semantic retrieval.')
heading('Submission readiness')
p('<b>Local run:</b> python3 server.py<br/><b>Tests:</b> python3 -m unittest discover -s tests -v<br/><b>Model setup:</b> ollama pull qwen2.5:0.5b<br/><b>Publication:</b> github.com/aggravating08/ilmbridge (MIT-licensed public repository).<br/><b>Report upload:</b> Use the organizer form before the event; final code submission instructions are announced during the event.')
p('References: huggingface.co/Qwen/Qwen2.5-0.5B-Instruct (Apache-2.0); docs.ollama.com/api/chat; sdgs.un.org/goals/goal4; sdgs.un.org/goals/goal10. Official event brief: Google Doc 1TO-m7CdR5u2bn6XlXaKKxefm4g87TtahJYb9p3Ogt3c.',small,gap=0)
c.save();print(OUT)
