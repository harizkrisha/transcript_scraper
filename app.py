import os
import ssl
import re
import json
import requests
import streamlit as st
from http.cookiejar import MozillaCookieJar
from xml.parsers.expat import ExpatError
import xml.etree.ElementTree as ET
from pytube import Playlist

# Import core functions from your module
from core.transcript_scraper import (
    create_http_client,
    get_video_id,
    fetch_transcript,
    format_output,
    save_output
)
from core.project_manager import ProjectManager
from core.dashboard import (
    get_project_level_stats,
    get_subproject_level_stats
)
from core.token_estimator import TokenEstimator

# ─── SSL Workaround for macOS ─────────────────────────────────────────────
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# ─── Initialize HTTP client ────────────────────────────────────────────────
ttp_session = create_http_client()

# ─── Application Mode ─────────────────────────────────────────────────────
mode = st.sidebar.radio("Mode", ["Scraper", "Dashboard"])

# ─── Common Sidebar: Projects & Subprojects ───────────────────────────────
OUTPUT_ROOT = "output"
pm = ProjectManager(OUTPUT_ROOT)
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# Session state defaults
for key in ("current_project", "current_subproject", "adding_project", "adding_subproject"):
    if key not in st.session_state:
        st.session_state[key] = None if "current" in key else False

st.sidebar.header("Project Management")
# Show existing
for proj in pm.get_projects():
    st.sidebar.write(f"• {proj}")
st.sidebar.markdown("---")

# Select / create project
proj_list = ["-- none --"] + pm.get_projects()
proj_choice = st.sidebar.selectbox("Project", proj_list, key="proj_sel")
if proj_choice != "-- none --":
    st.session_state.current_project = proj_choice
    st.session_state.current_subproject = None

if st.sidebar.button("Add New Project"):
    st.session_state.adding_project = True
if st.session_state.adding_project:
    new_p = st.sidebar.text_input("New project name", key="new_proj")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button("Save Project", key="save_proj"):
            ok, msg = pm.create_project(new_p)
            st.success(msg) if ok else st.error(msg)
            st.session_state.adding_project = False
    with c2:
        if st.button("Cancel", key="cancel_proj"):
            st.session_state.adding_project = False

# Select / create subproject
if st.session_state.current_project:
    subs = ["-- none --"] + pm.get_subprojects(st.session_state.current_project)
    sub_choice = st.sidebar.selectbox("Subproject", subs, key="sub_sel")
    if sub_choice != "-- none --":
        st.session_state.current_subproject = sub_choice

    if st.sidebar.button("Add New Subproject"):
        st.session_state.adding_subproject = True
    if st.session_state.adding_subproject:
        new_s = st.sidebar.text_input("New subproject name", key="new_sub")
        d1, d2 = st.sidebar.columns(2)
        with d1:
            if st.button("Save Sub", key="save_sub"):
                ok, msg = pm.create_subproject(st.session_state.current_project, new_s)
                st.success(msg) if ok else st.error(msg)
                st.session_state.adding_subproject = False
        with d2:
            if st.button("Cancel Sub", key="cancel_sub"):
                st.session_state.adding_subproject = False

st.sidebar.markdown("---")
st.sidebar.write("Current:")
st.sidebar.write(f"Project: {st.session_state.current_project or 'None'}")
st.sidebar.write(f"Subproject: {st.session_state.current_subproject or 'None'}")

# Determine base directory
base_dir = OUTPUT_ROOT
if st.session_state.current_project:
    base_dir = os.path.join(base_dir, st.session_state.current_project)
    if st.session_state.current_subproject:
        base_dir = os.path.join(base_dir, st.session_state.current_subproject)
os.makedirs(base_dir, exist_ok=True)

# ─── SCRAPER MODE ─────────────────────────────────────────────────────────
if mode == "Scraper":
    st.title("YouTube Transcript Scraper")
    input_url = st.text_input("Enter video or playlist URL/ID:")
    if st.button("Fetch Transcript"):
        if not st.session_state.current_project:
            st.error("Select or create a project first.")
        else:
            try:
                # Playlist
                if "playlist" in input_url and "list=" in input_url:
                    pid = re.search(r"list=([A-Za-z0-9_-]+)", input_url).group(1)
                    st.write(f"🔗 Playlist: {pid}")
                    pl = Playlist(input_url)
                    pl_dir = os.path.join(base_dir, pid)
                    os.makedirs(pl_dir, exist_ok=True)
                    for url in pl.video_urls:
                        vid = get_video_id(url)
                        segs = fetch_transcript(vid)
                        if not segs:
                            st.warning(f"No transcript for {vid}")
                            continue
                        data = format_output(segs, vid)
                        save_output(data, vid, pl_dir)
                        st.success(f"Saved {vid}.json → {pl_dir}")
                # Single video
                else:
                    vid = get_video_id(input_url)
                    segs = fetch_transcript(vid)
                    if not segs:
                        st.warning("No transcript found.")
                    else:
                        data = format_output(segs, vid)
                        save_output(data, vid, base_dir)
                        st.success(f"Saved {vid}.json → {base_dir}")
            except Exception as e:
                st.error(f"Error: {e}")

# ─── DASHBOARD MODE ───────────────────────────────────────────────────────
else:
    st.title("Dashboard")
    st.write("Project-level stats (files, tokens, bytes):")
    proj_stats = get_project_level_stats(OUTPUT_ROOT)
    st.table([{"Project": p, "Files": f, "Tokens": t, "Bytes": b} for p, f, t, b in proj_stats])

    st.write("Subproject-level stats:")
    sub_stats = get_subproject_level_stats(OUTPUT_ROOT)
    st.table([{"Project": p, "Subproject": s, "Files": f, "Tokens": t, "Bytes": b}
              for p, s, f, t, b in sub_stats])
