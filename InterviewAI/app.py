"""
InterviewAI — Main Application
Run: streamlit run app.py
"""

import streamlit as st
import sys
import os
import json
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agents.cv_agent import parse_cv_text, parse_cv_pdf
from core.agents.jd_agent import parse_job_description
from core.agents.question_agent import generate_interview_questions, build_interview_flow
from core.graph.skill_graph import SkillGraph, build_graph
from core.graph.state import InterviewState
from core.graph.traversal import pick_next_skill, decide_follow_up
from core.pipeline.interview_loop import InterviewLoop
from core.report.generator import generate_report
from core.graph.visualize import (
    render_candidate_graph,
    render_job_graph,
    render_gap_graph,
    render_full_graph,
)
from core.interview.room_components import (
    DEVICE_SETUP_HTML,
    get_interview_question_html,
    get_controls_html,
)

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InterviewAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Logger helper ────────────────────────────────────────────────────────────
def add_log(message: str, level: str = "INFO"):
    """Add a log entry to session state for display."""
    if "logs" not in st.session_state:
        st.session_state["logs"] = []
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["logs"].append(f"[{ts}] [{level}] {message}")
    if len(st.session_state["logs"]) > 50:
        st.session_state["logs"] = st.session_state["logs"][-50:]


# ─── Start background web server (serves LiveKit client + tokens) ──────────
from core.livekit.whisper_server import start_whisper_server
WHISPER_SERVER_STARTED = False
if not WHISPER_SERVER_STARTED:
    start_whisper_server()
    WHISPER_SERVER_STARTED = True

