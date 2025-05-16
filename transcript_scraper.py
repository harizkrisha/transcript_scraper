import os
import re
import json
import requests
from http.cookiejar import MozillaCookieJar
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api._errors import RequestBlocked
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError


def create_http_client(cookie_file: str = "cookies.txt") -> requests.Session:
    """
    Create an HTTP client that routes through Tor and optionally loads browser cookies.
    """
    session = requests.Session()
    session.proxies.update({
        "http":  "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050",
    })
    if os.path.exists(cookie_file):
        jar = MozillaCookieJar(cookie_file)
        jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies = jar
    return session

# Shared HTTP client and Transcript API
ttp_session = create_http_client()
ytt_api = YouTubeTranscriptApi(http_client=ttp_session)


def get_video_id(url_or_id: str) -> str:
    patterns = [
        r"(?:v=)([0-9A-Za-z_-]{11})",
        r"(?:be/)([0-9A-Za-z_-]{11})",
        r"^([0-9A-Za-z_-]{11})$"
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract a valid video ID from '{url_or_id}'")


def fetch_timed_text(video_id: str, language: str = "id") -> list:
    url = f"http://video.google.com/timedtext?lang={language}&v={video_id}"
    try:
        resp = ttp_session.get(url, timeout=10)
        if not resp.ok or not resp.text.strip():
            return []
        root = ET.fromstring(resp.text)
    except (requests.RequestException, ExpatError) as e:
        print(f"Timed-text fetch failed: {e}")
        return []
    segments = []
    for elem in root.findall('text'):
        text = (elem.text or '').strip().replace("\n", " ")
        start = float(elem.attrib.get('start', 0))
        duration = float(elem.attrib.get('dur', 0))
        segments.append({'text': text, 'start': start, 'duration': duration})
    return segments


def fetch_transcript(video_id: str, language: str = "id") -> list:
    try:
        fetched = ytt_api.fetch(video_id, languages=[language])
        return fetched.to_raw_data()
    except TranscriptsDisabled:
        print(f"Transcripts are disabled for video {video_id}")
        return []
    except NoTranscriptFound:
        print(f"No transcript found for video {video_id} in language '{language}'")
        return []
    except RequestBlocked:
        print(f"RequestBlocked: YouTube blocked requests for {video_id}. Retrying without proxy...")
        ttp_session.proxies.clear()
        try:
            fetched = ytt_api.fetch(video_id, languages=[language])
            return fetched.to_raw_data()
        except Exception as e:
            print(f"Retry without proxy failed: {e}")
    except ExpatError:
        print(f"XML parse error from API, falling back to raw timed-text...")
    return fetch_timed_text(video_id, language)


def format_output(transcript: list, video_id: str) -> dict:
    raw_content = " ".join(segment['text'] for segment in transcript)
    token_count = len(raw_content) // 4
    url = f"https://www.youtube.com/watch?v={video_id}"
    return {"raw_content": raw_content, "token_count": token_count, "url": url}


def save_output(data: dict, video_id: str) -> None:
    os.makedirs("output", exist_ok=True)
    path = os.path.join("output", f"{video_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Formatted transcript saved to {path}")


def main():
    print("YouTube Transcript Scraper — type 'exit' or 'quit' to stop")
    while True:
        user_input = input("Enter YouTube video URL or ID (or 'exit' to quit): ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        try:
            video_id = get_video_id(user_input)
        except ValueError as e:
            print(e)
            continue
        transcript = fetch_transcript(video_id)
        if not transcript:
            print("No transcript to save.")
            continue
        output_data = format_output(transcript, video_id)
        save_output(output_data, video_id)

if __name__ == "__main__":
    main()
