from llm_analyzer import analyze_resume
import json
import re
import tempfile
from pathlib import Path
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st
import streamlit.components.v1 as components
import pymupdf
import plotly.graph_objects as go

from llm_analyzer import analyze_resume
from ai_engine.resume_observer import SKILL_DATABASE
from interview_engine import generate_interview_test, evaluate_test, generate_interview_pdf_report
from job_predictor import predict_job_options, JOB_CATALOG
from supabase_client import (
    sign_in_with_email,
    sign_up_with_email,
    send_password_reset,
    sign_out_session,
    get_profile,
    save_resume_analysis,
    list_resume_analyses,
    delete_resume_analysis,
    save_interview_attempt,
    list_interview_attempts,
)


# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Resumind AI — Resume Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==========================================================
# 2. DESIGN SYSTEM
# ==========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300..700;1,9..40,400&family=Outfit:wght@500;600;700;800;900&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #EDEAE2;
    --bg-soft: #F5F2EB;
    --sage: #A7B099;
    --sage-deep: #4A5536;
    --sage-tint: #E5EAD9;
    --ink: #3A2C23;
    --espresso-dark: #2A2019;
    --muted: #73665C;
    --card: #FAF8F4;
    --border: #DCD4C6;
    --terracotta: #9C5F53;
    --terracotta-bg: #F5E8E4;
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--ink) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}

.block-container {
    max-width: 1220px;
    padding-top: 0.75rem;
    padding-bottom: 4rem;
}

header[data-testid="stHeader"] {
    background: transparent !important;
    height: 1.5rem !important;
    min-height: 1.5rem !important;
}

#MainMenu, footer {
    visibility: hidden;
}

/* Brand Mark */
.brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-family: 'Outfit', sans-serif;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--ink) !important;
    white-space: nowrap;
}

.top-brand {
    font-size: 21px;
    padding: 4px 2px;
}

.brand-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: var(--ink);
    color: #F6F3EB !important;
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 18px;
}

.brand span.brand-accent {
    color: var(--sage-deep) !important;
}

/* Sage Hero Surface & Scroll Pop-Up Animations */
@keyframes heroPopIn {
    0% {
        opacity: 0;
        transform: translateY(22px) scale(0.97);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.scroll-pop {
    transition: opacity 0.6s cubic-bezier(0.22, 1, 0.36, 1),
                transform 0.6s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.25s ease,
                border-color 0.25s ease !important;
    will-change: opacity, transform;
}

.scroll-pop-delay-1 {
    transition-delay: 0.07s !important;
}

.scroll-pop-delay-2 {
    transition-delay: 0.14s !important;
}

.scroll-pop.scroll-hidden-bottom {
    opacity: 0 !important;
    transform: translateY(44px) scale(0.93) !important;
}

.scroll-pop.scroll-hidden-top {
    opacity: 0 !important;
    transform: translateY(-36px) scale(0.93) !important;
}

.scroll-pop.scroll-visible {
    opacity: 1 !important;
    transform: translateY(0) scale(1) !important;
}

div[data-testid="stElementContainer"]:has(iframe[height="0"]) {
    display: none !important;
    margin: 0 !important;
    padding: 0 !important;
    height: 0 !important;
}

.pipeline-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 24px 26px;
    margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(58, 44, 35, 0.04);
    transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.25s ease, border-color 0.25s ease;
}

.pipeline-card:hover {
    transform: translateY(-4px) scale(1.01);
    border-color: #9CA58E;
    box-shadow: 0 14px 28px rgba(58, 44, 35, 0.09);
}

.pipeline-step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--sage-deep);
    color: #F6F3EB;
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 0.08em;
    border-radius: 999px;
    padding: 4px 12px;
    margin-bottom: 10px;
}

.pipeline-card h4 {
    font-family: 'Outfit', sans-serif;
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink) !important;
    margin: 4px 0 8px;
}

.pipeline-card p {
    font-size: 13.5px;
    color: var(--muted) !important;
    line-height: 1.65;
    margin: 0;
}

.hero {
    text-align: center;
    background: linear-gradient(155deg, #B2BAA5 0%, #9CA58E 100%);
    border: 1px solid #969F88;
    border-radius: 28px;
    padding: 48px 28px 42px;
    margin: 10px 0 26px;
    box-shadow: 0 10px 30px rgba(58, 44, 35, 0.06);
    animation: heroPopIn 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.hero-tag {
    display: inline-block;
    background: #3A2C23;
    border: 1px solid #2A2019;
    border-radius: 999px;
    padding: 6px 16px;
    color: #F5F2EB !important;
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
}

.hero h1 {
    font-family: 'Outfit', sans-serif;
    font-size: clamp(40px, 6.2vw, 72px);
    line-height: 0.98;
    letter-spacing: -0.04em;
    font-weight: 900;
    color: #F7F4EC !important;
    margin: 20px 0 16px;
}

.hero h1 em {
    color: #2E221A !important;
    font-style: normal;
}

.hero p {
    max-width: 640px;
    margin: auto;
    color: #2E221A !important;
    font-size: 15px;
    font-weight: 500;
    line-height: 1.65;
    opacity: 0.88;
}

.section-heading {
    font-family: 'Outfit', sans-serif;
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
    color: var(--ink) !important;
    margin: 24px 0 12px;
}

.section-tag {
    color: var(--sage-deep);
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .14em;
    text-transform: uppercase;
}

/* Upload Panel Header Styles */
.upload-panel-header {
    margin-bottom: 12px;
}

.panel-badge {
    display: inline-block;
    background: var(--sage-tint);
    color: var(--sage-deep);
    border: 1px solid #C6D0B4;
    border-radius: 999px;
    padding: 3px 11px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .08em;
    margin-bottom: 6px;
}

.upload-panel-header h4 {
    margin: 4px 0 2px 0;
    font-family: 'Outfit', sans-serif;
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink) !important;
}

.panel-desc {
    font-size: 13px;
    color: var(--muted) !important;
    margin: 0 0 8px 0;
    line-height: 1.5;
}

/* File Uploader - Warm Cream & Sage */
div[data-testid="stFileUploader"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 18px !important;
    box-shadow: 0 4px 16px rgba(58, 44, 35, 0.04) !important;
}

div[data-testid="stFileUploader"] label[data-testid="stWidgetLabel"] {
    color: var(--ink) !important;
    font-weight: 600 !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
    background: var(--bg-soft) !important;
    border: 2px dashed #9CA58E !important;
    border-radius: 16px !important;
    padding: 24px 14px !important;
    text-align: center !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
    background: #EFF2E8 !important;
    border-color: var(--sage-deep) !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] svg {
    fill: var(--sage-deep) !important;
    stroke: var(--sage-deep) !important;
    color: var(--sage-deep) !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span,
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small,
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] div,
div[data-testid="stFileUploaderDropzoneInstructions"] * {
    color: var(--ink) !important;
    font-weight: 500 !important;
}

div[data-testid="stFileUploader"] button,
div[data-testid="stFileUploaderDropzone"] button,
section[data-testid="stFileUploaderDropzone"] button {
    background: var(--ink) !important;
    color: #F6F3EB !important;
    -webkit-text-fill-color: #F6F3EB !important;
    border: 1px solid var(--ink) !important;
    border-radius: 999px !important;
    padding: 6px 18px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(58, 44, 35, 0.12) !important;
}

div[data-testid="stFileUploader"] button:hover,
div[data-testid="stFileUploaderDropzone"] button:hover,
section[data-testid="stFileUploaderDropzone"] button:hover {
    background: var(--sage-deep) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border-color: var(--sage-deep) !important;
}

div[data-testid="stFileUploaderFileData"] {
    background: var(--bg-soft) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    margin-top: 10px !important;
}

div[data-testid="stFileUploaderFileData"] * {
    color: var(--ink) !important;
}

div[data-testid="stFileUploaderFileData"] button {
    background: transparent !important;
    border: none !important;
    color: var(--muted) !important;
    -webkit-text-fill-color: var(--muted) !important;
    box-shadow: none !important;
}

div[data-testid="stFileUploaderFileData"] button:hover {
    background: var(--terracotta-bg) !important;
    color: var(--terracotta) !important;
    -webkit-text-fill-color: var(--terracotta) !important;
}

/* Textarea - Warm Alabaster */
div[data-testid="stTextArea"] {
    background: transparent !important;
}

div[data-testid="stTextArea"] label[data-testid="stWidgetLabel"] {
    color: var(--ink) !important;
    font-weight: 600 !important;
}

div[data-baseweb="textarea"],
div[data-baseweb="base-input"] {
    background-color: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 16px rgba(58, 44, 35, 0.03) !important;
}

div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="base-input"]:focus-within {
    border-color: var(--sage-deep) !important;
    box-shadow: 0 0 0 3px rgba(74, 85, 54, 0.16) !important;
}

div[data-baseweb="textarea"] textarea,
div[data-baseweb="base-input"] textarea {
    background-color: var(--card) !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 14px !important;
}

div[data-baseweb="textarea"] textarea::placeholder,
div[data-baseweb="base-input"] textarea::placeholder,
div[data-baseweb="base-input"] input::placeholder {
    color: #9A8F84 !important;
    -webkit-text-fill-color: #9A8F84 !important;
}

/* Text & Password Inputs + Auth Forms + Tabs */
div[data-testid="stTextInput"] label[data-testid="stWidgetLabel"] {
    color: var(--ink) !important;
    font-weight: 600 !important;
}

div[data-baseweb="base-input"] input {
    background-color: var(--card) !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    font-size: 14px !important;
    padding: 11px 14px !important;
}

div[data-testid="stForm"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 22px !important;
    padding: 22px 24px !important;
    box-shadow: 0 6px 22px rgba(58, 44, 35, 0.04) !important;
}

div[data-testid="stTabs"] button[role="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    color: var(--muted) !important;
}

div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--ink) !important;
}

div[data-baseweb="tab-highlight"] {
    background-color: var(--sage-deep) !important;
}

/* Primary, Secondary, Link & Download Buttons - Outfit + Olive & Espresso Pills */
button[kind="primary"],
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #3A2C23 0%, #2A2019 100%) !important;
    color: #F6F3EB !important;
    -webkit-text-fill-color: #F6F3EB !important;
    border: none !important;
    border-radius: 999px !important;
    min-height: 48px !important;
    font-family: 'Outfit', 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
    letter-spacing: .05em !important;
    box-shadow: 0 6px 18px rgba(42, 32, 25, 0.18) !important;
    transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1) !important;
}

button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg, #4A5536 0%, #343D25 100%) !important;
    box-shadow: 0 8px 22px rgba(74, 85, 54, 0.28) !important;
    transform: translateY(-1.5px) !important;
}

button[kind="secondary"],
.stButton > button,
button[data-testid="stBaseButton-secondary"],
.stButton > button[data-testid="stBaseButton-secondary"],
div[data-testid="stLinkButton"] a {
    background: var(--card) !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    border: 1px solid #CFC6B6 !important;
    border-radius: 999px !important;
    min-height: 44px !important;
    font-family: 'Outfit', 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: .04em !important;
    box-shadow: 0 2px 6px rgba(58, 44, 35, 0.04) !important;
    transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1) !important;
}

button[kind="secondary"]:hover,
.stButton > button:hover,
button[data-testid="stBaseButton-secondary"]:hover,
.stButton > button[data-testid="stBaseButton-secondary"]:hover,
div[data-testid="stLinkButton"] a:hover {
    background: var(--ink) !important;
    color: #F6F3EB !important;
    -webkit-text-fill-color: #F6F3EB !important;
    border-color: var(--ink) !important;
    transform: translateY(-1px) !important;
}

