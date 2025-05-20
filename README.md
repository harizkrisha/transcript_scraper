# YouTube Transcript Manager & Dashboard

An end‑to‑end Python application that:

* **Scrapes:** Fetches Indonesian (or other) transcripts from YouTube videos or playlists via Tor proxy and optional cookie authentication.
* **Organizes:** Saves each transcript into a hierarchical `output/<project>/<subproject>/` folder structure.
* **Dashboards:** Displays project‑ and subproject‑level statistics (file counts, token totals, byte sizes).
* **Token Estimation:** Generates `tokens.csv` summarizing token counts per transcript JSON.

---

## 📦 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/harizkrisha/transcript_scraper.git
   cd transcript_scraper
   ```

2. **Install system prerequisites:**

   * **Python 3.7+** and **pip**
   * **Tor** (for SOCKS5 proxy):

     * macOS (Homebrew):

       ```bash
       brew install tor
       brew services start tor
       ```
     * Ubuntu/Debian:

       ```bash
       sudo apt update && sudo apt install tor
       sudo systemctl enable --now tor
       ```
     * Windows:

       1. Download the Tor Expert Bundle from [https://www.torproject.org/download/](https://www.torproject.org/download/)
       2. Run `tor.exe` in a terminal.

3. **Export YouTube cookies (optional):**

   * Use a browser extension (e.g. **EditThisCookie**, **Cookie-Editor**) to export your YouTube session cookies in **Netscape** format as `cookies.txt` in the project root.

4. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` includes:

   ```text
   streamlit
   pysocks
   requests
   pytube
   youtube-transcript-api
   beautifulsoup4
   warcio
   langdetect
   tqdm
   PyMuPDF
   ```

---

## ⚙️ Usage

### 1. Launch the Streamlit App

```bash
streamlit run app.py
```

This opens a web UI at `http://localhost:8501` by default.

### 2. Project & Subproject Management (Sidebar)

1. **Select** an existing project or click **Add New Project** and enter a name.
2. Once a project is selected, **Select Subproject** or click **Add New Subproject**.
3. Your **Current Selection** drives where transcripts and reports are saved.

### 3. Scraper Mode (Default)

1. In **Mode → Scraper**, enter a **YouTube video** URL/ID or **playlist** URL/ID.
2. Click **Fetch Transcript**.
3. Transcript JSONs are saved under:

   ```text
   output/<project>/<subproject>/[<playlist_id>/]<video_id>.json
   ```

### 4. Dashboard Mode

1. Switch **Mode → Dashboard** in the sidebar.
2. **Project‑level stats**: shows total JSON files, sum of token counts, and total bytes per project.
3. **Subproject‑level stats**: similar breakdown per subproject.

---

## 🔧 Example Workflow

1. **Create** a project `MyYTTranscripts` and subproject `Tutorials`.
2. **Fetch** a single video:

   * Input `https://www.youtube.com/watch?v=ABC123XYZ` → saved as
     `output/MyYTTranscripts/Tutorials/ABC123XYZ.json`.
3. **Fetch** a playlist:

   * Input `https://youtube.com/playlist?list=PL12345` → folder
     `output/MyYTTranscripts/Tutorials/PL12345/…` with each video’s JSON.
4. **View stats** in **Dashboard**: see counts of files, tokens, and disk usage.
5. **Generate** `tokens.csv`: download a CSV of token counts for each JSON.

---

## 📜 Credits

This project was developed by:
- Hariz Krisha Muhammad
   - email: harizkrisha@gmail.com
   - github: harizkrisha

Additionally, this project was heavily inspired by the works of:
- NailFaaz
   - Email: nailfaaz2004@gmail.com
   - GitHub: Nailfaaz

