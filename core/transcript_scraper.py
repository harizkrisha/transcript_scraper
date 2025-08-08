import os
import ssl
from pytube import Playlist
import re
import json
import requests
from http.cookiejar import MozillaCookieJar
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api._errors import RequestBlocked
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError
from pytube import Playlist

# Shared client and API instances (updated by create_http_client)
ttp_session: requests.Session | None = None
ytt_api: YouTubeTranscriptApi | None = None


# Workaround macOS SSL certificate verification issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


# this function creates an HTTP client that attempts to route through Tor and optionally loads browser cookies
def create_http_client(cookie_file: str = "cookies.txt", use_tor: bool = True) -> tuple[requests.Session, dict]:
    """
    Create an HTTP client that attempts to route through Tor and optionally loads browser cookies.
    
    Args:
        cookie_file: Path to Netscape-format cookies.txt file
        use_tor: Whether to attempt connecting through Tor
        
    Returns:
        tuple: (session, status) where status contains connection information
    """
    global ttp_session, ytt_api

    session = requests.Session()
    status = {
        "using_tor": False,
        "connection_type": "direct",
        "cookies_loaded": False,
        "error": None
    }
    
    # Try to use Tor if requested
    if use_tor:
        tor_proxies = {
            "http":  "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050",
        }
        
        # Test if Tor is available
        try:
            test_session = requests.Session()
            test_session.proxies.update(tor_proxies)
            response = test_session.get("https://check.torproject.org", timeout=5)
            
            if "Congratulations" in response.text:
                session.proxies.update(tor_proxies)
                status["using_tor"] = True
                status["connection_type"] = "Tor"
            else:
                status["error"] = "Tor is running but connection check failed"
        except Exception as e:
            status["error"] = f"Tor not available: {str(e)}"
    else:
        # Direct connection was chosen explicitly; this is not an error
        status["error"] = None
    
    # Load cookies if available
    if os.path.exists(cookie_file):
        try:
            jar = MozillaCookieJar(cookie_file)
            jar.load(ignore_discard=True, ignore_expires=True)
            session.cookies = jar
            status["cookies_loaded"] = True
        except Exception as e:
            status["error"] = f"Failed to load cookies: {str(e)}"

    # Update the shared session and YouTubeTranscriptApi instance
    ttp_session = session
    ytt_api = YouTubeTranscriptApi(http_client=session)

    return session, status

# Shared HTTP client and Transcript API

http_session, connection_status = create_http_client()
ytt_api = YouTubeTranscriptApi(http_client=http_session)

# Function to extract video ID from URL or ID
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

# Function to fetch timed text from YouTube
def fetch_timed_text(video_id: str, language: str = "id") -> list:
    url = f"http://video.google.com/timedtext?lang={language}&v={video_id}"
    try:
        resp = http_session.get(url, timeout=10)
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

# Function to fetch transcript using YouTube Transcript API
def fetch_transcript(video_id: str, language: str = "id") -> list:
    try:
        fetched = ytt_api.fetch(video_id, languages=[language])
        return fetched.to_raw_data()
    except TranscriptsDisabled:
        print(f"Transcripts are disabled for video {video_id}")
        return []
    except NoTranscriptFound:
        print(f"No transcript found for video {video_id}")
        return []
    except RequestBlocked:
        print(f"RequestBlocked for {video_id}, retrying without proxy…")
        http_session.proxies.clear()
        try:
            fetched = ytt_api.fetch(video_id, languages=[language])
            return fetched.to_raw_data()
        except Exception as e:
            print(f"Retry failed: {e}")
    # Catch both ExpatError and ElementTree.ParseError
    except (ExpatError, ET.ParseError) as e:
        print(f"XML parse error ({type(e).__name__}), falling back to timed-text…")

    # Fallback to raw timed-text endpoint
    return fetch_timed_text(video_id, language)

# Function to format the output
def format_output(transcript: list, video_id: str) -> dict:
    raw_content = " ".join(segment['text'] for segment in transcript)
    token_count = len(raw_content) // 4
    url = f"https://www.youtube.com/watch?v={video_id}"
    return {"raw_content": raw_content, "token_count": token_count, "url": url}

# Function to save the output to a JSON
def save_output(data: dict, video_id: str, output_dir: str = "output") -> None:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{video_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Formatted transcript saved to {path}")


def main():
    print("YouTube Transcript Scraper — type 'exit' or 'quit' to stop")
    while True:
        user_input = input("Enter YouTube video or playlist URL/ID (or 'exit' to quit): ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        # Playlist support
        if "playlist" in user_input and "list=" in user_input:
            m = re.search(r"list=([A-Za-z0-9_-]+)", user_input)
            if not m:
                print("Could not extract playlist ID.")
                continue
            playlist_id = m.group(1)
            playlist_url = user_input.split("&si=")[0]
            try:
                pl = Playlist(playlist_url)
            except Exception as e:
                print(f"Error reading playlist: {e}")
                continue
            out_dir = os.path.join("output", playlist_id)
            for video_url in pl.video_urls:
                try:
                    vid = get_video_id(video_url)
                except ValueError as e:
                    print(e)
                    continue
                transcript = fetch_transcript(vid)
                if not transcript:
                    print(f"No transcript for {vid}")
                    continue
                data = format_output(transcript, vid)
                save_output(data, vid, out_dir)
            continue

        # Single video support
        try:
            vid = get_video_id(user_input)
        except ValueError as e:
            print(e)
            continue
        transcript = fetch_transcript(vid)
        if not transcript:
            print("No transcript to save.")
            continue
        data = format_output(transcript, vid)
        save_output(data, vid)

if __name__ == "__main__":
    main()