/* Top Navigation Header & Isolated Right Pill Dock */
div[data-testid="stHorizontalBlock"]:has(.top-brand) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-top: -4px !important;
    margin-bottom: 14px !important;
    align-items: center !important;
}

div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] {
    background: #F7F4EC !important;
    border: 1px solid #D7D0C1 !important;
    border-radius: 999px !important;
    padding: 6px 8px !important;
    margin: 0 !important;
    align-items: center !important;
    box-shadow: 0 8px 22px rgba(58, 44, 35, 0.06) !important;
    gap: 6px !important;
}

div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button {
    min-height: 38px !important;
    padding: 6px 12px !important;
    white-space: nowrap !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.05em !important;
}

div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button[data-testid="stBaseButton-secondary"],
div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"] {
    background: #EDEAE2 !important;
    color: #3A2C23 !important;
    -webkit-text-fill-color: #3A2C23 !important;
    border: 1px solid #D4CCBA !important;
    box-shadow: none !important;
}

div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button[data-testid="stBaseButton-secondary"]:hover,
div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"]:hover {
    background: #DFE6D3 !important;
    color: #2B3421 !important;
    -webkit-text-fill-color: #2B3421 !important;
    border-color: #939E81 !important;
    box-shadow: 0 4px 12px rgba(74, 85, 54, 0.14) !important;
}

div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button[data-testid="stBaseButton-primary"],
div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4A5536 0%, #2F3820 100%) !important;
    color: #F7F4EC !important;
    -webkit-text-fill-color: #F7F4EC !important;
    border: 1px solid #2F3820 !important;
    box-shadow: 0 5px 14px rgba(47, 56, 32, 0.26) !important;
}

div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button[data-testid="stBaseButton-primary"]:hover,
div[data-testid="stHorizontalBlock"]:has(.top-brand) div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #3A2C23 0%, #2A2019 100%) !important;
    border-color: #2A2019 !important;
}

.stDownloadButton > button,
.stDownloadButton > button[data-testid="stBaseButton-primary"],
.stDownloadButton > button[data-testid="stBaseButton-secondary"] {
    background: linear-gradient(135deg, #3A2C23 0%, #2A2019 100%) !important;
    color: #F6F3EB !important;
    -webkit-text-fill-color: #F6F3EB !important;
    border-radius: 999px !important;
    border: none !important;
    min-height: 48px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: .06em !important;
    box-shadow: 0 6px 18px rgba(42, 32, 25, 0.18) !important;
}

.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #4A5536 0%, #3A4429 100%) !important;
    box-shadow: 0 8px 22px rgba(74, 85, 54, 0.28) !important;
}

/* Containers, Inputs, Segmented Control & Progress */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card) !important;
    border-color: var(--border) !important;
    border-radius: 22px !important;
    box-shadow: 0 4px 16px rgba(58, 44, 35, 0.03) !important;
}

div[data-testid="stProgress"] > div > div > div > div {
    background-color: var(--sage-deep) !important;
}

div[data-baseweb="select"] > div {
    background-color: var(--card) !important;
    border-color: var(--border) !important;
    border-radius: 14px !important;
    color: var(--ink) !important;
}

/* Code and Pre blocks */
code, pre {
    background: var(--bg-soft) !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* Feature and Result Cards */
.feature-card {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 26px !important;
    min-height: 185px;
    margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(58, 44, 35, 0.04) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px rgba(58, 44, 35, 0.08) !important;
}

.feature-card h3 {
    font-family: 'Outfit', sans-serif;
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink) !important;
    margin: 6px 0 10px;
}

.feature-card p {
    font-size: 13.5px;
    color: var(--muted) !important;
    line-height: 1.65;
}

/* Metrics Cards */
div[data-testid="stMetric"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 22px !important;
    padding: 20px !important;
    box-shadow: 0 4px 16px rgba(58, 44, 35, 0.03) !important;
}

div[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: .1em !important;
    text-transform: uppercase !important;
}

div[data-testid="stMetricValue"] {
    color: var(--ink) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    font-size: 30px !important;
}

/* Alerts - Warm Earthy Palette */
div[data-testid="stAlert"] {
    border-radius: 16px !important;
    padding: 14px 18px !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}

div[data-testid="stAlert"] * {
    color: inherit !important;
}

div[data-testid="stAlert"]:has([data-testid="stNotificationContentInfo"]) {
    background: #EFF2E8 !important;
    color: #364125 !important;
    border: 1px solid #C8D2B7 !important;
}

div[data-testid="stAlert"]:has([data-testid="stNotificationContentSuccess"]) {
    background: #E7EFE0 !important;
    color: #2E4722 !important;
    border: 1px solid #BFD1B0 !important;
}

div[data-testid="stAlert"]:has([data-testid="stNotificationContentWarning"]) {
    background: #FBF1DF !important;
    color: #7A4B16 !important;
    border: 1px solid #EBD3A7 !important;
}

div[data-testid="stAlert"]:has([data-testid="stNotificationContentError"]) {
    background: #F8E8E4 !important;
    color: #7E3024 !important;
    border: 1px solid #E3BEB4 !important;
}

/* Expanders */
div[data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 18px !important;
    box-shadow: 0 2px 8px rgba(58, 44, 35, 0.03) !important;
}

div[data-testid="stExpander"] details {
    background: var(--card) !important;
    border-radius: 18px !important;
}

div[data-testid="stExpander"] summary {
    color: var(--ink) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
}

/* Skill Tags */
.skill-tag {
    display: inline-block;
    background: var(--sage-tint);
    color: #374325;
    border: 1px solid #C5CEB4;
    border-radius: 999px;
    padding: 6px 14px;
    margin: 4px;
    font-size: 12px;
    font-weight: 600;
}

.missing-tag {
    display: inline-block;
    background: var(--terracotta-bg);
    color: #7E3B2E;
    border: 1px solid #DFC0B6;
    border-radius: 999px;
    padding: 6px 14px;
    margin: 4px;
    font-size: 12px;
    font-weight: 600;
}

/* Dark Espresso Contrast Banner & Footer */
.espresso-band {
    background: var(--espresso-dark);
    color: #EDEAE2;
    border-radius: 26px;
    padding: 32px 34px;
    margin: 20px 0;
    box-shadow: 0 14px 32px rgba(42, 32, 25, 0.14);
}

.espresso-band-strip {
    border-top: 1px solid rgba(237, 234, 226, 0.15);
    border-bottom: 1px solid rgba(237, 234, 226, 0.15);
    padding: 8px 0;
    margin-bottom: 20px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11px;
    letter-spacing: 0.18em;
    color: #B6ABA0;
    text-transform: uppercase;
    overflow: hidden;
    white-space: nowrap;
}

