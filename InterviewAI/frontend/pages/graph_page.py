"""Step 3 — Skill Graph Page: Gap analysis and interview topics."""

import streamlit as st
from frontend.components import page_header, metric_row


def render():
    page_header("Step 3: Skill Graph Analysis", "Gap analysis and recommended interview topics (M3)")

    if "graph_data" not in st.session_state:
        st.info("⏳ Run the pipeline first from the main page.")
        return

    gaps = st.session_state["graph_data"]["gaps"]
    topics = st.session_state["graph_data"]["topics"]
    stats = st.session_state["graph_data"]["stats"]

    # ─── Metrics ──────────────────────────────────────────────────────────
    match_pct = gaps["match_percentage"]
    color = "normal" if match_pct >= 60 else "off" if match_pct >= 40 else "inverse"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Match Score", f"{match_pct}%", delta_color=color)
    col2.metric("Graph Nodes", stats["nodes"])
    col3.metric("Candidate Skills", stats["candidate_skills"])
    col4.metric("Job Requirements", stats["job_required"])

    st.markdown("---")

    # ─── Gap Analysis ─────────────────────────────────────────────────────
    st.markdown("### 🔍 Skill Gap Analysis")

    col_match, col_miss = st.columns(2, gap="large")

    with col_match:
        st.markdown("#### ✅ Skills Matched (Required)")
        if gaps["matched_required"]:
            for s in gaps["matched_required"]:
                st.markdown(f"✅ **{s.title()}**")
        else:
            st.warning("No required skills matched.")

        st.markdown("")
        st.markdown("#### 🌟 Bonus Skills Matched")
        if gaps["matched_nice_to_have"]:
            for s in gaps["matched_nice_to_have"]:
                st.markdown(f"🌟 {s.title()}")
        else:
            st.caption("None")

    with col_miss:
        st.markdown("#### ❌ Missing Required Skills")
        if gaps["missing_required"]:
            for s in gaps["missing_required"]:
                st.markdown(f"❌ **{s.title()}**")
        else:
            st.success("No gaps — full match!")

        st.markdown("")
        st.markdown("#### 💡 Extra Skills (not in JD)")
        if gaps["extra_skills"]:
            for s in gaps["extra_skills"][:10]:
                st.markdown(f"💡 {s.title()}")

    st.markdown("---")

    # ─── Interview Topics ─────────────────────────────────────────────────
    st.markdown("### 🎤 Recommended Interview Topics")
    st.caption("These will feed into Module 4 (Question Generator)")

    for i, t in enumerate(topics, 1):
        priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        icon = priority_colors.get(t["priority"], "⚪")

        with st.container():
            c1, c2, c3 = st.columns([2, 4, 2])
            c1.markdown(f"**{icon} {t['skill'].title()}**")
            c2.markdown(f"_{t['reason']}_")
            c3.markdown(f"`{t['priority'].upper()}`")
