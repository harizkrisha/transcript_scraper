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

# ─── Sidebar: Project Management ─────────────────────────────────────────
OUTPUT_ROOT = "output"
st.sidebar.header("Project Management")

pm = ProjectManager(OUTPUT_ROOT)
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# Show existing projects
st.sidebar.subheader("Existing Projects")
for proj in pm.get_projects():
    st.sidebar.write(f"• {proj}")

# Select a project
project = st.sidebar.selectbox(
    "Select Project",
    ["-- none --"] + pm.get_projects(),
    key="project_select"
)
if project != "-- none --":
    st.session_state.current_project = project
    st.sidebar.success(f"Selected: {project}")
else:
    st.session_state.current_project = None

# Add new project
if st.sidebar.button("Add New Project"):
    st.session_state.adding_project = True

if st.session_state.get("adding_project", False):
    new_proj = st.sidebar.text_input("New Project Name", key="new_proj_input")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Save Project", key="save_proj"):
            success, msg = pm.create_project(new_proj)
            if success:
                st.success(msg)
                st.session_state.adding_project = False
            else:
                st.error(msg)
    with col2:
        if st.button("Cancel", key="cancel_proj"):
            st.session_state.adding_project = False

st.sidebar.markdown("---")
st.sidebar.write("Current Project:")
st.sidebar.write(st.session_state.get("current_project") or "None")

# ─── Determine base directory ─────────────────────────────────────────────
if st.session_state.get("current_project"):
    base_dir = os.path.join(OUTPUT_ROOT, st.session_state.current_project)
    os.makedirs(base_dir, exist_ok=True)
else:
    base_dir = None

# ─── Main UI ──────────────────────────────────────────────────────────────
st.title("YouTube Transcript Scraper")

input_url = st.text_input("Enter YouTube video or playlist URL/ID:")

if st.button("Fetch Transcript"):
    if not base_dir:
        st.error("Please select or create a project first.")
    else:
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
