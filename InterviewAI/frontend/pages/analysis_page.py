"""Step 2 — Analysis Page: Show parsed CV and JD results."""

import streamlit as st
from frontend.components import page_header, metric_row


def render():
    page_header("Step 2: Analysis Results", "Parsed output from M1 (CV Agent) and M2 (JD Agent)")

    if "cv_data" not in st.session_state or "jd_data" not in st.session_state:
        st.info("⏳ Run the pipeline first from the main page.")
        return

    cv = st.session_state["cv_data"]
    jd = st.session_state["jd_data"]

    # ─── CV Results ───────────────────────────────────────────────────────
    st.markdown("### 📄 Module 1 — CV Parse Results")

    metric_row([
        ("Candidate", cv.get("name", "Unknown")),
        ("Skills Found", len(cv.get("skills", []))),
        ("Experience", len(cv.get("experience", []))),
        ("Projects", len(cv.get("projects", []))),
    ])

    with st.expander("🔍 Skills Extracted", expanded=True):
        skills = cv.get("skills", [])
        # Display as tags
        tags_html = " ".join(
            f'<span style="background:#edf2f7;padding:4px 10px;border-radius:6px;'
            f'margin:2px;display:inline-block;font-size:0.85rem;">{s}</span>'
            for s in skills
        )
        st.markdown(tags_html, unsafe_allow_html=True)

    with st.expander("💼 Experience"):
        for exp in cv.get("experience", []):
            st.markdown(
                f"**{exp.get('title', 'N/A')}** at {exp.get('company', 'N/A')} "
                f"— {exp.get('duration', '')}"
            )
            if exp.get("highlights"):
                st.caption(exp["highlights"] if isinstance(exp["highlights"], str)
                           else ", ".join(exp["highlights"]))

    with st.expander("🎓 Education"):
        for edu in cv.get("education", []):
            st.markdown(f"**{edu.get('degree', '')}** — {edu.get('institution', '')} ({edu.get('year', '')})")

    st.markdown("---")

    # ─── JD Results ───────────────────────────────────────────────────────
    st.markdown("### 💼 Module 2 — Job Description Results")

    metric_row([
        ("Job Title", jd.get("job_title", "N/A")),
        ("Required Skills", len(jd.get("required_skills", []))),
        ("Role Level", jd.get("role_level", "N/A").title()),
        ("Domain", jd.get("domain", "N/A").title()),
    ])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Required Skills:**")
        for s in jd.get("required_skills", []):
            st.markdown(f"- 🔴 {s}")

    with col2:
        st.markdown("**Nice to Have:**")
        for s in jd.get("nice_to_have", []):
            st.markdown(f"- 🟡 {s}")
