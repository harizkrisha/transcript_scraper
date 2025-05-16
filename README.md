# YouTube Transcript Scraper

This Python script fetches and saves transcripts for YouTube videos or entire playlists (Indonesian by default), with built‑in support for Tor proxy routing, optional cookie authentication, and intelligent fallbacks.

---

## Features

* **Interactive CLI**: Continuously prompts until you type `exit` or `quit`.
* **Single Video**: Fetches transcripts from one video URL/ID using `youtube-transcript-api`.
* **Playlist Mode**: Given a playlist URL/ID, iterates through every video and saves each transcript separately.
* **Anonymized Requests**: Routes through Tor (`socks5h://127.0.0.1:9050`) to avoid IP bans.
* **Cookie Authentication**: Detects a `cookies.txt` (Netscape format) for age‑restricted or region‑locked content.
* **Robust Fallbacks**:

  * Retries without Tor if blocked.
  * Falls back to raw timed‑text XML parsing on error.
* **JSON Output**: Saves each transcript in `output/` (or `output/<playlist_id>/`) with:

  ```json
  {
    "raw_content": "…",
    "token_count": 123,
    "url": "https://www.youtube.com/watch?v=…"
  }
  ```

---

## Prerequisites

* **Python** 3.7+
* **pip** for installing Python packages
* **Tor** service (for SOCKS5 proxy)
* *(Optional)* Browser cookies in `cookies.txt` (export via a plugin like "Export Cookies" in Netscape format)

---

## Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/yourusername/youtube_scraper.git
   cd youtube_scraper
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tor**

   * **macOS (Homebrew)**:

     ```bash
     brew install tor
     brew services start tor
     ```
   * **Ubuntu/Debian**:

     ```bash
     sudo apt update
     sudo apt install tor
     sudo systemctl enable --now tor
     ```
   * **Windows**:

     1. Download and install the [Tor Expert Bundle](https://www.torproject.org/download/).
     2. Start `tor.exe` in a terminal.

4. **(Optional) Export Cookies**

   * Use a browser extension (e.g., "EditThisCookie" or "Cookie-Editor") to export your YouTube cookies in **Netscape** format to a file named `cookies.txt` in the script directory.

---

## Usage

Run the scraper:

```bash
python transcript_scraper.py
```

* **Single video**: Paste a YouTube URL or ID at the prompt.
* **Playlist**: Paste a playlist link (`https://youtube.com/playlist?list=…`) and the script will batch‑process every video.
* **Exit**: Type `exit` or `quit` when you’re done.

Transcripts appear in the `output/` folder (or `output/<playlist_id>/`).

---

## Troubleshooting

* **Tor not listening on 127.0.0.1:9050?**
  Ensure the Tor daemon is running:  `tor` or `brew services start tor` (macOS) or `systemctl start tor` (Linux).

* **SSL issues on macOS?**
  Run the bundled `Install Certificates.command` found in your Python installation directory (e.g., `/Applications/Python 3.x/`).

* **No transcript found?**

  * Video may not have captions in Indonesian.
  * Remove `languages=["id"]` or adjust the language code in the script.

---

## License

MIT © Your Name