# ─── Global Styles ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1f36 0%, #1b2838 100%); }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stMarkdown h3 { color: #ffffff !important; }

    /* Main content */
    .block-container { padding-top: 1.5rem; max-width: 1200px; }
    h1 { color: #1a202c; font-weight: 700; }
    h2 { color: #2c5282; font-weight: 600; }
    h3 { color: #2d3748; font-weight: 600; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem;
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: 500;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    [data-testid="stMetric"] label { font-size: 0.8rem !important; color: #718096 !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.4rem !important; color: #2d3748 !important; }

    /* Cards */
    .skill-tag {
        background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
        border: 1px solid #bee3f8;
        padding: 6px 14px;
        border-radius: 20px;
        margin: 3px;
        display: inline-block;
        font-size: 0.82rem;
        font-weight: 500;
        color: #2c5282;
    }
    .skill-tag-red {
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
        border: 1px solid #feb2b2;
        color: #c53030;
    }
    .skill-tag-green {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border: 1px solid #9ae6b4;
        color: #276749;
    }
    .skill-tag-yellow {
        background: linear-gradient(135deg, #fffff0 0%, #fefcbf 100%);
        border: 1px solid #fefcbf;
        color: #975a16;
    }

    /* Section dividers */
    .section-header {
        background: linear-gradient(90deg, #2c5282 0%, #4299e1 100%);
        color: white !important;
        padding: 10px 20px;
        border-radius: 8px;
        margin: 20px 0 15px 0;
        font-weight: 600;
    }

    /* Log box */
    .log-box {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 0.75rem;
        background: #1a202c;
        color: #68d391;
        padding: 16px;
        border-radius: 10px;
        max-height: 250px;
        overflow-y: auto;
        line-height: 1.5;
        border: 1px solid #2d3748;
    }
    .log-box .error { color: #fc8181; }
    .log-box .warn { color: #f6e05e; }

    /* Button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2c5282 0%, #4299e1 100%);
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1rem;
    }

    /* Expander */
    .streamlit-expanderHeader { font-weight: 600; font-size: 0.95rem; }

    /* Graph container */
    .graph-container {
        background: #fafbfc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🧠 InterviewAI")
    st.markdown("*Multi-Agent Interview Platform*")
    st.markdown("---")

    st.markdown("### Pipeline")
    st.markdown("""
    **Step 1** → Upload CV + Job Description  
    **Step 2** → View parsed analysis  
    **Step 3** → Skill graph & gap analysis  
    """)

    st.markdown("---")
    st.markdown("### System Status")

    # Show API config status
    from core.config import GEMINI_API_KEY
    if GEMINI_API_KEY:
        st.markdown("✅ Gemini API Key loaded")
    else:
        st.markdown("❌ **API Key missing!** Check `.env`")

    st.markdown("✅ NetworkX Graph Engine")
    st.markdown("✅ ESCO Taxonomy (1,201 skills)")

    st.markdown("---")
    st.markdown("### Modules Active")
    st.markdown("M1 — CV Parser")
    st.markdown("M2 — JD Analyser")
    st.markdown("M3 — Skill Graph")
    st.markdown("M4 — Question Generator")
    st.markdown("M5 — Interview Room")
    st.markdown("M6 — LLM-as-Judge Evaluator")
    st.markdown("M7-M10 — Adaptive Live Interview")
    st.markdown("M11-M12 — Report Generator")

    st.markdown("---")

    # Pipeline state indicator
    st.markdown("### Data State")
    has_cv = "cv_data" in st.session_state
    has_jd = "jd_data" in st.session_state
    has_graph = "graph_data" in st.session_state
    has_live = "interview_loop" in st.session_state
    st.markdown(f"{'✅' if has_cv else '⬜'} CV Parsed")
    st.markdown(f"{'✅' if has_jd else '⬜'} JD Parsed")
    st.markdown(f"{'✅' if has_graph else '⬜'} Graph Built")
    st.markdown(f"{'✅' if has_live else '⬜'} Live Session")

    st.markdown("---")
    st.caption("CMP7200 — Masters Project")

# ─── Main Header ─────────────────────────────────────────────────────────────
st.markdown("# 🧠 InterviewAI Platform")
st.markdown("*Intelligent Multi-Agent Interview System — Pre-Interview Pipeline*")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab_logs = st.tabs([
    "📥  Step 1: Upload",
    "📊  Step 2: Analysis",
    "🎯  Step 3: Skill Graph",
    "❓  Step 4: Questions",
    "🧪  Step 5: Live Interview",
    "📋  Step 6: Report",
    "📋  Logs",
])

with tab1:
    st.markdown("## Upload Inputs")
    st.caption("Upload your CV and paste the job description")
    st.markdown("---")

    col_cv, col_jd = st.columns(2, gap="large")

    # ─── CV Input ─────────────────────────────────────────────────────────
    with col_cv:
        st.markdown("### 📄 Candidate CV")

        upload_method = st.radio(
            "How would you like to provide the CV?",
            ["Upload PDF", "Paste Text"],
            horizontal=True,
            key="cv_method",
        )

        if upload_method == "Upload PDF":
            uploaded = st.file_uploader(
                "Upload CV (PDF)",
                type=["pdf"],
                key="cv_upload",
                help="Upload a PDF resume. Text will be extracted automatically.",
            )
            if uploaded:
                st.session_state["cv_file"] = uploaded.read()
                st.session_state["cv_filename"] = uploaded.name
                # Clear text input if switching to PDF
                st.session_state.pop("cv_raw_text", None)
                st.success(f"✅ Uploaded: {uploaded.name} ({len(st.session_state['cv_file'])} bytes)")
                add_log(f"PDF uploaded: {uploaded.name} ({len(st.session_state['cv_file'])} bytes)")
            else:
                st.session_state.pop("cv_file", None)
                st.session_state.pop("cv_filename", None)
        else:
            # Clear PDF if switching to text
            st.session_state.pop("cv_file", None)
            st.session_state.pop("cv_filename", None)
            cv_text = st.text_area(
                "Paste CV text",
                height=300,
                placeholder="Paste the full CV content here...",
                key="cv_text_input",
            )
            if cv_text and cv_text.strip():
                st.session_state["cv_raw_text"] = cv_text.strip()
            else:
                st.session_state.pop("cv_raw_text", None)

    # ─── JD Input ─────────────────────────────────────────────────────────
    with col_jd:
        st.markdown("### 💼 Job Description")

        jd_text = st.text_area(
            "Paste the job description",
            height=350,
            placeholder=(
                "Paste the full job description here...\n\n"
                "Include:\n"
                "- Required skills and qualifications\n"
                "- Responsibilities\n"
                "- Experience level"
            ),
            key="jd_text_input",
        )
        if jd_text and jd_text.strip():
            st.session_state["jd_raw_text"] = jd_text.strip()
        else:
            st.session_state.pop("jd_raw_text", None)

    st.markdown("---")

    # ─── Check readiness ──────────────────────────────────────────────────
    has_cv_input = bool(
        st.session_state.get("cv_file") or st.session_state.get("cv_raw_text")
    )
    has_jd_input = bool(st.session_state.get("jd_raw_text"))

    # Show status
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        if has_cv_input:
            src = "PDF" if st.session_state.get("cv_file") else "Text"
            st.success(f"CV ready ({src})")
        else:
            st.warning("CV not provided")
    with status_col2:
        if has_jd_input:
            st.success("Job description ready")
        else:
            st.warning("Job description not provided")

    inputs_ready = has_cv_input and has_jd_input

    if inputs_ready:
        if st.button("🚀 Run Full Pipeline", type="primary", width='stretch'):
            add_log("Pipeline started...")
            progress = st.progress(0, text="Starting pipeline...")

            # ── Module 1: Parse CV ──
            progress.progress(10, text="M1: Parsing CV...")
            add_log("M1: CV Agent starting...")
            try:
                if st.session_state.get("cv_file"):
                    add_log(f"M1: Parsing PDF ({len(st.session_state['cv_file'])} bytes)")
                    cv_data = parse_cv_pdf(st.session_state["cv_file"])
                else:
                    text_len = len(st.session_state.get("cv_raw_text", ""))
                    add_log(f"M1: Parsing text ({text_len} chars)")
                    cv_data = parse_cv_text(st.session_state["cv_raw_text"])
                st.session_state["cv_data"] = cv_data
                n_skills = len(cv_data.get("skills", []))
                add_log(f"M1: SUCCESS - {n_skills} skills, name='{cv_data.get('name', 'N/A')}'")
            except Exception as e:
                add_log(f"M1: FAILED - {str(e)}", "ERROR")
                add_log(traceback.format_exc(), "ERROR")
                st.error(f"❌ CV parsing failed: {e}")
                progress.empty()
                st.stop()

            # ── Module 2: Parse JD ──
            progress.progress(40, text="M2: Analysing job description...")
            add_log("M2: JD Agent starting...")
            try:
                jd_data = parse_job_description(st.session_state["jd_raw_text"])
                st.session_state["jd_data"] = jd_data
                n_req = len(jd_data.get("required_skills", []))
                add_log(f"M2: SUCCESS - {n_req} required skills, title='{jd_data.get('job_title', 'N/A')}'")
            except Exception as e:
                add_log(f"M2: FAILED - {str(e)}", "ERROR")
                add_log(traceback.format_exc(), "ERROR")
                st.error(f"❌ JD analysis failed: {e}")
                progress.empty()
                st.stop()

            # ── Module 3: Build Graph ──
            progress.progress(70, text="M3: Building skill graph...")
            add_log("M3: Skill Graph building...")
            try:
                sg = build_graph(cv_data, jd_data)
                gaps = sg.analyse_gaps()
                topics = sg.get_interview_topics()
                stats = sg.get_stats()
                st.session_state["graph_data"] = {
                    "gaps": gaps,
                    "topics": topics,
                    "stats": stats,
                    "skill_graph_obj": sg,
                }
                add_log(f"M3: SUCCESS - Match={gaps['match_percentage']}%, "
                        f"Nodes={stats['nodes']}, Topics={len(topics)}")
            except Exception as e:
                add_log(f"M3: FAILED - {str(e)}", "ERROR")
                add_log(traceback.format_exc(), "ERROR")
                st.error(f"❌ Graph building failed: {e}")
                progress.empty()
                st.stop()

            progress.progress(100, text="Pipeline complete!")
            add_log("Pipeline COMPLETE. All modules passed.")
            st.success("✅ Pipeline complete! Check the **Analysis** and **Skill Graph** tabs.")
            st.balloons()
    else:
        st.info("👆 Provide both a CV and Job Description above, then click **Run Full Pipeline**.")

with tab2:
    st.markdown("## Analysis Results")
    st.caption("Parsed output from M1 (CV Agent) and M2 (JD Agent)")
    st.markdown("---")

    if "cv_data" not in st.session_state or "jd_data" not in st.session_state:
        st.info("⏳ Run the pipeline first from Step 1 tab.")
    else:
        cv = st.session_state["cv_data"]
        jd = st.session_state["jd_data"]

        # ─── CV Results ───────────────────────────────────────────────────
        st.markdown('<div class="section-header">📄 Module 1 — CV Parse Results</div>',
                    unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Candidate", cv.get("name", "Unknown"))
        m2.metric("Skills Found", len(cv.get("skills", [])))
        m3.metric("Experience", len(cv.get("experience", [])))
        m4.metric("Projects", len(cv.get("projects", [])))

        with st.expander("🔍 Skills Extracted", expanded=True):
            skills = cv.get("skills", [])
            if skills:
                tags_html = " ".join(
                    f'<span class="skill-tag">{s}</span>' for s in skills
                )
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.warning("No skills extracted.")

        with st.expander("💼 Experience"):
            for exp in cv.get("experience", []):
                if isinstance(exp, dict):
                    st.markdown(
                        f"**{exp.get('title', 'N/A')}** at {exp.get('company', 'N/A')} "
                        f"— {exp.get('duration', '')}"
                    )
                    highlights = exp.get("highlights", "")
                    if highlights:
                        if isinstance(highlights, list):
                            st.caption(", ".join(str(h) for h in highlights))
                        else:
                            st.caption(str(highlights))
                else:
                    st.markdown(f"- {exp}")

        with st.expander("🎓 Education"):
            for edu in cv.get("education", []):
                if isinstance(edu, dict):
                    st.markdown(f"**{edu.get('degree', '')}** — {edu.get('institution', '')} ({edu.get('year', '')})")
                else:
                    st.markdown(f"- {edu}")

        with st.expander("🛠 Projects"):
            for proj in cv.get("projects", []):
                if isinstance(proj, dict):
                    st.markdown(f"**{proj.get('name', 'N/A')}** — {proj.get('technologies', '')}")
                    if proj.get("description"):
                        st.caption(proj["description"])
                else:
                    st.markdown(f"- {proj}")

        st.markdown("---")

        # ─── JD Results ───────────────────────────────────────────────────
        st.markdown('<div class="section-header">💼 Module 2 — Job Description Results</div>',
                    unsafe_allow_html=True)

        j1, j2, j3, j4 = st.columns(4)
        j1.metric("Job Title", jd.get("job_title", "N/A"))
        j2.metric("Required Skills", len(jd.get("required_skills", [])))
        j3.metric("Role Level", str(jd.get("role_level", "N/A")).title())
        j4.metric("Domain", str(jd.get("domain", "N/A")).title())

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Required Skills:**")
            req_tags = " ".join(
                f'<span class="skill-tag skill-tag-red">{s}</span>'
                for s in jd.get("required_skills", [])
            )
            st.markdown(req_tags, unsafe_allow_html=True)

        with col2:
            st.markdown("**Nice to Have:**")
            nice_tags = " ".join(
                f'<span class="skill-tag skill-tag-yellow">{s}</span>'
                for s in jd.get("nice_to_have", [])
            )
            st.markdown(nice_tags, unsafe_allow_html=True)

with tab3:
    st.markdown("## Skill Graph Analysis")
    st.caption("Visual knowledge graph — gap analysis and recommended interview topics (M3)")
    st.markdown("---")

    if "graph_data" not in st.session_state:
        st.info("⏳ Run the pipeline first from Step 1 tab.")
    else:
        gaps = st.session_state["graph_data"]["gaps"]
        topics = st.session_state["graph_data"]["topics"]
        stats = st.session_state["graph_data"]["stats"]
        sg = st.session_state["graph_data"]["skill_graph_obj"]

        # ─── Metrics ──────────────────────────────────────────────────────
        match_pct = gaps["match_percentage"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Match Score", f"{match_pct}%")
        col2.metric("Graph Nodes", stats["nodes"])
        col3.metric("Candidate Skills", stats["candidate_skills"])
        col4.metric("Job Requirements", stats["job_required"])

        st.markdown("---")

        # ─── Visual Graphs ────────────────────────────────────────────────
        st.markdown('<div class="section-header">📊 Skill Knowledge Graphs</div>',
                    unsafe_allow_html=True)

        graph_tab1, graph_tab2, graph_tab3, graph_tab4 = st.tabs([
            "🟢 Candidate Skills",
            "🔴 Job Requirements",
            "⚡ Gap Analysis",
            "🗺 Full Map",
        ])

        with graph_tab1:
            st.markdown("#### Candidate's Skill Network")
            st.caption("Shows skills the candidate possesses and their relationships")
            with st.spinner("Rendering graph..."):
                img_buf = render_candidate_graph(sg)
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.image(img_buf, width='stretch')
                st.markdown('</div>', unsafe_allow_html=True)

        with graph_tab2:
            st.markdown("#### Job Requirements Network")
            st.caption("Shows skills required by the job and nice-to-have skills")
            with st.spinner("Rendering graph..."):
                img_buf = render_job_graph(sg)
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.image(img_buf, width='stretch')
                st.markdown('</div>', unsafe_allow_html=True)

        with graph_tab3:
            st.markdown("#### Skill Gap Visualization")
            st.caption("Green = Matched | Red = Missing | Blue = Extra candidate skills")
            with st.spinner("Rendering graph..."):
                img_buf = render_gap_graph(sg)
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.image(img_buf, width='stretch')
                st.markdown('</div>', unsafe_allow_html=True)

        with graph_tab4:
            st.markdown("#### Complete Skill Map")
            st.caption("All skills combined — candidate, required, and bonus")
            with st.spinner("Rendering graph..."):
                img_buf = render_full_graph(sg)
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.image(img_buf, width='stretch')
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ─── Gap Analysis Details ─────────────────────────────────────────
        st.markdown('<div class="section-header">🔍 Detailed Gap Analysis</div>',
                    unsafe_allow_html=True)

        col_match, col_miss = st.columns(2, gap="large")

        with col_match:
            st.markdown("#### ✅ Skills Matched (Required)")
            if gaps["matched_required"]:
                tags = " ".join(
                    f'<span class="skill-tag skill-tag-green">{s.title()}</span>'
                    for s in gaps["matched_required"]
                )
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.warning("No required skills matched.")

            st.markdown("")
            st.markdown("#### 🌟 Bonus Skills Matched")
            if gaps["matched_nice_to_have"]:
                tags = " ".join(
                    f'<span class="skill-tag skill-tag-yellow">{s.title()}</span>'
                    for s in gaps["matched_nice_to_have"]
                )
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.caption("None")

        with col_miss:
            st.markdown("#### ❌ Missing Required Skills")
            if gaps["missing_required"]:
                tags = " ".join(
                    f'<span class="skill-tag skill-tag-red">{s.title()}</span>'
                    for s in gaps["missing_required"]
                )
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.success("No gaps — full match!")

            st.markdown("")
            st.markdown("#### 💡 Extra Skills (not in JD)")
            if gaps["extra_skills"]:
                tags = " ".join(
                    f'<span class="skill-tag">{s.title()}</span>'
                    for s in gaps["extra_skills"][:12]
                )
                st.markdown(tags, unsafe_allow_html=True)

        st.markdown("---")

        # ─── Interview Topics ─────────────────────────────────────────────
        st.markdown('<div class="section-header">🎤 Recommended Interview Topics</div>',
                    unsafe_allow_html=True)
        st.caption("These will feed into Module 4 (Question Generator)")

        for i, t in enumerate(topics, 1):
            priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            icon = priority_colors.get(t["priority"], "⚪")
            with st.container():
                c1, c2, c3 = st.columns([2, 4, 2])
                c1.markdown(f"**{icon} {t['skill'].title()}**")
                c2.markdown(f"_{t['reason']}_")
                c3.markdown(f"`{t['priority'].upper()}`")

# ─── Tab 4: Question Generator ────────────────────────────────────────────────
with tab4:
    st.markdown("## Interview Questions")
    st.caption("AI-generated personalised questions based on skill gap analysis (M4)")
    st.markdown("---")

    if "graph_data" not in st.session_state:
        st.info("⏳ Complete Steps 1-3 first (run the pipeline).")
    else:
        # Generate questions button
        if "interview_questions" not in st.session_state:
            if st.button("🧠 Generate Interview Questions", type="primary", use_container_width=True):
                add_log("M4: Generating interview questions...")
                with st.spinner("M4: Generating personalised interview questions..."):
                    try:
                        questions = generate_interview_questions(
                            topics=st.session_state["graph_data"]["topics"],
                            cv_data=st.session_state["cv_data"],
                            jd_data=st.session_state["jd_data"],
                        )
                        st.session_state["interview_questions"] = questions
                        st.session_state["interview_flow"] = build_interview_flow(questions)
                        add_log(f"M4: SUCCESS - {questions['total_questions']} questions generated, "
                                f"~{questions['estimated_duration_mins']} min interview")
                        st.rerun()
                    except Exception as e:
                        add_log(f"M4: FAILED - {str(e)}", "ERROR")
                        st.error(f"❌ Question generation failed: {e}")
        else:
            questions = st.session_state["interview_questions"]

            # Metrics
            q1, q2, q3, q4 = st.columns(4)
            q1.metric("Total Questions", questions["total_questions"])
            q2.metric("Est. Duration", f"{questions['estimated_duration_mins']} min")
            q3.metric("Technical", len(questions.get("technical", [])))
            q4.metric("Behavioural", len(questions.get("behavioural", [])))

            st.markdown("---")

            # Opening Questions
            st.markdown('<div class="section-header">👋 Opening Questions</div>',
                        unsafe_allow_html=True)
            for q in questions.get("opening", []):
                st.markdown(f"**Q:** {q['question']}")
                st.caption(f"Purpose: {q.get('purpose', '')}")

            # Technical Questions
            st.markdown('<div class="section-header">⚙️ Technical Questions</div>',
                        unsafe_allow_html=True)
            for i, q in enumerate(questions.get("technical", []), 1):
                with st.expander(f"Q{i}: {q.get('skill', 'Technical')} ({q.get('difficulty', 'medium')})"):
                    st.markdown(f"**{q['question']}**")
                    if q.get("follow_up"):
                        st.caption(f"Follow-up: {q['follow_up']}")
                    diff = q.get("difficulty", "medium")
                    diff_colors = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
                    st.markdown(f"Difficulty: {diff_colors.get(diff, '⚪')} {diff.title()}")

            # Behavioural Questions
            st.markdown('<div class="section-header">🧠 Behavioural Questions</div>',
                        unsafe_allow_html=True)
            for i, q in enumerate(questions.get("behavioural", []), 1):
                with st.expander(f"B{i}: {q.get('competency', 'Behavioural')}"):
                    st.markdown(f"**{q['question']}**")
                    if q.get("follow_up"):
                        st.caption(f"Follow-up: {q['follow_up']}")

            # Closing Questions
            st.markdown('<div class="section-header">🏁 Closing Questions</div>',
                        unsafe_allow_html=True)
            for q in questions.get("closing", []):
                st.markdown(f"**Q:** {q['question']}")

            st.markdown("---")
            if st.button("🔄 Regenerate Questions"):
                del st.session_state["interview_questions"]
                if "interview_flow" in st.session_state:
                    del st.session_state["interview_flow"]
                st.rerun()

# ─── Tab 5: Live Interview (Adaptive) ─────────────────────────────────────────
with tab5:
    st.markdown("## 🧪 Adaptive Live Interview")
    st.caption("Dynamic question selection — LLM-as-Judge evaluation on each answer (M6-M10)")
    st.markdown("---")

    if "graph_data" not in st.session_state:
        st.info("⏳ Complete Steps 1-3 first (run the pipeline).")
    else:
        # Start / Reset
        if "interview_loop" not in st.session_state:
            col_text, col_lk = st.columns(2)

            with col_text:
                st.markdown("### 💬 Text Interview")
                st.caption("Type answers manually — works immediately")
                if st.button("🚀 Start Adaptive Interview", type="primary", use_container_width=True):
                    topics = st.session_state["graph_data"]["topics"]
                    loop = InterviewLoop(
                        topics=topics,
                        cv_data=st.session_state["cv_data"],
                        jd_data=st.session_state["jd_data"],
                    )
                    st.session_state["interview_loop"] = loop
                    st.session_state["live_mode"] = "text"
                    st.session_state["live_answers"] = []
                    st.session_state["live_current_result"] = None
                    st.session_state["live_q_history"] = []
                    add_log("Live Interview: Adaptive session started (text mode)")
                    st.rerun()

            with col_lk:
                st.markdown("### 🎧 Full-Duplex Voice")
                st.caption("Real-time AI conversation — Deepgram + Gemini + ElevenLabs")
                st.info("🎥 Opens a browser page with live webcam + transcription")

                if st.button("🎧 Launch Live Interview", type="primary", use_container_width=True):
                    # Save context
                    cv_text = st.session_state.get("cv_data", {}).get("full_text", "")
                    jd_text = st.session_state.get("jd_data", {}).get("full_text", "")
                    # Collect up to 5 questions from Step 4
                    q_list = []
                    iq = st.session_state.get("interview_questions", {})
                    for section in ("opening", "technical", "behavioural", "closing"):
                        for q in iq.get(section, []):
                            q_list.append(q.get("question", ""))
                            if len(q_list) >= 5:
                                break
                        if len(q_list) >= 5:
                            break
                    from core.livekit.launcher import launch
                    url = launch(resume_text=cv_text, jd_text=jd_text, questions=q_list or None)
                    if url:
                        st.session_state["livekit_url"] = url
                        st.session_state["livekit_launched"] = True
                        add_log("Live Interview: LiveKit session launched")
                        st.rerun()
                    else:
                        st.error("LiveKit server binary not found. Download from https://github.com/livekit/livekit/releases")
            # ── Post-launch status ──
            if st.session_state.get("livekit_launched"):
                st.success(f"✅ Live Interview launched at [{st.session_state['livekit_url']}]({st.session_state['livekit_url']}) — open in your browser")
                col_stop, col_import = st.columns(2)
                with col_stop:
                    if st.button("🛑 Stop LiveKit Session"):
                        from core.livekit.launcher import cleanup
                        cleanup()
                        st.session_state["livekit_launched"] = False
                        st.rerun()
                with col_import:
                    if st.button("📥 Import LiveKit Results"):
                        transcript_dir = Path(tempfile.gettempdir()) / "interviewai_transcripts"
                        files = list(transcript_dir.glob("*.json"))
                        if files:
                            latest = max(files, key=lambda f: f.stat().st_mtime)
                            data = json.loads(latest.read_text())
                            st.session_state["livekit_transcript"] = data
                            st.session_state["live_answers"] = []
                            # Convert conversation to answer format
                            conv = data.get("conversation", [])
                            for i, msg in enumerate(conv):
                                if msg["role"] == "agent":
                                    continue
                                st.session_state["live_answers"].append({
                                    "question": {"question_number": i//2+1, "question": conv[i-1]["text"] if i>0 else "N/A", "skill": "livekit", "difficulty": "medium"},
                                    "answer": msg["text"],
                                    "result": {"score": None, "verdict": "pending", "feedback": "Imported from LiveKit. Use Step 7 to generate report."},
                                })
                            add_log(f"LiveKit transcript imported: {len(conv)} messages")
                            st.rerun()
                        else:
                            st.warning("No transcript found. Complete the LiveKit interview first.")
                if "livekit_transcript" in st.session_state:
                    data = st.session_state["livekit_transcript"]
                    conv = data.get("conversation", [])
                    st.info(f"📄 LiveKit transcript loaded: {len(conv)} messages ({len([m for m in conv if m['role']=='candidate'])} answers)")
                    with st.expander("View Transcript"):
                        for msg in conv:
                            icon = "🤖" if msg["role"] == "agent" else "🧑"
                            st.markdown(f"**{icon} {msg['role'].title()}:** {msg['text']}")
        else:
            loop = st.session_state["interview_loop"]
            result = st.session_state.get("live_current_result")

            col_q, col_eval = st.columns([3, 2])

            with col_q:
                if not loop.is_complete:
                    # Show current question
                    if result is None or st.session_state.get("live_answered", False):
                        q_data = loop.get_next_question()
                        if q_data:
                            st.session_state["live_current_q"] = q_data
                            st.session_state["live_answered"] = False
                            st.session_state["live_current_result"] = None

                            # Show greeting before first question
                            if q_data['question_number'] == 1:
                                greeting_html = """
                                <div style="background:#ebf8ff;border:1px solid #bee3f8;border-radius:10px;padding:12px 18px;margin-bottom:12px;">
                                    <strong>👋 Welcome!</strong> I'll ask you a few questions about your skills.
                                    Type your answer below and click Submit.
                                </div>
                                """
                                st.markdown(greeting_html, unsafe_allow_html=True)

                            st.markdown(f"### Question {q_data['question_number']}")
                            if q_data["is_follow_up"]:
                                st.markdown(f"*Follow-up on: **{q_data['skill']}***")
                            st.markdown(f"**{q_data['question']}**")
                            st.markdown(f"`{q_data['skill']}` · `{q_data['difficulty']}`")

                            # ── Answer input ──
                            answer = st.text_area(
                                "Your Answer",
                                height=120,
                                key=f"live_answer_{q_data['question_number']}",
                                placeholder="Type your answer here...",
                            )

                            if st.button("📤 Submit Answer", type="primary", use_container_width=True):
                                if answer.strip():
                                    eval_result = loop.submit_answer(q_data, answer.strip())
                                    st.session_state["live_current_result"] = eval_result
                                    st.session_state["live_answers"].append({
                                        "question": q_data,
                                        "answer": answer.strip(),
                                        "result": eval_result,
                                    })
                                    st.session_state["live_answered"] = True
                                    add_log(f"Live Q{q_data['question_number']} ({q_data['skill']}): scored {eval_result['score']:.1f} — {eval_result['verdict']}")
                                    st.rerun()
                                else:
                                    st.warning("Please provide an answer before submitting.")
                        else:
                            st.info("No more questions to generate.")
                    else:
                        # Show evaluation result before next question
                        r = st.session_state["live_current_result"]
                        score_color = "🟢" if r["score"] >= 70 else ("🟡" if r["score"] >= 40 else "🔴")
                        st.markdown(f"### {score_color} Score: {r['score']:.1f}/100")
                        st.markdown(f"**Verdict:** `{r['verdict'].upper()}`")
                        st.markdown(f"**Feedback:** {r['feedback']}")

                        with st.expander("Reference Answer"):
                            st.markdown(r.get("reference_answer", "N/A"))

                        if r.get("criterion_scores"):
                            cs = r["criterion_scores"]
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Technical", f"{cs.get('technical_accuracy', 0):.0f}/25")
                            c2.metric("Completeness", f"{cs.get('completeness', 0):.0f}/25")
                            c3.metric("Clarity", f"{cs.get('clarity', 0):.0f}/25")
                            c4.metric("Relevance", f"{cs.get('relevance', 0):.0f}/25")

                        if r["need_follow_up"]:
                            st.info("💡 A follow-up question will be asked for this skill.")

                        if st.button("➡ Next Question", type="primary", use_container_width=True):
                            st.session_state["live_current_result"] = None
                            st.rerun()
                else:
                    st.success("🎉 Adaptive interview complete!")
                    st.balloons()
                    st.markdown("Go to **Step 7: Report** tab to view the full assessment.")

            with col_eval:
                st.markdown("### 📊 Live State")
                state = loop.state
                summary = state.summary()

                total = summary["total"]
                strong = summary["verified_strong"]
                weak = summary["verified_weak"]
                gaps_count = summary["confirmed_gaps"]
                pending = summary["pending"]

                st.metric("Total Skills", total)
                st.metric("Verified Strong", strong)
                st.metric("Needs Work", weak)
                st.metric("Gaps", gaps_count)
                st.metric("Pending", pending)

                st.markdown("---")
                st.markdown("### Skill Progress")
                for skill_name, info in summary["skills"].items():
                    icon = {"verified_strong": "🟢", "verified_weak": "🟡", "confirmed_gap": "🔴", "pending": "⚪", "skipped": "⏭"}.get(info["status"], "⚪")
                    st.markdown(f"{icon} **{skill_name.title()}**: {info['avg_score']:.0f} ({info['questions_asked']}x)")

                if st.button("🔄 Reset Interview"):
                    for key in ["interview_loop", "live_answers", "live_current_result", "live_current_q", "live_answered"]:
                        st.session_state.pop(key, None)
                    st.rerun()

# ─── Tab 6: Report ────────────────────────────────────────────────────────────
with tab6:
    st.markdown("## 📋 Final Assessment Report")
    st.caption("M11-M12: Comprehensive interview report with skill breakdown (generated from Live Interview)")
    st.markdown("---")

    if "interview_loop" not in st.session_state:
        st.info("⏳ Complete a Live Interview session first (Step 5).")
    else:
        loop = st.session_state["interview_loop"]

        if not loop.is_complete:
            st.warning("⚠️ The live interview is not yet complete. Finish all questions in Step 6 first.")
        else:
            if "interview_report" not in st.session_state:
                if st.button("📄 Generate Report", type="primary", use_container_width=True):
                    with st.spinner("Generating report..."):
                        report = generate_report(loop)
                        st.session_state["interview_report"] = report
                        add_log("Report generated successfully")
                    st.rerun()
            else:
                report = st.session_state["interview_report"]

                # ── Top-level Metrics ──
                st.markdown(f"### {report['report_title']}")
                st.caption(f"Generated: {report['generated_at']}")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Overall Score", f"{report['overall_score']}/100")
                col2.metric("Verdict", report['label'])
                col3.metric("Questions Asked", report['total_questions'])
                col4.metric("Skills Evaluated", report['skills_evaluated'])

                st.markdown(f"**Summary:** {report['feedback_summary']}")

                st.markdown("---")

                # ── Strengths & Gaps ──
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.markdown("#### ✅ Strengths")
                    if report["strengths"]:
                        for s in report["strengths"]:
                            st.markdown(f"- {s.title()}")
                    else:
                        st.caption("None identified")
                with s2:
                    st.markdown("#### ⚠️ Needs Development")
                    if report["needs_development"]:
                        for s in report["needs_development"]:
                            st.markdown(f"- {s.title()}")
                    else:
                        st.caption("None")
                with s3:
                    st.markdown("#### 🔴 Gaps")
                    if report["gaps"]:
                        for s in report["gaps"]:
                            st.markdown(f"- {s.title()}")
                    else:
                        st.caption("None")

                st.markdown("---")

                # ── Per-Skill Breakdown ──
                st.markdown("### 📊 Per-Skill Breakdown")
                for item in report["breakdown"]:
                    score = item["avg_score"]
                    color = "🟢" if score >= 70 else ("🟡" if score >= 40 else "🔴")
                    with st.expander(f"{color} {item['skill'].title()} — {score:.1f}/100 ({item['status']})"):
                        st.markdown(f"**Status:** {item['status']}")
                        st.markdown(f"**Best Score:** {item['best_score']:.1f}")
                        st.markdown(f"**Questions Answered:** {item['questions_answered']}")
                        if item["feedback"]:
                            clean_fb = [f for f in item["feedback"] if f]
                            if clean_fb:
                                st.markdown("**Feedback:**")
                                for fb in clean_fb:
                                    st.caption(f"- {fb}")

                st.markdown("---")

                # ── Answer Log ──
                with st.expander("📝 Full Answer Log"):
                    for i, entry in enumerate(report["answer_log"], 1):
                        st.markdown(f"**Q{i}** ({entry['skill']}): {entry['question'][:80]}...")
                        st.caption(f"Score: {entry['score']:.1f} — Verdict: {entry['verdict']}")
                        if st.button(f"Show Answer {i}", key=f"show_ans_{i}"):
                            st.info(entry['answer'])

                if st.button("🔄 Regenerate Report"):
                    st.session_state.pop("interview_report", None)
                    st.rerun()

# ─── Logs Tab ─────────────────────────────────────────────────────────────────
with tab_logs:
    st.markdown("## 📋 System Logs")
    st.caption("Real-time pipeline execution logs for debugging")
    st.markdown("---")

    logs = st.session_state.get("logs", [])

    if logs:
        # Format logs with color coding
        log_lines = []
        for log in logs:
            if "[ERROR]" in log:
                log_lines.append(f'<span class="error">{log}</span>')
            elif "[WARN]" in log:
                log_lines.append(f'<span class="warn">{log}</span>')
            else:
                log_lines.append(log)

        log_html = "<br>".join(log_lines)
        st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

        if st.button("🗑 Clear Logs"):
            st.session_state["logs"] = []
            st.rerun()
    else:
        st.info("No logs yet. Run the pipeline to see execution logs here.")

    st.markdown("---")
    st.markdown("### 🔧 Debug Info")
    debug_col1, debug_col2 = st.columns(2)
    with debug_col1:
        st.markdown("**Session State Keys:**")
        for key in sorted(st.session_state.keys()):
            val = st.session_state[key]
            if isinstance(val, (bytes,)):
                st.markdown(f"- `{key}`: bytes ({len(val)} B)")
            elif isinstance(val, dict):
                st.markdown(f"- `{key}`: dict ({len(val)} keys)")
            elif isinstance(val, list):
                st.markdown(f"- `{key}`: list ({len(val)} items)")
            elif isinstance(val, str) and len(val) > 50:
                st.markdown(f"- `{key}`: str ({len(val)} chars)")
            else:
                st.markdown(f"- `{key}`: `{val}`")
    with debug_col2:
        st.markdown("**API Config:**")
        from core.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_ENDPOINT
        st.markdown(f"- Model: `{GEMINI_MODEL}`")
        st.markdown(f"- Key: `{'***' + GEMINI_API_KEY[-4:] if GEMINI_API_KEY else 'NOT SET'}`")
        st.markdown(f"- Endpoint: `.../{GEMINI_MODEL}:generateContent`")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("InterviewAI v0.1 — CMP7200 Individual Masters Project | Birmingham City University")
