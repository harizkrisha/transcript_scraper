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

# ─── SSL Workaround for macOS ─────────────────────────────────────────────
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# ─── Initialize HTTP client (via transcript_scraper) ───────────────────────
ttp_session = create_http_client()

# ─── Sidebar: Project & Subproject Management ────────────────────────────
OUTPUT_ROOT = "output"
st.sidebar.header("Project Management")

# Initialize ProjectManager
pm = ProjectManager(OUTPUT_ROOT)

# Session state defaults
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "current_subproject" not in st.session_state:
    st.session_state.current_subproject = None
if "adding_project" not in st.session_state:
    st.session_state.adding_project = False
if "adding_subproject" not in st.session_state:
    st.session_state.adding_subproject = False

# -- Display existing structure --
st.sidebar.subheader("Existing Projects")
projects = pm.get_projects()
for proj in projects:
    st.sidebar.write(f"• {proj}")
    for sub in pm.get_subprojects(proj):
        st.sidebar.write(f"    – {sub}")

st.sidebar.markdown("---")

# -- Project Selection --
proj_choice = st.sidebar.selectbox(
    "Select Project",
    ["-- none --"] + projects,
    key="proj_select"
)
if proj_choice != "-- none --":
    st.session_state.current_project = proj_choice
    st.session_state.current_subproject = None

# -- Add New Project --
if st.sidebar.button("Add New Project"):
    st.session_state.adding_project = True

if st.session_state.adding_project:
    new_proj = st.sidebar.text_input("Project Name", key="new_proj_input")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Save Project"):
            success, msg = pm.create_project(new_proj)
            if success:
                st.success(msg)
                st.session_state.adding_project = False
            else:
                st.error(msg)
    with col2:
        if st.button("Cancel"):
            st.session_state.adding_project = False

# -- Subproject Selection --
if st.session_state.current_project:
    subprojects = pm.get_subprojects(st.session_state.current_project)
    sub_choice = st.sidebar.selectbox(
        "Select Subproject",
        ["-- none --"] + subprojects,
        key="sub_select"
    )
    if sub_choice != "-- none --":
        st.session_state.current_subproject = sub_choice

    # Add New Subproject
    if st.sidebar.button("Add New Subproject"):
        st.session_state.adding_subproject = True

    if st.session_state.adding_subproject:
        new_sub = st.sidebar.text_input("Subproject Name", key="new_sub_input")
        c1, c2 = st.sidebar.columns(2)
        with c1:
            if st.button("Save Subproject"):
                success, msg = pm.create_subproject(
                    st.session_state.current_project, new_sub
                )
                if success:
                    st.success(msg)
                    st.session_state.adding_subproject = False
                else:
                    st.error(msg)
        with c2:
            if st.button("Cancel Subproject"):
                st.session_state.adding_subproject = False

st.sidebar.markdown("---")
st.sidebar.write("Current Selection:")
st.sidebar.write(f"Project: {st.session_state.current_project or 'None'}")
st.sidebar.write(f"Subproject: {st.session_state.current_subproject or 'None'}")

# Determine base output directory
base_dir = OUTPUT_ROOT
if st.session_state.current_project:
    base_dir = os.path.join(base_dir, st.session_state.current_project)
    if st.session_state.current_subproject:
        base_dir = os.path.join(base_dir, st.session_state.current_subproject)
os.makedirs(base_dir, exist_ok=True)

# ─── STREAMLIT MAIN UI ────────────────────────────────────────────────────
st.title("YouTube Transcript Scraper")

input_url = st.text_input("Enter YouTube video or playlist URL/ID:")

if st.button("Fetch Transcript"):
    try:
        # Playlist mode
        if "playlist" in input_url and "list=" in input_url:
            pid = re.search(r"list=([A-Za-z0-9_-]+)", input_url).group(1)
            st.write(f"🔗 Playlist detected: {pid}")
            pl = Playlist(input_url)
            playlist_dir = os.path.join(base_dir, pid)
            os.makedirs(playlist_dir, exist_ok=True)

            for url in pl.video_urls:
                vid = get_video_id(url)
                segs = fetch_transcript(vid)
                if not segs:
                    st.warning(f"No transcript for {vid}")
                    continue
                data = format_output(segs, vid)
                save_output(data, vid, playlist_dir)
                st.success(f"Saved {vid}.json → {playlist_dir}")

        # Single-video mode
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
