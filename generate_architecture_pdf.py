"""
Script to generate a comprehensive, executive PDF specification
of the Resumind AI System Architecture.
"""

from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Adds 'Page X of Y' and header/footer to each page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 805, "RESUMIND AI — COMPLETE SYSTEM ARCHITECTURE BLUEPRINT")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, 798, 559, 798)

        # Running footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 25, page_str)
        self.drawString(36, 25, "CONFIDENTIAL & PROPRIETARY — RESUMIND AI PLATFORM SPECIFICATION")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 35, 559, 35)

        self.restoreState()


def build_architecture_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#4263EB"),
        spaceAfter=4
    )

    tag_style = ParagraphStyle(
        'DocTag',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#364FC7"),
        spaceAfter=8
    )

    sub_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#364FC7"),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=14,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#1E1B4B")
    )

    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    td_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    td_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # ================= HEADER =================
    story.append(Paragraph("TECHNICAL SPECIFICATION & BLUEPRINT", tag_style))
    story.append(Paragraph("Resumind AI System Architecture", title_style))
    story.append(Paragraph(
        f"<b>Version:</b> 2.0.0 &nbsp;|&nbsp; <b>Release Date:</b> {datetime.now().strftime('%B %Y')} &nbsp;|&nbsp; "
        "<b>Architect:</b> Souradeep Saha &nbsp;|&nbsp; <b>Runtime:</b> PyTorch Local Edge-AI + FastAPI + Streamlit",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4263EB"), spaceAfter=12))

    # ================= 1. EXECUTIVE SUMMARY =================
    story.append(Paragraph("1. Executive Architectural Summary", h1_style))
    story.append(Paragraph(
        "<b>Resumind AI</b> is a high-performance, privacy-first, edge-native career intelligence and candidate evaluation platform. "
        "Unlike conventional HR tools that transmit sensitive candidate documents to third-party cloud LLM APIs (e.g. OpenAI, Anthropic), "
        "Resumind AI executes <b>100% locally</b> in process memory using custom PyTorch deep neural networks, universal section segmenters, "
        "and rule-based ATS taxonomy engines. It provides instantaneous resume auditing, job role prediction with direct apply links, "
        "and interactive mock interview preparation without incurring recurring API fees or exposing candidate data.",
        body_style
    ))

    # Callout Highlight Box
    callout_data = [[
        Paragraph(
            "<b>✦ Core Architectural Principle:</b> Zero External Dependency. Everything runs on the host machine. "
            "Resumes are parsed, vectorized, inferred, and evaluated in sub-1.5 second latency with complete data privacy and offline resilience.",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[523])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EEF2FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#C7D2FE")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 10))

    # ================= 2. THE 6 ARCHITECTURAL LAYERS =================
    story.append(Paragraph("2. The 6-Layer Modular Architecture", h1_style))

    # Layer 1
    story.append(Paragraph("Layer 1: Presentation & Dual Delivery (Streamlit SPA & FastAPI)", h2_style))
    story.append(Paragraph(
        "The system provides two simultaneous interfaces sharing the same underlying neural intelligence core:",
        body_style
    ))
    story.append(Paragraph("• <b>Streamlit SPA (app.py):</b> Reactive light-mode web dashboard featuring four specialized studios: Home, Resume Analyser, Career Paths Explorer, and AI Mock Interview Studio.", bullet_style))
    story.append(Paragraph("• <b>Headless REST API (api/index.py):</b> Production-grade FastAPI server allowing external clients, mobile applications, or corporate ATS systems to ingest resumes via HTTP JSON / multipart endpoints.", bullet_style))

    # Layer 2
    story.append(Paragraph("Layer 2: Ingestion & Text Normalization Layer (PyMuPDF)", h2_style))
    story.append(Paragraph(
        "• <b>In-Memory Parsing:</b> Decodes uploaded PDF byte streams directly in RAM without writing temporary files to disk, eliminating filesystem overhead and preventing data leakage.<br/>"
        "• <b>Reading Order Sorter:</b> Employs <code>pymupdf.open(stream, filetype='pdf')</code> with structural coordinate sorting (<code>sort=True</code>) to accurately reconstruct multi-column, side-by-side, and tabular resume layouts into natural English reading order.<br/>"
        "• <b>Metadata Extraction:</b> Utilizes high-precision regex anchors to extract candidate contact coordinates (Email, Phone, LinkedIn, GitHub).",
        body_style
    ))

    # Layer 3
    story.append(Paragraph("Layer 3: Universal Resume Observer & Domain Taxonomy (ai_engine/)", h2_style))
    story.append(Paragraph(
        "• <b>Section Segmenter (field_extractor.py):</b> Employs robust pattern boundary detection to isolate Education, Work Experience, Projects, Certifications, and Languages independently.<br/>"
        "• <b>Domain Taxonomy Database (resume_observer.py):</b> Curated lexicon of over 6,000+ industry skills across 8 core verticals: <i>IT & Software, Data Science & AI, Database, Cloud & DevOps, Cybersecurity, Accounting & Finance, Sales & Marketing, HR, and Management</i>.",
        body_style
    ))

    # Layer 4
    story.append(Paragraph("Layer 4: Deep Learning & PyTorch Neural Inference Layer", h2_style))
    story.append(Paragraph(
        "• <b>Hardware-Agnostic Execution:</b> Automatically binds to an NVIDIA CUDA GPU (e.g., RTX 2050) when available, and seamlessly defaults to CPU on non-GPU laptops with zero code changes.<br/>"
        "• <b>Model 1: SkillNet (SouraSkillNet):</b> Multi-label neural classifier (Linear -> BatchNorm1d -> ReLU -> Dropout -> Sigmoid) trained on resume embeddings to predict 30+ competencies with confidence percentages.<br/>"
        "• <b>Model 2: ResumindMatchNet:</b> Deep neural regression network evaluating joint candidate-job embeddings to compute semantic compatibility scores ($0.0 - 100.0\\%$).<br/>"
        "• <b>Memory Singleton Caching:</b> Models remain resident in process memory and evaluate via <code>torch.no_grad()</code> for sub-second inference.",
        body_style
    ))

    # Layer 5
    story.append(Paragraph("Layer 5: Decision Intelligence & Strategic Reasoning Layer", h2_style))
    story.append(Paragraph(
        "• <b>Hybrid ATS Calibration (llm_analyzer.py):</b> Combines deterministic keyword taxonomy matching (60% weight) with neural semantic prediction (40% weight) to generate a balanced hiring probability.<br/>"
        "• <b>Job Role Predictor (job_predictor.py):</b> Compares candidate competencies against 16+ market roles, generates personalized rationales ('Why this role fits your profile'), identifies skills to learn, and generates live apply links for LinkedIn, Indeed, and Glassdoor.<br/>"
        "• <b>AI Mock Interview Studio (interview_engine.py):</b> Curates technical MCQs and STAR-method behavioral scenarios tailored to the resume, evaluates answers, and awards readiness tiers.",
        body_style
    ))

    # Layer 6
    story.append(Paragraph("Layer 6: Document Generation & Formal Export Layer", h2_style))
    story.append(Paragraph(
        "• <b>Executive Report Generator:</b> Compiles candidate career audit reports and interview readiness summaries into formal, downloadable PDF documents using ReportLab.",
        body_style
    ))

    story.append(Spacer(1, 8))

    # ================= 3. SYSTEM DATA FLOW =================
    story.append(Paragraph("3. End-to-End Data Flow Lifecycle", h1_style))

    flow_table_data = [
        [Paragraph("Step", th_style), Paragraph("Stage", th_style), Paragraph("Component", th_style), Paragraph("Description", th_style)],
        [Paragraph("01", td_bold), Paragraph("Upload", td_style), Paragraph("Streamlit / FastAPI", td_style), Paragraph("Candidate drops PDF resume + optional target job description.", td_style)],
        [Paragraph("02", td_bold), Paragraph("Text Extraction", td_style), Paragraph("PyMuPDF (fitz)", td_style), Paragraph("In-memory parsing, reading-order sorting, UTF-8 normalization.", td_style)],
        [Paragraph("03", td_bold), Paragraph("Segmentation", td_style), Paragraph("resume_observer.py", td_style), Paragraph("Extracts contact info, education, experience, and domain taxonomy.", td_style)],
        [Paragraph("04", td_bold), Paragraph("Neural Inference", td_style), Paragraph("PyTorch SkillNet", td_style), Paragraph("Generates multi-label skill confidence probabilities (RTX GPU/CPU).", td_style)],
        [Paragraph("05", td_bold), Paragraph("Job Matching", td_style), Paragraph("MatchNet + matcher.py", td_style), Paragraph("Calculates blended ATS score: 60% deterministic + 40% neural.", td_style)],
        [Paragraph("06", td_bold), Paragraph("Role Prediction", td_style), Paragraph("job_predictor.py", td_style), Paragraph("Predicts top job matches, fit reasons, and generates live apply links.", td_style)],
        [Paragraph("07", td_bold), Paragraph("Interview Prep", td_style), Paragraph("interview_engine.py", td_style), Paragraph("Generates calibrated mock test, evaluates answers, assigns tier.", td_style)],
        [Paragraph("08", td_bold), Paragraph("Report Export", td_style), Paragraph("ReportLab Engine", td_style), Paragraph("Generates downloadable PDF audit and interview readiness reports.", td_style)],
    ]

    flow_table = Table(flow_table_data, colWidths=[32, 75, 110, 306])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4263EB")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 12))

    # ================= 4. REST API SPECIFICATION =================
    story.append(Paragraph("4. Built-in REST API Endpoints (api/index.py)", h1_style))
    story.append(Paragraph(
        "Resumind AI provides a fully autonomous FastAPI backend that can be consumed by external client applications:",
        body_style
    ))

    api_table_data = [
        [Paragraph("Method", th_style), Paragraph("Endpoint", th_style), Paragraph("Payload", th_style), Paragraph("Output / Purpose", th_style)],
        [Paragraph("POST", td_bold), Paragraph("/api/analyze", td_style), Paragraph("PDF file / JSON", td_style), Paragraph("Full candidate audit, match scores, verified & missing skills, JSON analysis.", td_style)],
        [Paragraph("GET", td_bold), Paragraph("/api/health", td_style), Paragraph("None", td_style), Paragraph("System status, service version, and PyTorch neural engine confirmation.", td_style)],
        [Paragraph("GET", td_bold), Paragraph("/", td_style), Paragraph("None", td_style), Paragraph("Serves the standalone HTML5/CSS3 client evaluation portal.", td_style)],
    ]
    api_table = Table(api_table_data, colWidths=[45, 80, 85, 313])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#364FC7")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 12))

    # ================= 5. DIRECTORY BLUEPRINT =================
    story.append(Paragraph("5. Project Repository & Directory Blueprint", h1_style))

    repo_table_data = [
        [Paragraph("File / Directory", th_style), Paragraph("Role & Core Architectural Responsibility", th_style)],
        [Paragraph("app.py", td_bold), Paragraph("Streamlit reactive UI, dashboard cards, tab navigation, and Plotly visualizations.", td_style)],
        [Paragraph("job_predictor.py", td_bold), Paragraph("Career prediction engine, role scoring, personalized rationale, and live job search URLs.", td_style)],
        [Paragraph("interview_engine.py", td_bold), Paragraph("AI mock interview question bank, test generator, evaluation tiering, and PDF report generator.", td_style)],
        [Paragraph("llm_analyzer.py", td_bold), Paragraph("Hybrid audit synthesizer (60% deterministic ATS + 40% PyTorch neural match).", td_style)],
        [Paragraph("matcher.py", td_bold), Paragraph("Deterministic keyword overlap, domain taxonomy mapping, and gap identifier.", td_style)],
        [Paragraph("config.py", td_bold), Paragraph("Centralized paths, environment loading, and PyTorch device detection (CUDA/CPU).", td_style)],
        [Paragraph("ai_engine/inference.py", td_bold), Paragraph("Unified PyTorch inference wrapper with singleton predictor caching.", td_style)],
        [Paragraph("ai_engine/skill_model.py", td_bold), Paragraph("PyTorch SouraSkillNet multi-label neural network definition.", td_style)],
        [Paragraph("ai_engine/matching_model.py", td_bold), Paragraph("PyTorch ResumindMatchNet neural regressor definition.", td_style)],
        [Paragraph("ai_engine/resume_observer.py", td_bold), Paragraph("Universal multi-domain resume parser and 6,000+ skill taxonomy database.", td_style)],
        [Paragraph("api/index.py", td_bold), Paragraph("FastAPI server providing headless REST endpoints for third-party integrations.", td_style)],
        [Paragraph("models/", td_bold), Paragraph("Serialized weights (.pth) and TF-IDF feature extractors (.joblib).", td_style)],
        [Paragraph("run.bat & start.sh", td_bold), Paragraph("1-click automated deployment runners for Windows, macOS, and Linux.", td_style)],
    ]

    repo_table = Table(repo_table_data, colWidths=[140, 383])
    repo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(repo_table)
    story.append(Spacer(1, 12))

    # ================= 6. ARCHITECTURAL COMPARISON =================
    story.append(Paragraph("6. Architectural Advantages Over Cloud-Only Solutions", h1_style))

    comp_table_data = [
        [Paragraph("Dimension", th_style), Paragraph("Cloud API Architectures (OpenAI / Gemini)", th_style), Paragraph("Resumind AI Local Architecture", th_style)],
        [Paragraph("Candidate Privacy", td_bold), Paragraph("Resumes uploaded to commercial cloud servers.", td_style), Paragraph("<b>100% Private</b>; processed in local RAM only.", td_style)],
        [Paragraph("Cost Structure", td_bold), Paragraph("Recurring per-token API charges ($$$).", td_style), Paragraph("<b>$0 Forever</b>; zero external subscriptions.", td_style)],
        [Paragraph("Inference Speed", td_bold), Paragraph("10 - 25 seconds per resume (network roundtrips).", td_style), Paragraph("<b>< 1.5 seconds</b> (local PyTorch execution).", td_style)],
        [Paragraph("Offline Resilience", td_bold), Paragraph("Completely fails without active internet connection.", td_style), Paragraph("<b>100% Functional Offline</b>; self-contained.", td_style)],
        [Paragraph("Model Ownership", td_bold), Paragraph("Owned and controlled by third-party vendor.", td_style), Paragraph("<b>100% Owned by You</b> (.pth neural checkpoints).", td_style)],
    ]

    comp_table = Table(comp_table_data, colWidths=[90, 215, 218])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4263EB")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(comp_table)

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Architecture PDF successfully built at: {output_path}")


if __name__ == "__main__":
    pdf_dest = Path("Resumind_AI_System_Architecture.pdf").resolve()
    build_architecture_pdf(str(pdf_dest))
