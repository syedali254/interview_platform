"""Step 1 — Input Page: Upload CV and enter Job Description."""

import streamlit as st
from frontend.components import page_header


def render():
    page_header("Step 1: Upload Inputs", "Upload your CV and paste the job description")

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
                st.success(f"✅ Uploaded: {uploaded.name}")
        else:
            cv_text = st.text_area(
                "Paste CV text",
                height=300,
                placeholder="Paste the full CV content here...",
                key="cv_text_input",
            )
            if cv_text.strip():
                st.session_state["cv_raw_text"] = cv_text

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
        if jd_text.strip():
            st.session_state["jd_raw_text"] = jd_text

    return _inputs_ready()


def _inputs_ready() -> bool:
    """Check if we have both CV and JD inputs."""
    has_cv = (
        st.session_state.get("cv_file")
        or st.session_state.get("cv_raw_text", "").strip()
    )
    has_jd = st.session_state.get("jd_raw_text", "").strip()
    return bool(has_cv and has_jd)
