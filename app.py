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

# Import core functions from the scraper module
from transcript_scraper import (
    create_http_client,
    get_video_id,
    fetch_transcript,
    fetch_timed_text,
    format_output,
    save_output
)

# ─── SSL Workaround for macOS ─────────────────────────────────────────────
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# ─── Initialize HTTP client & API (via transcript_scraper) ────────────────
ttp_session = create_http_client()

# ─── STREAMLIT UI ────────────────────────────────────────────────────────
st.title("YouTube Transcript Scraper")

input_url = st.text_input("Enter YouTube video or playlist URL/ID:")
if st.button("Fetch Transcript"):
    try:
        # Playlist mode
        if "playlist" in input_url and "list=" in input_url:
            match = re.search(r"list=([A-Za-z0-9_-]+)", input_url)
            pid = match.group(1)
            st.write(f"📄 Detected playlist ID: {pid}")

            pl = Playlist(input_url)
            out_dir = os.path.join("output", pid)
            os.makedirs(out_dir, exist_ok=True)

            for url in pl.video_urls:
                vid = get_video_id(url)
                segments = fetch_transcript(vid)
                if not segments:
                    st.warning(f"No transcript for {vid}")
                    continue
                data = format_output(segments, vid)
                save_output(data, vid, out_dir)
                st.success(f"Saved {vid}.json to {out_dir}")

        # Single-video mode
        else:
            vid = get_video_id(input_url)
            segments = fetch_transcript(vid)
            if not segments:
                st.warning("No transcript found.")
            else:
                data = format_output(segments, vid)

                # Automatically save to disk
                save_output(data, vid)  
                st.success(f"Saved {vid}.json to output/")

    except Exception as e:
        st.error(f"Error: {e}")
