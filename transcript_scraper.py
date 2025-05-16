import os
import re
import json
import requests
from http.cookiejar import MozillaCookieJar
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


def create_http_client(cookie_file: str = "cookies.txt") -> requests.Session:
    """
    Create an HTTP client that routes through Tor and optionally loads browser cookies.
    """
    session = requests.Session()
    # Route through Tor (SOCKS5) on localhost:9050
    session.proxies.update({
        "http":  "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050",
    })
    # Load cookies if available (Netscape format)
    if os.path.exists(cookie_file):
        jar = MozillaCookieJar(cookie_file)
        jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies = jar
    return session

# Initialize a shared HTTP client and transcript API instance
http_client = create_http_client()
ytt_api = YouTubeTranscriptApi(http_client=http_client)


def get_video_id(url_or_id: str) -> str:
    """
    Extract the YouTube video ID from a URL or return it if already an ID.
    Supports typical YouTube URL formats and short links.
    """
    patterns = [
        r"(?:v=)([0-9A-Za-z_-]{11})",  # standard URL
        r"(?:be/)([0-9A-Za-z_-]{11})",  # short URL
        r"^([0-9A-Za-z_-]{11})$"        # plain ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract a valid video ID from '{url_or_id}'")


def fetch_transcript(video_id: str, language: str = "id") -> list:
    """
    Fetch the transcript for the given video ID in the specified language (default Indonesian).
    Uses the shared HTTP client (Tor + cookies).
    """
    try:
        # ytt_api.fetch returns a FetchedTranscript object that's iterable
        fetched = ytt_api.fetch(video_id, languages=[language])
        # Convert to raw list of dicts if needed
        return fetched.to_raw_data()
    except TranscriptsDisabled:
        print(f"Transcripts are disabled for video {video_id}")
    except NoTranscriptFound:
        print(f"No transcript found for video {video_id} in language '{language}'")
    return []


def format_output(transcript: list, video_id: str) -> dict:
    """
    Combine the transcript segments into a single raw_content string, estimate token count,
    and set the video URL. Returns a dict with 'raw_content', 'token_count', and 'url'.
    """
    raw_content = " ".join(segment['text'] for segment in transcript)
    token_count = len(raw_content) // 4
    url = f"https://www.youtube.com/watch?v={video_id}"

    return {
        "raw_content": raw_content,
        "token_count": token_count,
        "url": url
    }


def save_output(data: dict, video_id: str) -> None:
    """
    Save the formatted output dict to a JSON file under 'output/<video_id>.json'.
    """
    os.makedirs("output", exist_ok=True)
    path = os.path.join("output", f"{video_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Formatted transcript saved to {path}")


def main():
    user_input = input("Enter YouTube video URL or ID: ").strip()
    try:
        video_id = get_video_id(user_input)
    except ValueError as e:
        print(e)
        return

    transcript = fetch_transcript(video_id)
    if not transcript:
        print("No transcript to save.")
        return

    output_data = format_output(transcript, video_id)
    save_output(output_data, video_id)


if __name__ == "__main__":
    main()
