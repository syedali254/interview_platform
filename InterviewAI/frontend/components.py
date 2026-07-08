"""Reusable UI components for the frontend."""

import streamlit as st


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


def status_badge(text: str, color: str = "green"):
    colors = {"green": "#38a169", "blue": "#3182ce", "orange": "#dd6b20", "red": "#e53e3e"}
    c = colors.get(color, "#3182ce")
    st.markdown(
        f'<span style="background:{c};color:white;padding:4px 12px;'
        f'border-radius:12px;font-size:0.8rem;font-weight:600;">{text}</span>',
        unsafe_allow_html=True,
    )


def metric_row(metrics: list):
    """Display metrics in columns. metrics = [(label, value), ...]"""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