.footer {
    background: linear-gradient(135deg, #2D3622 0%, #202818 100%);
    border: 1px solid #445234;
    color: #C9D0BF;
    border-radius: 16px;
    padding: 14px 24px;
    margin-top: 38px;
    font-size: 12.5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    box-shadow: 0 8px 20px rgba(32, 40, 24, 0.14);
}

.footer .brand {
    font-size: 16px;
    color: #F6F3EB !important;
}

.footer .brand-badge {
    width: 26px;
    height: 26px;
    font-size: 14px;
    border-radius: 8px;
    background: #A7B099;
    color: #202818 !important;
}

.footer .brand span.brand-accent {
    color: #BCC6AC !important;
}

.footer-meta {
    color: #B8C1AC;
    font-size: 12px;
    letter-spacing: 0.01em;
}
</style>
""", unsafe_allow_html=True)


# ==========================================================
# 3. SESSION STATE
# ==========================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "interview_test" not in st.session_state:
    st.session_state.interview_test = None

if "interview_answers" not in st.session_state:
    st.session_state.interview_answers = {}

if "interview_eval" not in st.session_state:
    st.session_state.interview_eval = None

if "interview_focus_mode" not in st.session_state:
    st.session_state.interview_focus_mode = "Balanced Mock Interview"

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "auth_access_token" not in st.session_state:
    st.session_state.auth_access_token = None

if "auth_refresh_token" not in st.session_state:
    st.session_state.auth_refresh_token = None

if "redirect_after_login" not in st.session_state:
    st.session_state.redirect_after_login = None

if "last_analysis_id" not in st.session_state:
    st.session_state.last_analysis_id = None


# ==========================================================
# 4. PDF TEXT EXTRACTION
# ==========================================================

def extract_pdf_text(uploaded_file):

    pdf_bytes = uploaded_file.getvalue()
    text_parts = []

    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    ) as document:

        for page in document:
            # Sort text in logical reading order
            page_text = page.get_text("text", sort=True)
            if not page_text or len(page_text.strip()) < 15:
                blocks = page.get_text("blocks")
                page_text = "\n".join(b[4] for b in blocks if len(b) > 4 and str(b[4]).strip())
            if page_text.strip():
                text_parts.append(page_text)

    raw_text = "\n".join(text_parts)
    raw_text = raw_text.replace("\xa0", " ").replace("\x00", " ")
    return raw_text.strip()


# ==========================================================
# 5. CANDIDATE INFORMATION
# ==========================================================

def extract_candidate_information(text):

    email_match = re.search(
        r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b',
        text
    )

    phone_match = re.search(
        r'(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4,5}',
        text
    )

    linkedin_match = re.search(
        r'(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[a-zA-Z0-9_\-]+',
        text,
        re.IGNORECASE
    )

    github_match = re.search(
        r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_\-]+',
        text,
        re.IGNORECASE
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    candidate_name = "Candidate"

    excluded_words = [
        "resume", "curriculum vitae", "cv", "email",
        "phone", "mobile", "linkedin", "github",
        "portfolio", "address", "profile", "summary",
        "objective", "education", "experience", "skills",
        "developer", "engineer"
    ]

    for line in lines[:10]:
        clean_line = re.sub(r'^[•*|✦\s\d\.-]+', '', line).strip()
        words = clean_line.split()
        if (
            1 <= len(words) <= 4
            and len(clean_line) <= 45
            and not re.search(r'[@\d:/\\{}<>]', clean_line)
            and not any(word in clean_line.lower() for word in excluded_words)
            and any(c.isalpha() for c in clean_line)
        ):
            candidate_name = clean_line
            break

    phone_str = "Not found"
    if phone_match:
        digits = re.sub(r'\D', '', phone_match.group(0))
        if 10 <= len(digits) <= 13:
            phone_str = phone_match.group(0).strip()

    return {
        "name": candidate_name,
        "email": (
            email_match.group(0)
            if email_match else "Not found"
        ),
        "phone": phone_str,
        "linkedin": linkedin_match.group(0) if linkedin_match else "",
        "github": github_match.group(0) if github_match else ""
    }


# ==========================================================
# 6. JOB DESCRIPTION SKILL EXTRACTION
# ==========================================================

def extract_job_skills(job_description):

    found = []

    for category, skills in SKILL_DATABASE.items():

        for skill in skills:

            pattern = (
                r"(?<![a-zA-Z0-9])"
                + re.escape(skill)
                + r"(?![a-zA-Z0-9])"
            )

            if re.search(
                pattern,
                job_description,
                re.IGNORECASE
            ):
                found.append(skill)

    return list(dict.fromkeys(found))


# ==========================================================
# 7. JOB MATCHING
# ==========================================================

def calculate_job_match(resume_result, job_description):

    resume_skills = []
    for category_skills in resume_result.get("skills", {}).values():
        for skill in category_skills:
            if skill not in resume_skills:
                resume_skills.append(skill)

    # Merge verified skills from trained PyTorch SkillNet
    for pred in resume_result.get("trained_skill_predictions", []):
        if pred.get("predicted_present") and pred.get("skill") not in resume_skills:
            resume_skills.append(pred["skill"])

    required_skills = extract_job_skills(job_description)

    resume_set = {
        skill.lower() for skill in resume_skills
    }

    matched = [
        skill for skill in required_skills
        if skill.lower() in resume_set
    ]

    missing = [
        skill for skill in required_skills
        if skill.lower() not in resume_set
    ]

    if required_skills:

        score = round(
            len(matched) / len(required_skills) * 100,
            2
        )

    else:
        score = None

    return {
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_score": score
    }


# ==========================================================
# 8. PDF REPORT GENERATOR
# ==========================================================

def create_pdf_report(result):

    try:

        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        story = []

        story.append(
            Paragraph(
                "<b>RESUMIND AI</b>",
                styles["Title"]
            )
        )

        story.append(
            Paragraph(
                "Resumind AI - Executive Career & Skills Analysis Report",
                styles["Heading2"]
            )
        )

        story.append(Spacer(1, 18))

        candidate = result["candidate"]
        analysis = result["soura_result"]
        matching = result["match_data"]

        for label, value in [
            ("Candidate", candidate["name"]),
            ("Email", candidate["email"]),
            ("Phone", candidate["phone"]),
            ("Career category", analysis["resume_category"])
        ]:

            story.append(
                Paragraph(
                    f"<b>{label}:</b> {escape(str(value))}",
                    styles["Normal"]
                )
            )

        story.append(Spacer(1, 15))

        if matching["match_score"] is not None:

            story.append(
                Paragraph(
                    f"<b>Job skill overlap:</b> "
                    f"{matching['match_score']:.1f}%",
                    styles["Heading2"]
                )
            )

        def add_section(title, content):

            story.append(
                Paragraph(title, styles["Heading2"])
            )

            if isinstance(content, dict):

                for category, values in content.items():

                    story.append(
                        Paragraph(
                            f"<b>{escape(str(category))}:</b> "
                            f"{escape(', '.join(map(str, values)))}",
                            styles["Normal"]
                        )
                    )

            elif isinstance(content, list):

                for item in content:

                    story.append(
                        Paragraph(
                            escape(str(item)),
                            styles["Normal"]
                        )
                    )

            elif content:

                for line in str(content).splitlines():

                    if line.strip():

                        story.append(
                            Paragraph(
                                escape(line),
                                styles["Normal"]
                            )
                        )

            else:

                story.append(
                    Paragraph(
                        "No information detected.",
                        styles["Normal"]
                    )
                )

            story.append(Spacer(1, 10))

        add_section(
            "Professional Summary",
            analysis["professional_summary"]
        )

        add_section(
            "Education",
            analysis["education"]["section_text"]
        )

        add_section(
            "Work Experience",
            analysis["experience"]["section_text"]
        )

        add_section(
            "Detected Skills",
            analysis["skills"]
        )

        add_section(
            "Projects",
            analysis["projects"]
        )

        add_section(
            "Certifications",
            analysis["certifications"]
        )

        add_section(
            "Achievements",
            analysis["achievements"]
        )

        add_section(
            "Matched Skills",
            matching["matched_skills"]
        )

        add_section(
            "Missing Skills",
            matching["missing_skills"]
        )

        story.append(
            Paragraph(
                "<i>This report contains automated resume observations. "
                "Please verify extracted information.</i>",
                styles["Italic"]
            )
        )

        document.build(story)

        buffer.seek(0)

        return buffer.getvalue()

    except ImportError:
        return None


# ==========================================================
# 9. NAVIGATION & AUTHENTICATION GATE
# ==========================================================

is_logged_in = st.session_state.auth_user is not None


def _navigate_protected(target_page: str):
    if st.session_state.auth_user is not None:
        st.session_state.page = target_page
    else:
        st.session_state.redirect_after_login = target_page
        st.session_state.page = "Login"
    st.rerun()


brand_col, nav_col = st.columns([1.45, 4.55], gap="medium", vertical_alignment="center")

with brand_col:

    st.markdown(
        '<div class="brand top-brand"><span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span></div>',
        unsafe_allow_html=True
    )

with nav_col:

    nav2, nav3, nav4, nav5, nav6 = st.columns([0.75, 0.9, 1.3, 1.4, 1.05], gap="small")

    with nav2:

        if st.button(
            "HOME",
            key="nav_home",
            type="primary" if st.session_state.page == "Home" else "secondary",
            use_container_width=True,
        ):

            st.session_state.page = "Home"
            st.rerun()

    with nav3:

        if st.button(
            "ANALYSER",
            key="nav_analysis",
            type="primary" if st.session_state.page == "Analysis" else "secondary",
            use_container_width=True,
        ):

            _navigate_protected("Analysis")

    with nav4:

        if st.button(
            "CAREER PATHS 🧭",
            key="nav_career",
            type="primary" if st.session_state.page == "CareerPaths" else "secondary",
            use_container_width=True,
        ):

            _navigate_protected("CareerPaths")

    with nav5:

        if st.button(
            "MOCK INTERVIEW 🎯",
            key="nav_interview",
            type="primary" if st.session_state.page == "Interview" else "secondary",
            use_container_width=True,
        ):

            _navigate_protected("Interview")

    with nav6:

        if is_logged_in:
            if st.button(
                "ACCOUNT 👤",
                key="nav_auth",
                type="primary" if st.session_state.page == "Account" else "secondary",
                use_container_width=True,
            ):
                st.session_state.page = "Account"
                st.rerun()
        else:
            if st.button(
                "SIGN IN",
                key="nav_auth",
                type="primary" if st.session_state.page == "Login" else "secondary",
                use_container_width=True,
            ):
                st.session_state.page = "Login"
                st.rerun()


# Enforce authentication for protected studio pages
if st.session_state.page in ("Analysis", "CareerPaths", "Interview", "Account") and not is_logged_in:
    if st.session_state.page != "Account":
        st.session_state.redirect_after_login = st.session_state.page
    st.session_state.page = "Login"
    st.rerun()


# ==========================================================
# 9B. LOGIN & SIGN-UP PAGE
# ==========================================================

if st.session_state.page == "Login":

    st.markdown(
        '<div class="hero scroll-pop">'
        '<span class="hero-tag">✦ SUPABASE AUTHENTICATION</span>'
        '<h1>Welcome to<br><em>Resumind AI</em></h1>'
        '<p>Sign in or create your account to unlock the neural Resume Analyser, Career Paths, Mock Interview Studio, and cloud-saved audit history.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    if st.session_state.redirect_after_login:
        target_labels = {
            "Analysis": "Resume Analyser",
            "CareerPaths": "Career Paths",
            "Interview": "Mock Interview Studio",
        }
        target_label = target_labels.get(st.session_state.redirect_after_login, "the studio")
        st.info(f"🔒 Please sign in or create an account to continue to **{target_label}**.")

    _, auth_center, _ = st.columns([0.85, 2.3, 0.85])

    with auth_center:
        tab_signin, tab_signup, tab_reset = st.tabs(["Sign In", "Create Account", "Reset Password"])

        with tab_signin:
            with st.form("login_form", clear_on_submit=False):
                st.markdown(
                    '<div class="upload-panel-header">'
                    '<span class="panel-badge">MEMBER ACCESS</span>'
                    '<h4>Sign in to your account</h4>'
                    '<p class="panel-desc">Enter your email and password registered with Resumind AI.</p>'
                    '</div>',
                    unsafe_allow_html=True
                )
                login_email = st.text_input("Email Address", placeholder="you@example.com")
                login_password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit_login = st.form_submit_button("SIGN IN →", type="primary", use_container_width=True)

            if submit_login:
                if not login_email.strip() or not login_password:
                    st.error("Please enter both your email address and password.")
                else:
                    with st.spinner("Signing in with Supabase..."):
                        auth_res = sign_in_with_email(login_email, login_password)
                    if auth_res.get("ok"):
                        st.session_state.auth_user = auth_res["user"]
                        st.session_state.auth_access_token = auth_res["access_token"]
                        st.session_state.auth_refresh_token = auth_res["refresh_token"]
                        next_page = st.session_state.redirect_after_login or "Analysis"
                        st.session_state.redirect_after_login = None
                        st.session_state.page = next_page
                        st.rerun()
                    else:
                        st.error(auth_res.get("error", "Sign-in failed."))

        with tab_signup:
            with st.form("signup_form", clear_on_submit=False):
                st.markdown(
                    '<div class="upload-panel-header">'
                    '<span class="panel-badge">NEW ACCOUNT</span>'
                    '<h4>Create your Resumind AI account</h4>'
                    '<p class="panel-desc">Save your resume audits, skill scores, and mock interview attempts securely.</p>'
                    '</div>',
                    unsafe_allow_html=True
                )
                reg_name = st.text_input("Full Name", placeholder="Jane Doe")
                reg_email = st.text_input("Email Address", placeholder="you@example.com", key="reg_email")
                reg_password = st.text_input("Password (min 6 characters)", type="password", placeholder="Create a strong password", key="reg_pw")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_pw2")
                submit_signup = st.form_submit_button("CREATE ACCOUNT →", type="primary", use_container_width=True)

            if submit_signup:
                if not reg_name.strip() or not reg_email.strip() or not reg_password:
                    st.error("Please complete your full name, email address, and password.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Creating your Supabase account..."):
                        signup_res = sign_up_with_email(reg_email, reg_password, reg_name)
                    if signup_res.get("ok"):
                        if signup_res.get("needs_email_confirmation"):
                            st.success(
                                "Account created! Please check your email inbox and click the confirmation link, then sign in under the **Sign In** tab."
                            )
                        else:
                            st.session_state.auth_user = signup_res["user"]
                            st.session_state.auth_access_token = signup_res["access_token"]
                            st.session_state.auth_refresh_token = signup_res["refresh_token"]
                            next_page = st.session_state.redirect_after_login or "Analysis"
                            st.session_state.redirect_after_login = None
                            st.session_state.page = next_page
                            st.rerun()
                    else:
                        st.error(signup_res.get("error", "Could not create account."))

        with tab_reset:
            with st.form("reset_form", clear_on_submit=False):
                st.markdown(
                    '<div class="upload-panel-header">'
                    '<span class="panel-badge">ACCOUNT RECOVERY</span>'
                    '<h4>Reset your password</h4>'
                    '<p class="panel-desc">Receive a password recovery link at your registered email address.</p>'
                    '</div>',
                    unsafe_allow_html=True
                )
                reset_email = st.text_input("Registered Email", placeholder="you@example.com", key="reset_email")
                submit_reset = st.form_submit_button("SEND PASSWORD RESET LINK", type="secondary", use_container_width=True)

            if submit_reset:
                if not reset_email.strip():
                    st.error("Please enter your email address.")
                else:
                    reset_res = send_password_reset(reset_email)
                    if reset_res.get("ok"):
                        st.success("If an account exists for that email, a password reset link has been sent.")
                    else:
                        st.error(reset_res.get("error", "Failed to send reset link."))

    st.markdown(
        '<div class="footer">'
        '<div class="brand"><span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span></div>'
        '<div class="footer-meta">Protected by Supabase Authentication &bull; &copy; 2026 Resumind AI</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ==========================================================
# 9C. ACCOUNT & SAVED HISTORY PAGE
# ==========================================================

if st.session_state.page == "Account" and is_logged_in:

    user_info = st.session_state.auth_user
    profile = get_profile(
        user_info["id"],
        st.session_state.auth_access_token,
        st.session_state.auth_refresh_token,
    )
    display_name = (profile or {}).get("full_name") or user_info.get("full_name") or "Member"
    display_email = (profile or {}).get("email") or user_info.get("email") or ""

    st.markdown(
        f'<div class="hero">'
        f'<span class="hero-tag">✦ MEMBER WORKSPACE</span>'
        f'<h1>{escape(display_name)}</h1>'
        f'<p>{escape(display_email)} &bull; Your resume analyses and mock interview progress are securely synced to Supabase.</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    acc_c1, acc_c2, acc_c3 = st.columns([1, 1, 1])
    with acc_c1:
        if st.button("ANALYSE NEW RESUME →", type="primary", use_container_width=True):
            st.session_state.page = "Analysis"
            st.rerun()
    with acc_c2:
        if st.button("TAKE MOCK INTERVIEW 🎯", type="secondary", use_container_width=True):
            st.session_state.page = "Interview"
            st.rerun()
    with acc_c3:
        if st.button("SIGN OUT", type="secondary", use_container_width=True):
            sign_out_session(
                st.session_state.auth_access_token or "",
                st.session_state.auth_refresh_token or "",
            )
            st.session_state.auth_user = None
            st.session_state.auth_access_token = None
            st.session_state.auth_refresh_token = None
            st.session_state.analysis_result = None
            st.session_state.last_analysis_id = None
            st.session_state.page = "Home"
            st.rerun()

    st.divider()
    st.markdown(
        '<span class="section-tag">SUPABASE DATABASE</span>'
        '<div class="section-heading">Saved Resume Analyses</div>',
        unsafe_allow_html=True
    )

    saved_analyses = list_resume_analyses(
        user_info["id"],
        st.session_state.auth_access_token,
        st.session_state.auth_refresh_token,
    )

    if not saved_analyses:
        st.info("No saved resume analyses yet. Upload a resume in the **ANALYSER** tab to automatically save it here.")
    else:
        for row in saved_analyses:
            with st.container(border=True):
                rc1, rc2 = st.columns([3, 1])
                with rc1:
                    score_txt = f"{row['match_score']}%" if row.get("match_score") is not None else "General Audit"
                    st.markdown(
                        f'<span class="panel-badge">{escape(str(row.get("career_category") or "AUDIT"))}</span> '
                        f'<span class="skill-tag" style="margin:0 4px;">{escape(score_txt)}</span>'
                        f'<h4 style="margin:8px 0 4px; font-family:\'Outfit\', sans-serif; color:#3A2C23;">{escape(str(row.get("file_name", "resume.pdf")))}</h4>'
                        f'<p style="margin:0; font-size:13px; color:#73665C;">Candidate: <b>{escape(str(row.get("candidate_name", "Candidate")))}</b> &bull; Saved: {escape(str(row.get("created_at", ""))[:19].replace("T", " "))}</p>',
                        unsafe_allow_html=True
                    )
                with rc2:
                    if st.button("Open Audit", key=f"load_audit_{row['id']}", type="primary", use_container_width=True):
                        detected_skills = row.get("detected_skills") or {}
                        all_skills = [s for vals in detected_skills.values() for s in vals]
                        matched_skills = row.get("matched_skills") or []
                        missing_skills = row.get("missing_skills") or []
                        st.session_state.analysis_result = {
                            "candidate": {
                                "name": row.get("candidate_name", "Candidate"),
                                "email": row.get("candidate_email", "Not found"),
                                "phone": "Not found",
                                "linkedin": "",
                                "github": "",
                            },
                            "soura_result": {
                                "engine": "Resumind Custom PyTorch AI",
                                "file_name": row.get("file_name", "resume.pdf"),
                                "resume_category": row.get("career_category", "Technical Professional"),
                                "personal_information": {},
                                "professional_summary": "",
                                "career_objective": "",
                                "education": {},
                                "experience": {},
                                "skills": detected_skills,
                                "projects": [],
                                "certifications": [],
                                "achievements": [],
                                "languages": [],
                                "trained_skill_predictions": row.get("neural_predictions") or [],
                                "trained_model_status": "Loaded from Supabase History",
                                "ai_analysis": row.get("ai_analysis", ""),
                            },
                            "match_data": {
                                "resume_skills": all_skills,
                                "required_skills": list(dict.fromkeys(matched_skills + missing_skills)),
                                "matched_skills": matched_skills,
                                "missing_skills": missing_skills,
                                "match_score": row.get("match_score"),
                            },
                            "filename": row.get("file_name", "resume.pdf"),
                            "created_at": str(row.get("created_at", ""))[:19].replace("T", " "),
                        }
                        st.session_state.last_analysis_id = row["id"]
                        st.session_state.page = "Analysis"
                        st.rerun()

                    if st.button("Delete", key=f"del_audit_{row['id']}", type="secondary", use_container_width=True):
                        delete_resume_analysis(
                            row["id"],
                            st.session_state.auth_access_token,
                            st.session_state.auth_refresh_token,
                        )
                        st.rerun()

    st.divider()
    st.markdown(
        '<span class="section-tag">ASSESSMENT RECORDS</span>'
        '<div class="section-heading">Mock Interview History</div>',
        unsafe_allow_html=True
    )

    saved_interviews = list_interview_attempts(
        user_info["id"],
        st.session_state.auth_access_token,
        st.session_state.auth_refresh_token,
    )

    if not saved_interviews:
        st.info("No mock interview attempts saved yet. Complete a test in **MOCK INTERVIEW** to track your readiness over time.")
    else:
        for attempt in saved_interviews:
            with st.container(border=True):
                weak_list = attempt.get("weak_skills") or []
                weak_txt = ", ".join(weak_list) if weak_list else "None — strong across all tested skills"
                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">'
                    f'<div>'
                    f'<span class="panel-badge">{escape(str(attempt.get("readiness_tier", "")))}</span> '
                    f'<span class="skill-tag" style="margin:0 4px;">{escape(str(attempt.get("focus_mode", "")))}</span>'
                    f'<div style="font-family:\'Outfit\', sans-serif; font-weight:700; font-size:17px; color:#3A2C23; margin-top:6px;">'
                    f'Score: {attempt.get("score_pct", 0)}% ({attempt.get("correct_count", 0)}/{attempt.get("total_questions", 0)} correct)</div>'
                    f'<div style="font-size:12.5px; color:#73665C; margin-top:2px;">Revision Topics: {escape(weak_txt)}</div>'
                    f'</div>'
                    f'<div style="font-size:12px; color:#73665C;">{escape(str(attempt.get("created_at", ""))[:19].replace("T", " "))}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    st.markdown(
        '<div class="footer">'
        '<div class="brand"><span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span></div>'
        '<div class="footer-meta">Synced with Supabase Cloud &bull; &copy; 2026 Resumind AI</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ==========================================================
# 10. HOMEPAGE
# ==========================================================

if st.session_state.page == "Home":

    st.markdown(
        '<div class="hero scroll-pop">'
        '<span class="hero-tag">✦ RESUMIND AI ENGINE</span>'
        '<h1>A sharper resume.<br><em>Your next defining role.</em></h1>'
        '<p>Analyse your professional experience, discover your strengths and understand how your qualifications align with your next career opportunity. Supporting IT and non-IT resume analysis.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    center1, center2, center3 = st.columns([1, 1.5, 1])

    with center2:

        if st.button(
            "ANALYSE MY RESUME →",
            type="primary",
            use_container_width=True
        ):

            _navigate_protected("Analysis")

    st.markdown(
        '<div class="scroll-pop" style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:16px; margin:32px 0 18px;">'
        '<div><span class="section-tag">CAPABILITIES COLLECTION</span>'
        '<div class="section-heading" style="margin:6px 0 0;">Simplifying career<br>intelligence with clarity</div></div>'
        '<p style="max-width:450px; color:#73665C; font-size:14px; line-height:1.65; margin:0;">'
        'We evaluate more than keywords. Resumind AI parses your full PDF layout, runs custom PyTorch neural networks, audits ATS compatibility, and maps your clearest next career step.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    cards = [
        (
            "01",
            "Resume Observation",
            "Layout-aware PDF extraction captures contact details, summaries, education, employment timelines, projects, certifications, and languages."
        ),
        (
            "02",
            "Industry Recognition",
            "Scans across 14 IT, non-IT, and hybrid professional domains—from Software & AI to Finance, Marketing, HR, Healthcare, and Operations."
        ),
        (
            "03",
            "Job Compatibility",
            "Benchmarks your detected competencies against any target job description to surface matched skills, critical gaps, and overlap percentages."
        ),
        (
            "04",
            "Neural SkillNet & MatchNet",
            "Dual custom PyTorch neural models predict verified skill confidence and semantic resume-to-job compatibility scores 100% locally."
        ),
        (
            "05",
            "Resume Diagnostics",
            "Highlights missing resume sections, ATS parseability checks, quantified achievement opportunities, and tailored improvement suggestions."
        ),
        (
            "06",
            "Executive Reporting",
            "Generates a formal, downloadable ReportLab PDF career audit report plus role recommendations and skill-calibrated mock interviews."
        )
    ]

    for index, (number, title, description) in enumerate(cards):

        delay_cls = f"scroll-pop-delay-{index % 3}" if index % 3 in (1, 2) else ""
        with [c1, c2, c3][index % 3]:

            st.markdown(
                f'<div class="feature-card scroll-pop {delay_cls}">'
                f'<span class="section-tag">MODULE {number}</span>'
                f'<h3>{title}</h3>'
                f'<p>{description}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown(
        '<div class="scroll-pop" style="margin:34px 0 16px;">'
        '<span class="section-tag">INSIDE THE RESUME AUDIT</span>'
        '<div class="section-heading" style="margin:6px 0 6px;">How Resumind Analyses Your Resume</div>'
        '<p style="max-width:660px; color:#73665C; font-size:14px; line-height:1.65; margin:0;">'
        'Every uploaded resume passes through a structured four-stage intelligence pipeline designed for precision, readability, and actionable career guidance.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    p1, p2 = st.columns(2, gap="medium")

    pipeline_steps = [
        (
            "STAGE 01 • PARSE",
            "Structured PDF & Section Decoding",
            "PyMuPDF reads multi-column and single-column resumes in logical reading order, isolating headings, dates, qualifications, projects, and contact links without external API calls."
        ),
        (
            "STAGE 02 • CLASSIFY",
            "PyTorch Neural Skill Inference",
            "Resumind SkillNet evaluates TF-IDF n-gram signals alongside our curated skill dictionary to assign confidence scores to every recognized competency."
        ),
        (
            "STAGE 03 • AUDIT",
            "ATS Calibration & Gap Detection",
            "ResumindMatchNet and our deterministic matcher blend semantic similarity with exact requirement overlap to calculate suitability scores and pinpoint missing target skills."
        ),
        (
            "STAGE 04 • LAUNCH",
            "Career Radar & Mock Interview Prep",
            "Automatically ranks your highest-fit job roles with direct apply links, builds customized MCQ mock interviews from your resume skills, and exports a clean PDF audit."
        )
    ]

    for idx, (badge, heading, body) in enumerate(pipeline_steps):
        delay_cls = "scroll-pop-delay-1" if idx % 2 == 1 else ""
        with [p1, p2][idx % 2]:
            st.markdown(
                f'<div class="pipeline-card scroll-pop {delay_cls}">'
                f'<span class="pipeline-step-num">{badge}</span>'
                f'<h4>{heading}</h4>'
                f'<p>{body}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown(
        '<div class="footer scroll-pop">'
        '<div class="brand"><span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span></div>'
        '<div class="footer-meta">Your Resume. Your Skills. Your Next Opportunity. &bull; &copy; 2026 Resumind AI</div>'
        '</div>',
        unsafe_allow_html=True
    )

    components.html(
        """
        <script>
        (function() {
            const parentWin = window.parent;
            const doc = parentWin.document;
            let ticking = false;

            function updateScrollPop() {
                ticking = false;
                const h = parentWin.innerHeight || doc.documentElement.clientHeight || 800;
                const els = doc.querySelectorAll('.scroll-pop');
                els.forEach((el) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.top < h * 0.92 && rect.bottom > h * 0.06) {
                        el.classList.remove('scroll-hidden-bottom', 'scroll-hidden-top');
                        el.classList.add('scroll-visible');
                    } else if (rect.top >= h - 8) {
                        el.classList.remove('scroll-visible', 'scroll-hidden-top');
                        el.classList.add('scroll-hidden-bottom');
                    } else if (rect.bottom <= 8) {
                        el.classList.remove('scroll-visible', 'scroll-hidden-bottom');
                        el.classList.add('scroll-hidden-top');
                    }
                });
            }

            function onScrollOrResize() {
                if (!ticking) {
                    ticking = true;
                    parentWin.requestAnimationFrame(updateScrollPop);
                }
            }

            function bindScrollPop() {
                updateScrollPop();

                if ('IntersectionObserver' in parentWin) {
                    if (parentWin.__resumindIO) {
                        parentWin.__resumindIO.disconnect();
                    }
                    const io = new parentWin.IntersectionObserver(() => {
                        onScrollOrResize();
                    }, { root: null, threshold: [0, 0.08, 0.25, 0.5] });
                    doc.querySelectorAll('.scroll-pop').forEach((el) => io.observe(el));
                    parentWin.__resumindIO = io;
                }

                if (parentWin.__resumindScrollHandler) {
                    doc.removeEventListener('scroll', parentWin.__resumindScrollHandler, { capture: true });
                    parentWin.removeEventListener('scroll', parentWin.__resumindScrollHandler);
                    parentWin.removeEventListener('resize', parentWin.__resumindScrollHandler);
                }
                parentWin.__resumindScrollHandler = onScrollOrResize;
                doc.addEventListener('scroll', onScrollOrResize, { passive: true, capture: true });
                parentWin.addEventListener('scroll', onScrollOrResize, { passive: true });
                parentWin.addEventListener('resize', onScrollOrResize, { passive: true });
            }

            setTimeout(bindScrollPop, 50);
            setTimeout(bindScrollPop, 250);
            setTimeout(updateScrollPop, 600);
        })();
        </script>
        """,
        height=0,
    )


# ==========================================================
# 11. ANALYSIS PAGE
# ==========================================================

if st.session_state.page == "Analysis":

    st.markdown(
        '<div class="hero">'
        '<span class="hero-tag">RESUME EVALUATION STUDIO</span>'
        '<h1>Resume Analysis<br><em>Studio</em></h1>'
        '<p>Upload your PDF resume. Resumind AI will inspect your professional background, identify skills and organise your career information.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    input1, input2 = st.columns([1, 1], gap="medium")

    with input1:

        st.markdown(
            '<div class="upload-panel-header">'
            '<span class="panel-badge">STEP 1</span>'
            '<h4>Upload PDF Resume</h4>'
            '<p class="panel-desc">Select or drop your text-based PDF resume (supports IT & non-IT).</p>'
            '</div>',
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Upload Resume PDF",
            type=["pdf"],
            help="Upload a text-based PDF resume.",
            label_visibility="collapsed"
        )

        if uploaded_file:

            st.success(
                f"✓ Resume loaded: {uploaded_file.name} ({len(uploaded_file.getvalue()) / 1024:.1f} KB)"
            )

    with input2:

        st.markdown(
            '<div class="upload-panel-header">'
            '<span class="panel-badge">STEP 2</span>'
            '<h4>Target Job Description <span style="font-weight:400; color:#73665C; font-size:12px;">(Optional)</span></h4>'
            '<p class="panel-desc">Paste job requirements to run ATS skill matching and gap analysis.</p>'
            '</div>',
            unsafe_allow_html=True
        )

        job_description = st.text_area(
            "Target Job Description (Optional)",
            placeholder=(
                "Paste the job description here if you "
                "want a resume-to-job comparison, ATS score & keyword match..."
            ),
            height=180,
            label_visibility="collapsed"
        )

    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

    analyse_button = st.button(
        "ANALYSE RESUME →",
        type="primary",
        use_container_width=True
    )

    if analyse_button:

        st.session_state.analysis_result = None

        if uploaded_file is None:

            st.error("Please upload a resume PDF.")

        else:

            try:

                with st.spinner(
                    "Resumind AI is analysing your resume..."
                ):

                    # Extract text for candidate information
                    resume_text = extract_pdf_text(uploaded_file)

                    if not resume_text:

                        raise ValueError(
                            "No readable text found in this PDF. "
                            "Scanned PDFs require OCR."
                        )

                    candidate = extract_candidate_information(
                        resume_text
                    )

                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(
                        suffix=".pdf",
                        delete=False
                    ) as temp_file:

                        temp_file.write(
                            uploaded_file.getvalue()
                        )

                        temp_pdf_path = Path(temp_file.name)

                    try:

                        # Run Resumind AI Engine
                        soura_result = analyze_resume(
                            temp_pdf_path,
                            job_description
                        )

                    finally:

                        temp_pdf_path.unlink(
                            missing_ok=True
                        )

                    # Sync candidate details into personal_information
                    if candidate and isinstance(candidate, dict):
                        if not soura_result.get("personal_information"):
                            soura_result["personal_information"] = candidate
                        else:
                            for k, v in candidate.items():
                                curr_v = soura_result["personal_information"].get(k)
                                if v and (not curr_v or curr_v in ("Candidate", "Not found", [])):
                                    soura_result["personal_information"][k] = v

                    # Optional job matching
                    if job_description.strip():

                        match_data = calculate_job_match(
                            soura_result,
                            job_description
                        )

                    else:

                        all_skills = [
                            skill
                            for values in soura_result.get("skills", {}).values()
                            for skill in values
                        ]
                        for pred in soura_result.get("trained_skill_predictions", []):
                            if pred.get("predicted_present") and pred.get("skill") not in all_skills:
                                all_skills.append(pred["skill"])

                        match_data = {
                            "resume_skills": all_skills,
                            "required_skills": [],
                            "matched_skills": [],
                            "missing_skills": [],
                            "match_score": None
                        }

                    # Save result
                    st.session_state.analysis_result = {
                        "candidate": candidate,
                        "soura_result": soura_result,
                        "match_data": match_data,
                        "filename": uploaded_file.name,
                        "created_at": datetime.now().strftime(
                            "%d %b %Y, %I:%M %p"
                        )
                    }

                    if st.session_state.auth_user is not None:
                        saved_id = save_resume_analysis(
                            user_id=st.session_state.auth_user["id"],
                            access_token=st.session_state.auth_access_token,
                            refresh_token=st.session_state.auth_refresh_token,
                            file_name=uploaded_file.name,
                            candidate=candidate,
                            soura_result=soura_result,
                            match_data=match_data,
                            job_description=job_description,
                        )
                        st.session_state.last_analysis_id = saved_id

                st.success(
                    "Resumind AI analysis completed and saved to your account!"
                    if st.session_state.get("last_analysis_id")
                    else "Resumind AI analysis completed!"
                )

            except Exception as error:

                st.error(
                    f"Analysis failed: {type(error).__name__}: {error}"
                )

                st.exception(error)


# ==========================================================
# 12. ANALYSIS DASHBOARD
# ==========================================================

result = st.session_state.analysis_result

if (
    st.session_state.page == "Analysis"
    and result is not None
):

    candidate = result["candidate"]
    data = result["soura_result"]
    match = result["match_data"]

    st.divider()

    st.markdown(
        '<span class="section-tag">CAREER AUDIT</span>'
        '<div class="section-heading">Candidate Profile</div>',
        unsafe_allow_html=True
    )

    p1, p2, p3 = st.columns(3)

    with p1:
        st.metric("Candidate", candidate["name"])

    with p2:
        st.metric("Email", candidate["email"])

    with p3:
        st.metric("Phone", candidate["phone"])

    st.caption(
        f"File: {result['filename']} | "
        f"Analysed: {result['created_at']}"
    )

    st.markdown(
        f"**Career category:** {data['resume_category']}"
    )

    st.caption(
        f"Analysis engine: {data['engine']} | "
        f"Model status: {data.get('trained_model_status', 'Not available')}"
    )

    # ------------------------------------------------------
    # JOB PREDICTION & CAREER PATH RECOMMENDATIONS
    # ------------------------------------------------------

    st.divider()

    st.markdown(
        '<span class="section-tag">AI CAREER RADAR</span>'
        '<div class="section-heading">Top Predicted Job Roles & Career Paths</div>',
        unsafe_allow_html=True
    )
    st.caption("Resumind AI evaluated your detected competencies against market roles to identify your highest-conviction career options, personalized fit reasons, and direct application links.")

    # Collect all candidate skills
    candidate_skills_for_pred = list(match.get("resume_skills") or [])
    if not candidate_skills_for_pred and data.get("skills"):
        for slist in data["skills"].values():
            candidate_skills_for_pred.extend(slist)
    for p in data.get("trained_skill_predictions", []):
        if p.get("predicted_present") and p.get("skill") not in candidate_skills_for_pred:
            candidate_skills_for_pred.append(p["skill"])

    predicted_roles = predict_job_options(
        candidate_skills=candidate_skills_for_pred,
        resume_category=data.get("resume_category"),
        top_n=3
    )

    if predicted_roles:
        for role_idx, role in enumerate(predicted_roles):
            with st.container(border=True):
                # Header row
                rc1, rc2 = st.columns([3, 1])
                with rc1:
                    st.markdown(
                        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
                        f'<span class="panel-badge">RECOMMENDED OPTION #{role_idx+1}</span>'
                        f'<span style="font-size:11px; font-weight:600; color:#5A4D43; background:#EDEAE2; border-radius:20px; padding:2px 8px;">{escape(role["category"])}</span>'
                        f'</div>'
                        f'<h3 style="margin:2px 0 6px 0; color:#3A2C23; font-family:\'Outfit\', sans-serif; font-size:21px; font-weight:700;">'
                        f'{escape(role["title"])}</h3>',
                        unsafe_allow_html=True
                    )
                with rc2:
                    st.markdown(
                        f'<div style="text-align:right;">'
                        f'<div style="font-family:\'Outfit\', sans-serif; font-size:28px; font-weight:800; color:{role["suitability_color"]};">'
                        f'{role["fit_score"]}%</div>'
                        f'<span style="display:inline-block; font-size:11px; font-weight:700; color:{role["suitability_color"]}; background:{role["suitability_bg"]}; padding:3px 10px; border-radius:20px;">'
                        f'{role["suitability_label"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                st.markdown(f'<p style="color:#73665C; font-size:13px; margin:0 0 10px 0;">{escape(role["description"])}</p>', unsafe_allow_html=True)

                # Custom Justification / Reason
                st.markdown(
                    f'<div style="background:#F5F2EB; border-left:3px solid {role["suitability_color"]}; padding:10px 14px; border-radius:10px; margin-bottom:12px;">'
                    f'<div style="font-size:11px; font-weight:700; color:{role["suitability_color"]}; letter-spacing:.05em; text-transform:uppercase; margin-bottom:3px;">💡 Why this is a suitable fit:</div>'
                    f'<div style="font-size:13px; color:#3A2C23; line-height:1.5;">{role["reasoning"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # Skills comparison
                sc1, sc2 = st.columns(2)
                with sc1:
                    st.markdown("**✓ Demonstrated Skills:**")
                    if role["matched_skills"]:
                        st.markdown("".join(f'<span class="skill-tag">✓ {escape(s)}</span>' for s in role["matched_skills"]), unsafe_allow_html=True)
                    else:
                        st.caption("Foundational overlap")
                with sc2:
                    st.markdown("**✦ Skills to Pick Up (Close the Gap):**")
                    if role["skills_to_learn"]:
                        st.markdown("".join(f'<span class="missing-tag">+ {escape(s)}</span>' for s in role["skills_to_learn"]), unsafe_allow_html=True)
                    else:
                        st.caption("You meet all core skill requirements!")

                # Meta specs
                st.markdown(
                    f'<div style="font-size:12px; color:#73665C; margin-top:10px; border-top:1px solid #DCD4C6; padding-top:8px;">'
                    f'<b>Compensation:</b> {escape(role["salary_range"])} &nbsp;|&nbsp; '
                    f'<b>Market Demand:</b> {escape(role["market_demand"])} &nbsp;|&nbsp; '
                    f'<b>Career Path:</b> {escape(role["growth_path"])}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # Action Links
                act1, act2, act3, act4 = st.columns([1, 1, 1, 1.3])
                with act1:
                    st.link_button("LinkedIn Jobs ↗", role["links"]["linkedin"], use_container_width=True)
                with act2:
                    st.link_button("Indeed Jobs ↗", role["links"]["indeed"], use_container_width=True)
                with act3:
                    st.link_button("Glassdoor ↗", role["links"]["glassdoor"], use_container_width=True)
                with act4:
                    if st.button("Practice Mock Test 🎯", key=f"btn_role_test_{role['id']}", type="secondary", use_container_width=True):
                        st.session_state.interview_test = generate_interview_test(
                            candidate_skills=role["matched_skills"] or candidate_skills_for_pred,
                            resume_category=role["category"],
                            num_questions=5,
                            focus_mode="Balanced Mock Interview"
                        )
                        st.session_state.interview_answers = {}
                        st.session_state.interview_eval = None
                        st.session_state.page = "Interview"
                        st.rerun()

    # ------------------------------------------------------
    # JOB MATCHING
    # ------------------------------------------------------

    st.divider()

    st.markdown(
        '<span class="section-tag">JOB COMPATIBILITY</span>'
        '<div class="section-heading">Skills Match Analysis</div>',
        unsafe_allow_html=True
    )

    if match["match_score"] is not None:

        score1, score2, score3 = st.columns(3)

        with score1:

            st.metric(
                "Skill Overlap",
                f"{match['match_score']:.1f}%"
            )

        with score2:

            st.metric(
                "Matched Skills",
                len(match["matched_skills"])
            )

        with score3:

            st.metric(
                "Missing Skills",
                len(match["missing_skills"])
            )

        st.progress(
            min(100, max(0, int(round(float(match["match_score"]))))),
            text="Percentage of recognised job skills found in the resume"
        )

        st.caption(
            "This is a keyword-based skill overlap measure, "
            "not a validated hiring probability or ATS score."
        )

    else:

        info_c1, info_c2 = st.columns([2.5, 1])
        with info_c1:
            st.info(
                "💡 **No Target Job Description Provided** — General resume analysis and neural skill predictions are displayed below. "
                "Paste a job description in the analysis studio to calculate real-time match percentage, keyword gaps, and ATS alignment."
            )
        with info_c2:
            st.metric("Target Job Status", "Awaiting Job Desc")

    # ------------------------------------------------------
    # MATCHED AND MISSING SKILLS
    # ------------------------------------------------------

    if match["required_skills"]:

        s1, s2 = st.columns(2)

        with s1:

            st.markdown("### Matched Skills")

            if match["matched_skills"]:

                tags = "".join(
                    f'<span class="skill-tag">✓ {escape(str(skill))}</span>'
                    for skill in match["matched_skills"]
                )

                st.markdown(tags, unsafe_allow_html=True)

            else:

                st.info("No matching skills identified.")

        with s2:

            st.markdown("### Missing Skills")

            if match["missing_skills"]:

                tags = "".join(
                    f'<span class="missing-tag">✕ {escape(str(skill))}</span>'
                    for skill in match["missing_skills"]
                )

                st.markdown(tags, unsafe_allow_html=True)

            else:

                st.success("All recognised job skills were found.")

        # Skill chart
        chart = go.Figure()

        chart.add_trace(
            go.Bar(
                name="Matched",
                x=["Job Skills"],
                y=[len(match["matched_skills"])],
                marker_color="#4A5536"
            )
        )

        chart.add_trace(
            go.Bar(
                name="Missing",
                x=["Job Skills"],
                y=[len(match["missing_skills"])],
                marker_color="#9C5F53"
            )
        )

        chart.update_layout(
            barmode="group",
            paper_bgcolor="#FAF8F4",
            plot_bgcolor="#EDEAE2",
            font=dict(color="#3A2C23", family="DM Sans"),
            height=330,
            yaxis_title="Number of skills",
            margin=dict(l=25, r=25, t=30, b=30)
        )

        st.plotly_chart(
            chart,
            use_container_width=True
        )

    else:

        cat_counts = {
            cat: len(s_list)
            for cat, s_list in data.get("skills", {}).items()
            if s_list
        }

        if cat_counts:

            st.markdown("### Profile Skill Domain Breakdown")

            chart = go.Figure()

            chart.add_trace(
                go.Bar(
                    x=list(cat_counts.keys()),
                    y=list(cat_counts.values()),
                    marker_color="#4A5536"
                )
            )

            chart.update_layout(
                paper_bgcolor="#FAF8F4",
                plot_bgcolor="#EDEAE2",
                font=dict(color="#3A2C23", family="DM Sans"),
                height=300,
                yaxis_title="Skills Count",
                margin=dict(l=25, r=25, t=30, b=30)
            )

            st.plotly_chart(
                chart,
                use_container_width=True
            )

        if match.get("resume_skills"):

            st.markdown("### Profile Verified Skills")

            tags = "".join(
                f'<span class="skill-tag">✓ {escape(str(skill))}</span>'
                for skill in match["resume_skills"]
            )

            st.markdown(tags, unsafe_allow_html=True)

    # ------------------------------------------------------
    # SKILLS BY CATEGORY
    # ------------------------------------------------------

    st.divider()

    st.markdown(
        '<span class="section-tag">COMPETENCY TAXONOMY</span>'
        '<div class="section-heading">Detected Skills</div>',
        unsafe_allow_html=True
    )

    if data["skills"]:

        for category, skills in data["skills"].items():

            with st.expander(
                f"{category} — {len(skills)} skills",
                expanded=True
            ):

                tags = "".join(
                    f'<span class="skill-tag">{escape(str(skill))}</span>'
                    for skill in skills
                )

                st.markdown(
                    tags,
                    unsafe_allow_html=True
                )

    else:

        st.warning(
            "No recognised skills found. "
            "The resume may use skills outside the current dictionary."
        )

    # ------------------------------------------------------
    # COMPLETE RESUMIND AI ANALYSIS REPORT
    # ------------------------------------------------------

    ai_report = data.get("ai_analysis")
    if ai_report:

        st.divider()

        st.markdown(
            '<span class="section-tag">EXECUTIVE INTELLIGENCE</span>'
            '<div class="section-heading">Complete Resumind AI Analysis</div>',
            unsafe_allow_html=True
        )

        st.markdown(ai_report)

    # ------------------------------------------------------
    # PROFESSIONAL SUMMARY & OBJECTIVE
    # ------------------------------------------------------

    summary_text = (data.get("professional_summary") or "").strip()
    objective_text = (data.get("career_objective") or "").strip()

    if summary_text or objective_text:

        st.divider()

        if summary_text:
            st.markdown("### Professional Summary")
            st.write(summary_text)

        if objective_text and objective_text != summary_text:
            st.markdown("### Career Objective")
            st.write(objective_text)

    # ------------------------------------------------------
    # EDUCATION
    # ------------------------------------------------------

    st.divider()

    st.markdown("### Education")

    education = data.get("education") or {}
    sec_text = education.get("section_text", "") if isinstance(education, dict) else str(education)
    quals = education.get("possible_qualifications", []) if isinstance(education, dict) else []

    st.write(
        sec_text or "No education section detected."
    )

    if quals:

        st.markdown("**Possible qualifications detected:**")

        for qualification in quals:
            st.write(f"• {qualification}")

    # ------------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------------

    st.divider()

    st.markdown("### Work Experience")

    experience = data.get("experience") or {}
    exp_text = experience.get("section_text", "") if isinstance(experience, dict) else str(experience)
    exp_years = experience.get("years_of_experience_mentioned") if isinstance(experience, dict) else None

    st.write(
        exp_text or "No experience section detected."
    )

    if exp_years is not None:

        st.metric(
            "Experience mentioned",
            f"{exp_years} years"
        )

    # ------------------------------------------------------
    # PROJECTS AND CERTIFICATIONS
    # ------------------------------------------------------

    st.divider()

    pc1, pc2 = st.columns(2)

    with pc1:

        st.markdown("### Projects")

        st.write(
            data["projects"]
            or "No projects detected."
        )

    with pc2:

        st.markdown("### Certifications")

        st.write(
            data["certifications"]
            or "No certifications detected."
        )

    # ------------------------------------------------------
    # ACHIEVEMENTS AND LANGUAGES
    # ------------------------------------------------------

    ac1, ac2 = st.columns(2)

    with ac1:

        st.markdown("### Achievements")

        st.write(
            data["achievements"]
            or "No achievements detected."
        )

    with ac2:

        st.markdown("### Languages")

        st.write(
            data["languages"]
            or "No language section detected."
        )

    # ------------------------------------------------------
    # TRAINED MODEL PREDICTIONS
    # ------------------------------------------------------

    if data.get("trained_skill_predictions"):

        st.divider()

        st.markdown("### ✦ Resumind Neural Network Predictions")

        st.caption(
            "Predictions from your custom PyTorch SkillNet trained on your RTX 2050 GPU."
        )

        st.dataframe(
            data["trained_skill_predictions"],
            width="stretch",
            hide_index=True
        )

    elif data.get("trained_model_warning"):

        st.warning(
            "The trained model could not run: "
            + data["trained_model_warning"]
        )

    else:

        st.info(
            "Custom PyTorch SkillNet model is not trained yet. "
            "Run 'python build_model.py' to train it."
        )

    # ------------------------------------------------------
    # MOCK INTERVIEW CALLOUT
    # ------------------------------------------------------

    st.divider()

    st.markdown(
        '<div class="espresso-band">'
        '<div class="espresso-band-strip">'
        'CAREER READINESS // AI MOCK INTERVIEW STUDIO // SKILL CALIBRATION // RESUMIND INTELLIGENCE'
        '</div>'
        '<span style="display:inline-block; background:#A7B099; color:#2A2019; '
        'border-radius:999px; padding:4px 14px; font-size:11px; font-weight:700; '
        'letter-spacing:.08em; margin-bottom:12px;">✦ NEXT STEP: INTERVIEW PREPARATION</span>'
        '<h3 style="margin:4px 0 8px 0; color:#F7F4EC; font-family:\'Outfit\', sans-serif; font-size:24px; font-weight:800; letter-spacing:-0.02em;">'
        'Test Your Knowledge with an AI Mock Interview</h3>'
        '<p style="margin:0; color:#D5CCC2; font-size:14px; line-height:1.65; max-width:740px;">'
        'Take an interactive test calibrated directly to your resume\'s detected skills '
        'and career category. Practice technical questions, review scenario challenges, '
        'and get instant readiness feedback with interviewer insights.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button("START MOCK INTERVIEW TEST BASED ON THIS RESUME →", type="primary", key="btn_start_interview_from_resume", use_container_width=True):
        candidate_skills = list(match.get("resume_skills") or [])
        if not candidate_skills and data.get("skills"):
            for s_list in data["skills"].values():
                candidate_skills.extend(s_list)
        st.session_state.interview_test = generate_interview_test(
            candidate_skills=candidate_skills,
            resume_category=data.get("resume_category"),
            num_questions=5,
            focus_mode="Balanced Mock Interview"
        )
        st.session_state.interview_answers = {}
        st.session_state.interview_eval = None
        st.session_state.page = "Interview"
        st.rerun()

    # ------------------------------------------------------
    # DOWNLOAD REPORTS
    # ------------------------------------------------------

    st.divider()

    st.markdown("### Export Your Report")

    pdf_bytes = create_pdf_report(result)

    if pdf_bytes:

        st.download_button(
            "DOWNLOAD PDF REPORT",
            data=pdf_bytes,
            file_name="Resumind_AI_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    else:

        st.warning(
            "Install reportlab to enable PDF reports."
        )

    # ------------------------------------------------------
    # NEW ANALYSIS
    # ------------------------------------------------------

    st.divider()

    if st.button(
        "START NEW RESUME ANALYSIS",
        type="secondary",
        use_container_width=True
    ):

        st.session_state.analysis_result = None
        st.rerun()

    st.markdown(
        '<div class="footer">'
        '<div class="brand"><span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span></div>'
        '<div class="footer-meta">Powered by Resumind AI &bull; &copy; 2026 Resumind AI</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ==========================================================
# 12. INTERVIEW PREP & SKILL TEST STUDIO
# ==========================================================

if st.session_state.page == "Interview":

    st.markdown(
        '<div class="hero">'
        '<span class="hero-tag">✦ AI INTERVIEW PREPARATION STUDIO</span>'
        '<h1>Interactive Mock Interview<br><em>& Skill Test</em></h1>'
        '<p>Test your competencies with questions tailored directly to your skills and domain. Get immediate evaluation, interview readiness grades, and detailed interviewer insights.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # STATE 1: CONFIGURATION (No active test yet)
    if st.session_state.interview_test is None:
        has_resume = (st.session_state.analysis_result is not None)
        active_skills = []
        active_name = "Candidate"
        active_cat = "IT & SOFTWARE"

        if has_resume:
            res = st.session_state.analysis_result
            active_name = res["candidate"]["name"]
            active_cat = res["soura_result"]["resume_category"]
            active_skills = list(res["match_data"].get("resume_skills") or [])
            if not active_skills and res["soura_result"].get("skills"):
                for slist in res["soura_result"]["skills"].values():
                    active_skills.extend(slist)

        # Config Panel
        with st.container(border=True):
            st.markdown(
                '<div class="upload-panel-header">'
                '<span class="panel-badge">TEST CONFIGURATION</span>'
                '<h4>Configure Your Mock Interview</h4>'
                '<p class="panel-desc">Customize your assessment focus, domain alignment, and question volume.</p>'
                '</div>',
                unsafe_allow_html=True
            )

            if has_resume and active_skills:
                st.info(
                    f"🎯 **Resume Synchronized:** Testing skills detected in **{active_name}'s** resume ({active_cat}): "
                    f"*{', '.join(active_skills[:12])}*"
                )
            else:
                st.info(
                    "💡 **No Resume Uploaded Yet:** You can choose your skills manually below, or upload a resume in the **ANALYSER** tab for auto-calibration."
                )

            c1, c2 = st.columns(2, gap="medium")
            with c1:
                focus_mode = st.selectbox(
                    "Interview Focus Area",
                    options=["Balanced Mock Interview", "Technical Only", "Behavioral & Leadership"],
                    index=0,
                    help="Balanced includes both technical knowledge and behavioral scenario questions."
                )

            with c2:
                num_q = st.select_slider(
                    "Number of Questions",
                    options=[3, 5, 8, 10, 15],
                    value=5
                )

            # Manual skill override / addition if desired
            all_known_skills = []
            for slist in SKILL_DATABASE.values():
                all_known_skills.extend(slist)
            all_known_skills = sorted(list(set(all_known_skills)))

            default_skills = [s for s in active_skills if s in all_known_skills] or ["Python", "SQL", "Git", "Problem Solving"]
            selected_skills = st.multiselect(
                "Target Skills to Test",
                options=all_known_skills,
                default=default_skills[:8],
                help="Add or remove skills to tailor the questions."
            )

            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

            if st.button("GENERATE & START TEST →", type="primary", use_container_width=True):
                test_questions = generate_interview_test(
                    candidate_skills=selected_skills,
                    resume_category=active_cat,
                    num_questions=num_q,
                    focus_mode=focus_mode
                )
                st.session_state.interview_test = test_questions
                st.session_state.interview_answers = {}
                st.session_state.interview_eval = None
                st.session_state.interview_focus_mode = focus_mode
                st.rerun()

    # STATE 2: ACTIVE TEST IN PROGRESS
    elif st.session_state.interview_eval is None:
        questions = st.session_state.interview_test
        total_q = len(questions)

        top_col1, top_col2 = st.columns([3, 1])
        with top_col1:
            st.markdown(
                f'<span class="section-tag">ASSESSMENT IN PROGRESS</span>'
                f'<div class="section-heading" style="font-size:26px; margin:10px 0;">'
                f'Answer the following {total_q} questions</div>',
                unsafe_allow_html=True
            )
        with top_col2:
            if st.button("RESET TEST ✕", type="secondary", use_container_width=True):
                st.session_state.interview_test = None
                st.session_state.interview_answers = {}
                st.session_state.interview_eval = None
                st.rerun()

        st.progress(
            len(st.session_state.interview_answers) / max(1, total_q),
            text=f"Completed {len(st.session_state.interview_answers)} of {total_q} questions"
        )

        for q in questions:
            q_id = q["test_id"]
            current_choice = st.session_state.interview_answers.get(q_id, None)

            with st.container(border=True):
                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
                    f'<div>'
                    f'<span class="panel-badge">QUESTION {q["question_number"]} OF {total_q}</span> '
                    f'<span class="skill-tag" style="margin:0 4px;">{escape(q["skill"])}</span>'
                    f'</div>'
                    f'<span style="font-size:11px; font-weight:600; color:#5A4D43; background:#EDEAE2; border-radius:20px; padding:3px 10px;">{escape(q["difficulty"])}</span>'
                    f'</div>'
                    f'<h4 style="margin:8px 0 14px 0; color:#3A2C23; font-family:\'Outfit\', sans-serif; font-size:17px; font-weight:700; line-height:1.45;">'
                    f'{escape(q["question"])}</h4>',
                    unsafe_allow_html=True
                )

                selected_opt = st.radio(
                    label=f"q_label_{q_id}",
                    options=q["options"],
                    index=current_choice if current_choice is not None else None,
                    key=f"radio_{q_id}",
                    label_visibility="collapsed"
                )

                if selected_opt is not None:
                    st.session_state.interview_answers[q_id] = q["options"].index(selected_opt)

        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)

        if st.button("SUBMIT TEST & VIEW EVALUATION →", type="primary", use_container_width=True):
            if len(st.session_state.interview_answers) < total_q:
                st.warning(f"Please answer all {total_q} questions before submitting (currently answered: {len(st.session_state.interview_answers)}).")
            else:
                eval_result = evaluate_test(st.session_state.interview_test, st.session_state.interview_answers)
                st.session_state.interview_eval = eval_result
                if st.session_state.auth_user is not None:
                    cand_name = "Candidate"
                    if st.session_state.analysis_result:
                        cand_name = st.session_state.analysis_result["candidate"]["name"]
                    save_interview_attempt(
                        user_id=st.session_state.auth_user["id"],
                        access_token=st.session_state.auth_access_token,
                        refresh_token=st.session_state.auth_refresh_token,
                        candidate_name=cand_name,
                        focus_mode=st.session_state.get("interview_focus_mode", "Balanced Mock Interview"),
                        eval_res=eval_result,
                        analysis_id=st.session_state.get("last_analysis_id"),
                    )
                st.rerun()

    # STATE 3: TEST EVALUATION & DETAILED RESULTS
    else:
        eval_res = st.session_state.interview_eval
        score_pct = eval_res["score_pct"]
        correct_count = eval_res["correct_count"]
        total_q = eval_res["total"]
        tier = eval_res["tier"]

        candidate_name = "Candidate"
        if st.session_state.analysis_result:
            candidate_name = st.session_state.analysis_result["candidate"]["name"]

        # Results Hero Card
        st.markdown(
            f'<div style="background: #FAF8F4; border: 1px solid #DCD4C6; border-radius: 24px; padding: 30px; '
            f'box-shadow: 0 6px 20px rgba(58,44,35,0.04); text-align: center; margin-bottom: 25px;">'
            f'<span class="panel-badge">EVALUATION COMPLETE</span>'
            f'<h1 style="font-family:\'Outfit\', sans-serif; font-weight: 900; letter-spacing:-0.03em; font-size: 56px; margin: 10px 0; color: #3A2C23;">'
            f'{score_pct}%</h1>'
            f'<div style="font-size: 17px; font-weight: 700; color: {eval_res["readiness_color"]}; margin-bottom: 8px;">'
            f'{eval_res["readiness_badge"]}</div>'
            f'<p style="color: #73665C; font-size: 14px; margin: 0;">'
            f'Answered <b>{correct_count}</b> out of <b>{total_q}</b> questions correctly</p>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Performance Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Score", f"{score_pct}%")
        with m2:
            st.metric("Correct Answers", f"{correct_count} / {total_q}")
        with m3:
            st.metric("Readiness Tier", tier)

        # Per-Skill Mastery Breakdown
        if eval_res.get("skill_stats"):
            st.divider()
            st.markdown(
                '<span class="section-tag">COMPETENCY ACCURACY</span>'
                '<div class="section-heading">Skill-by-Skill Breakdown</div>',
                unsafe_allow_html=True
            )

            skill_cols = st.columns(min(4, max(1, len(eval_res["skill_stats"]))))
            for idx, (sname, sdata) in enumerate(eval_res["skill_stats"].items()):
                col = skill_cols[idx % len(skill_cols)]
                with col:
                    col_score = round((sdata["correct"] / sdata["total"]) * 100)
                    with st.container(border=True):
                        st.markdown(f"**{escape(sname)}**")
                        st.markdown(f"Accuracy: **{col_score}%** ({sdata['correct']}/{sdata['total']})")

        # Weak skills alert
        if eval_res.get("weak_skills"):
            st.warning(
                f"💡 **Recommended Revision:** Focus your final interview prep on: "
                f"**{', '.join(eval_res['weak_skills'])}**."
            )
        else:
            st.success("🎉 Outstanding! You answered every question correctly across all tested skill domains!")

        # Detailed Question Review
        st.divider()
        st.markdown(
            '<span class="section-tag">DETAILED REVIEW</span>'
            '<div class="section-heading">Question-by-Question Analysis & Interviewer Insights</div>',
            unsafe_allow_html=True
        )

        for item in eval_res["review"]:
            is_corr = item["is_correct"]
            bg_card = "#EBF1E5" if is_corr else "#F8EAE6"
            border_card = "#C3D3B3" if is_corr else "#E2BEB4"
            header_color = "#2E4722" if is_corr else "#7E3024"
            status_text = "✓ CORRECT" if is_corr else "✕ INCORRECT"

            st.markdown(
                f'<div style="background:{bg_card}; border:1px solid {border_card}; border-radius:20px; padding:20px; margin-bottom:18px;">'
                f'<div style="display:flex; justify-content:space-between; margin-bottom:8px;">'
                f'<span style="font-weight:700; color:{header_color}; font-size:12px; letter-spacing:.05em;">'
                f'{status_text} • QUESTION {item["question_number"]} ({escape(item["skill"])})</span>'
                f'</div>'
                f'<h4 style="margin:4px 0 12px 0; color:#3A2C23; font-family:\'Outfit\', sans-serif; font-weight:700; font-size:17px; line-height:1.45;">'
                f'{escape(item["question"])}</h4>'
                f'<p style="margin:4px 0; font-size:14px; color:#3A2C23;"><b>Your Answer:</b> '
                f'<span style="color:{"#2E4722" if is_corr else "#9C3F31"};">{escape(item["user_answer_text"])}</span></p>'
                f'{"<p style=\'margin:4px 0; font-size:14px; color:#2E4722;\'><b>Correct Answer:</b> " + escape(item["correct_answer_text"]) + "</p>" if not is_corr else ""}'
                f'<div style="margin-top:12px; padding-top:10px; border-top:1px dashed {border_card};">'
                f'<p style="margin:4px 0; font-size:13px; color:#5A4D43; line-height:1.6;"><b>Explanation:</b> {escape(item["explanation"])}</p>'
                f'<p style="margin:6px 0 0 0; font-size:13px; color:#4A5536; line-height:1.6;"><b>💡 Interviewer Insight:</b> {escape(item["insight"])}</p>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Download & Next Steps
        st.divider()
        st.markdown("### Export & Next Steps")

        pdf_bytes = generate_interview_pdf_report(candidate_name, eval_res)
        if pdf_bytes:
            st.download_button(
                "DOWNLOAD INTERVIEW READINESS REPORT (PDF)",
                data=pdf_bytes,
                file_name=f"Interview_Readiness_{candidate_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        retake_c1, retake_c2 = st.columns(2)
        with retake_c1:
            if st.button("TAKE A NEW TEST ↻", type="secondary", use_container_width=True):
                st.session_state.interview_test = None
                st.session_state.interview_answers = {}
                st.session_state.interview_eval = None
                st.rerun()

        with retake_c2:
            if st.button("BACK TO RESUME AUDIT →", type="secondary", use_container_width=True):
                st.session_state.page = "Analysis"
                st.rerun()

    st.markdown(
        '<div class="footer">'
        '<div class="brand"><span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span></div>'
        '<div class="footer-meta">AI Career Readiness &amp; Interview Prep &bull; &copy; 2026 Resumind AI</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ==========================================================
# 13. CAREER PATHS & JOB PREDICTOR STUDIO
# ==========================================================

if st.session_state.page == "CareerPaths":

    st.markdown(
        '<div class="hero">'
        '<span class="hero-tag">✦ AI CAREER ROADMAP & ROLE PREDICTOR</span>'
        '<h1>Explore Suitable Job Roles<br><em>& Career Paths</em></h1>'
        '<p>Discover roles precisely matched to your background, understand why each path fits your profile, identify target skills to learn, and apply directly with one click.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    has_resume = (st.session_state.analysis_result is not None)
    active_skills = []
    active_name = "Candidate"
    active_cat = "IT & SOFTWARE"

    if has_resume:
        res = st.session_state.analysis_result
        active_name = res["candidate"]["name"]
        active_cat = res["soura_result"]["resume_category"]
        active_skills = list(res["match_data"].get("resume_skills") or [])
        if not active_skills and res["soura_result"].get("skills"):
            for slist in res["soura_result"]["skills"].values():
                active_skills.extend(slist)
        for p in res["soura_result"].get("trained_skill_predictions", []):
            if p.get("predicted_present") and p.get("skill") not in active_skills:
                active_skills.append(p["skill"])

        st.info(
            f"🎯 **Personalized Career Predictions Active:** Analyzed for **{active_name}** ({active_cat}) "
            f"based on {len(active_skills)} verified skills."
        )
    else:
        st.info(
            "💡 **Tip:** Upload your resume in the **ANALYSER** tab to calculate custom match percentages and personalized fit rationales. Below are all verified industry roles."
        )

    # Filter controls
    all_categories = ["All Domains"] + sorted(list(set(j["category"] for j in JOB_CATALOG)))
    sel_cat = st.segmented_control("Domain Filter", options=all_categories, default="All Domains")

    # Predict or compute scores
    if active_skills:
        all_predicted = predict_job_options(
            candidate_skills=active_skills,
            resume_category=active_cat,
            top_n=len(JOB_CATALOG)
        )
    else:
        all_predicted = predict_job_options(
            candidate_skills=["Python", "SQL", "Git"],
            top_n=len(JOB_CATALOG)
        )

    # Filter by category if selected
    if sel_cat and sel_cat != "All Domains":
        display_roles = [r for r in all_predicted if r["category"] == sel_cat]
    else:
        display_roles = all_predicted

    st.markdown(f'<div style="font-size:14px; color:#73665C; margin:12px 0 18px 0;">Showing <b>{len(display_roles)}</b> career options</div>', unsafe_allow_html=True)

    for role_idx, role in enumerate(display_roles):
        with st.container(border=True):
            rcol1, rcol2 = st.columns([3, 1])
            with rcol1:
                st.markdown(
                    f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
                    f'<span class="panel-badge">ROLE #{role_idx+1}</span>'
                    f'<span style="font-size:11px; font-weight:600; color:#5A4D43; background:#EDEAE2; border-radius:20px; padding:2px 8px;">{escape(role["category"])}</span>'
                    f'</div>'
                    f'<h3 style="margin:2px 0 6px 0; color:#3A2C23; font-family:\'Outfit\', sans-serif; font-size:21px; font-weight:700;">'
                    f'{escape(role["title"])}</h3>',
                    unsafe_allow_html=True
                )
            with rcol2:
                if has_resume:
                    st.markdown(
                        f'<div style="text-align:right;">'
                        f'<div style="font-family:\'Outfit\', sans-serif; font-size:28px; font-weight:800; color:{role["suitability_color"]};">'
                        f'{role["fit_score"]}%</div>'
                        f'<span style="display:inline-block; font-size:11px; font-weight:700; color:{role["suitability_color"]}; background:{role["suitability_bg"]}; padding:3px 10px; border-radius:20px;">'
                        f'{role["suitability_label"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="text-align:right;">'
                        f'<span style="font-size:12px; font-weight:700; color:#4A5536; background:#E5EAD9; padding:4px 12px; border-radius:20px;">'
                        f'Demand: {escape(role["market_demand"])}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            st.markdown(f'<p style="color:#73665C; font-size:13px; margin:0 0 10px 0;">{escape(role["description"])}</p>', unsafe_allow_html=True)

            # Personalized Rationale
            if has_resume:
                st.markdown(
                    f'<div style="background:#F5F2EB; border-left:3px solid {role["suitability_color"]}; padding:10px 14px; border-radius:10px; margin-bottom:12px;">'
                    f'<div style="font-size:11px; font-weight:700; color:{role["suitability_color"]}; letter-spacing:.05em; text-transform:uppercase; margin-bottom:3px;">💡 Why this is a suitable path:</div>'
                    f'<div style="font-size:13px; color:#3A2C23; line-height:1.5;">{role["reasoning"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # Skills comparison
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown("**✓ Demonstrated Skills:**" if has_resume else "**Prerequisite Core Skills:**")
                if has_resume and role["matched_skills"]:
                    st.markdown("".join(f'<span class="skill-tag">✓ {escape(s)}</span>' for s in role["matched_skills"]), unsafe_allow_html=True)
                elif not has_resume:
                    job_obj = next((j for j in JOB_CATALOG if j["id"] == role["id"]), None)
                    req_list = job_obj["required_skills"] if job_obj else []
                    st.markdown("".join(f'<span class="skill-tag">{escape(s)}</span>' for s in req_list), unsafe_allow_html=True)
                else:
                    st.caption("Foundational overlap")

            with sc2:
                st.markdown("**✦ Skills to Pick Up (Close the Gap):**" if has_resume else "**Advantage / Bonus Skills:**")
                if has_resume and role["skills_to_learn"]:
                    st.markdown("".join(f'<span class="missing-tag">+ {escape(s)}</span>' for s in role["skills_to_learn"]), unsafe_allow_html=True)
                elif not has_resume:
                    job_obj = next((j for j in JOB_CATALOG if j["id"] == role["id"]), None)
                    bonus_list = job_obj["bonus_skills"] if job_obj else []
                    st.markdown("".join(f'<span class="skill-tag" style="background:#EBF1E5; color:#2E4722; border-color:#C3D3B3;">+ {escape(s)}</span>' for s in bonus_list), unsafe_allow_html=True)
                else:
                    st.caption("All core prerequisites satisfied!")

            # Compensation & Progression
            st.markdown(
                f'<div style="font-size:12px; color:#73665C; margin-top:10px; border-top:1px solid #DCD4C6; padding-top:8px;">'
                f'<b>Compensation:</b> {escape(role["salary_range"])} &nbsp;|&nbsp; '
                f'<b>Market Demand:</b> {escape(role["market_demand"])} &nbsp;|&nbsp; '
                f'<b>Career Path:</b> {escape(role["growth_path"])}'
                f'</div>',
                unsafe_allow_html=True
            )

            # Action Links
            act1, act2, act3, act4 = st.columns([1, 1, 1, 1.3])
            with act1:
                st.link_button("LinkedIn Jobs ↗", role["links"]["linkedin"], use_container_width=True)
            with act2:
                st.link_button("Indeed Jobs ↗", role["links"]["indeed"], use_container_width=True)
            with act3:
                st.link_button("Glassdoor ↗", role["links"]["glassdoor"], use_container_width=True)
            with act4:
                if st.button("Practice Mock Test 🎯", key=f"btn_explore_test_{role['id']}", type="secondary", use_container_width=True):
                    job_obj = next((j for j in JOB_CATALOG if j["id"] == role["id"]), None)
                    target_skills = role.get("matched_skills") or (job_obj["required_skills"] if job_obj else ["Python"])
                    st.session_state.interview_test = generate_interview_test(
                        candidate_skills=target_skills,
                        resume_category=role["category"],
                        num_questions=5,
                        focus_mode="Balanced Mock Interview"
                    )
                    st.session_state.interview_answers = {}
                    st.session_state.interview_eval = None
                    st.session_state.page = "Interview"
                    st.rerun()

    st.markdown(
        '<div class="footer">'
        '<div class="brand"><span class="brand-badge">R</span>RESUMIND <span class="brand-accent">AI</span></div>'
        '<div class="footer-meta">AI Career Intelligence &amp; Job Predictions &bull; &copy; 2026 Resumind AI</div>'
        '</div>',
        unsafe_allow_html=True
    )