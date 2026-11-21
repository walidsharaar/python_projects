"""
YouTube -> MP3 batch downloader
================================

Reads video links from list.txt and saves each one as an MP3 in ./mp3/.

Use it ethically:
  * Only download videos you have the right to keep offline: your own uploads,
    Creative Commons / public-domain content, or content whose creator allows it.
    Downloading copyrighted music without permission can break YouTube's Terms of
    Service and copyright law in your country.
  * Files are for personal use. Don't re-upload or share them.
  * The script waits a few seconds between downloads so it doesn't hammer
    YouTube's servers, and it never downloads the same video twice.

Setup (one time):
    pip install yt-dlp imageio-ffmpeg
    # or install the real ffmpeg:  winget install Gyan.FFmpeg

Run:
    python download_mp3.py                 # uses list.txt, saves to ./mp3
    python download_mp3.py my_list.txt     # use a different list
"""

import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    import yt_dlp
except ImportError:
    sys.exit("yt-dlp is not installed. Run:  pip install yt-dlp imageio-ffmpeg")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "mp3"
ARCHIVE_FILE = BASE_DIR / "downloaded.txt"  # IDs of finished videos, so reruns skip them
AUDIO_QUALITY = "192"  # kbps


def find_ffmpeg() -> str | None:
    """Return a path to ffmpeg: system install first, then the pip package."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def video_id(url: str) -> str | None:
    """Get the 11-character video ID from youtu.be or youtube.com links."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        return parsed.path.lstrip("/").split("/")[0] or None
    if host in ("youtube.com", "music.youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            return parsed.path.split("/")[2]
    return None


def read_links(list_file: Path) -> list[str]:
    """Read list.txt, skip blank lines and comments, remove tracking params and duplicates."""
    clean_urls, seen = [], set()
    for line_no, line in enumerate(list_file.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        vid = video_id(line)
        if not vid:
            print(f"  [skip] line {line_no}: not a YouTube video link -> {line}")
            continue
        if vid in seen:
            print(f"  [skip] line {line_no}: duplicate of video {vid}")
            continue
        seen.add(vid)
        clean_urls.append(f"https://www.youtube.com/watch?v={vid}")  # drops the ?si= tracker
    return clean_urls


def main() -> None:
    list_file = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "list.txt"
    if not list_file.exists():
        sys.exit(f"List file not found: {list_file}")

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        sys.exit("ffmpeg not found. Run:  pip install imageio-ffmpeg   (or: winget install Gyan.FFmpeg)")

    print(f"Reading {list_file.name} ...")
    urls = read_links(list_file)
    print(f"{len(urls)} unique videos to process.\n")
    if not urls:
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    options = {
        "format": "bestaudio/best",
        "outtmpl": str(OUTPUT_DIR / "%(title)s [%(id)s].%(ext)s"),
        "restrictfilenames": False,
        "windowsfilenames": True,          # strip characters Windows doesn't allow
        "noplaylist": True,                # a link = one video, never a whole playlist
        "download_archive": str(ARCHIVE_FILE),
        "ignoreerrors": True,              # one bad video doesn't stop the batch
        "ffmpeg_location": ffmpeg,
        "sleep_interval": 3,               # be polite: wait 3-8 s between downloads
        "max_sleep_interval": 8,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": AUDIO_QUALITY},
            {"key": "FFmpegMetadata"},     # writes title/artist tags into the MP3
        ],
        "quiet": False,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        failed_count = ydl.download(urls)

    mp3_count = len(list(OUTPUT_DIR.glob("*.mp3")))
    print("\nDone.")
    print(f"  MP3 files in folder : {mp3_count}  ->  {OUTPUT_DIR}")
    if failed_count:
        print("  Some videos failed (private, removed, age/region-locked). See the errors above.")


if __name__ == "__main__":
    main()
