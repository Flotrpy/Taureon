import os
import uuid
import glob
import json
import subprocess
import re
import tempfile
import threading
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

jobs = {}


_cookies_tmp_path = None


def get_cookies_file():
    """Return a writable cookies.txt path for yt-dlp, or None.

    YTDLP_COOKIES is a path to an existing Netscape-format cookies file.
    YTDLP_COOKIES_CONTENT is the file's text (handy for hosts that only
    support environment variables).

    yt-dlp rewrites the cookies file after each run (to persist refreshed
    session cookies), so either source is copied once into a private,
    writable temp file on first use — hosts like Render mount secret files
    read-only, and using that path directly would fail on first request.
    """
    global _cookies_tmp_path
    if _cookies_tmp_path:
        return _cookies_tmp_path

    path = os.environ.get("YTDLP_COOKIES")
    content = os.environ.get("YTDLP_COOKIES_CONTENT")
    if path:
        with open(path, "r") as fh:
            content = fh.read()
    if not content:
        return None

    fd, tmp = tempfile.mkstemp(prefix="cookies-", suffix=".txt")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    _cookies_tmp_path = tmp
    return _cookies_tmp_path


def ytdlp_cmd(*args):
    """Start a yt-dlp command line, adding cookies when configured."""
    cmd = ["yt-dlp"]
    cookies = get_cookies_file()
    if cookies:
        cmd += ["--cookies", cookies]
    return cmd + list(args)


def parse_ytdlp_json(stdout):
    """Parse yt-dlp JSON output.

    With ``-j`` yt-dlp prints one JSON object per line. Some extractors
    emit multiple videos even with ``--no-playlist``, so stdout contains
    several objects and a plain ``json.loads`` raises "Extra data".
    Return the first valid object.
    """
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        return json.loads(line)
    raise ValueError("yt-dlp returned no data")


PROGRESS_RE = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")


def parse_progress(line):
    """Return the percent from a yt-dlp "[download]  45.3% of ..." line, or None."""
    m = PROGRESS_RE.search(line)
    return float(m.group(1)) if m else None


def build_download_cmd(out_template, url, format_choice, format_id):
    """Build the yt-dlp command line for a download job."""
    cmd = ytdlp_cmd("--newline", "--no-playlist", "-o", out_template)

    if format_choice == "audio":
        cmd += ["-x", "--audio-format", "mp3"]
    elif format_id:
        cmd += ["-f", f"{format_id}+bestaudio/best", "--merge-output-format", "mp4"]
    else:
        cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]

    cmd.append(url)
    return cmd


def run_download(job_id, url, format_choice, format_id):
    job = jobs[job_id]
    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")
    cmd = build_download_cmd(out_template, url, format_choice, format_id)

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        timed_out = []

        def on_timeout():
            timed_out.append(True)
            proc.kill()

        timer = threading.Timer(300, on_timeout)
        timer.start()
        last_line = ""
        try:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                last_line = line
                pct = parse_progress(line)
                if pct is not None:
                    job["progress"] = pct
            proc.wait()
        finally:
            timer.cancel()

        if timed_out:
            raise subprocess.TimeoutExpired(cmd, 300)
        if proc.returncode != 0:
            job["status"] = "error"
            job["error"] = last_line or "yt-dlp failed"
            return

        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
        if not files:
            job["status"] = "error"
            job["error"] = "Download completed but no file was found"
            return

        if format_choice == "audio":
            target = [f for f in files if f.endswith(".mp3")]
            chosen = target[0] if target else files[0]
        else:
            target = [f for f in files if f.endswith(".mp4")]
            chosen = target[0] if target else files[0]

        for f in files:
            if f != chosen:
                try:
                    os.remove(f)
                except OSError:
                    pass

        job["status"] = "done"
        job["file"] = chosen
        ext = os.path.splitext(chosen)[1]
        title = job.get("title", "").strip()
        # Sanitize title for filename
        if title:
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()[:100].strip()
            job["filename"] = f"{safe_title}{ext}" if safe_title else os.path.basename(chosen)
        else:
            job["filename"] = os.path.basename(chosen)
    except subprocess.TimeoutExpired:
        job["status"] = "error"
        job["error"] = "Download timed out (5 min limit)"
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    cmd = ytdlp_cmd("--no-playlist", "-j", url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip().split("\n")[-1]}), 400

        info = parse_ytdlp_json(result.stdout)

        # Build quality options — keep best format per resolution
        best_by_height = {}
        for f in info.get("formats", []):
            height = f.get("height")
            if height and f.get("vcodec", "none") != "none":
                tbr = f.get("tbr") or 0
                if height not in best_by_height or tbr > (best_by_height[height].get("tbr") or 0):
                    best_by_height[height] = f

        formats = []
        for height, f in best_by_height.items():
            formats.append({
                "id": f["format_id"],
                "label": f"{height}p",
                "height": height,
            })
        formats.sort(key=lambda x: x["height"], reverse=True)

        return jsonify({
            "title": info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration"),
            "uploader": info.get("uploader", ""),
            "formats": formats,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timed out fetching video info"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/playlist", methods=["POST"])
def get_playlist_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    cmd = ytdlp_cmd("--flat-playlist", "-J", url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip().split("\n")[-1]}), 400

        info = json.loads(result.stdout)
        entries = info.get("entries", [])
        urls = [entry.get("url") for entry in entries if entry.get("url")]
        return jsonify({"urls": urls})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timed out fetching playlist info"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    format_choice = data.get("format", "video")
    format_id = data.get("format_id")
    title = data.get("title", "")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    job_id = uuid.uuid4().hex[:10]
    jobs[job_id] = {"status": "downloading", "url": url, "title": title}

    thread = threading.Thread(target=run_download, args=(job_id, url, format_choice, format_id))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def check_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "status": job["status"],
        "error": job.get("error"),
        "filename": job.get("filename"),
        "progress": job.get("progress"),
    })


@app.route("/api/file/<job_id>")
def download_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "File not ready"}), 404
    return send_file(job["file"], as_attachment=True, download_name=job["filename"])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8899))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port)
