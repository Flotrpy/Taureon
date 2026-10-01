# RedoClip

A self-hosted, open-source video and audio downloader with a clean web UI. Paste links from sites like TikTok, Instagram, Twitter/X, Reddit and 1000+ others, then download them as MP4 (video) or MP3 (audio).

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

![RedoClip MP3 mode](assets/preview-mp3.png)

> RedoClip is a fork of [ReClip](https://github.com/averygan/reclip) by Avery Gan. See [Credits](#credits).

## What it does

- Downloads from 1000+ sites (powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp))
- MP4 video or MP3 audio
- Pick the quality or resolution
- Paste many links at once, duplicates are removed automatically
- Simple, responsive page with no frameworks and no build step

## Run it on your computer

You need **Python 3**, **yt-dlp** and **ffmpeg** installed.

1. Install the tools:
   - Mac: `brew install yt-dlp ffmpeg`
   - Linux: `sudo apt install ffmpeg` then `pip install yt-dlp`
   - Windows: install Python, then `pip install yt-dlp`, and install [ffmpeg](https://ffmpeg.org/download.html)
2. Get the code:
   ```bash
   git clone https://github.com/Flotrpy/redoclip.git
   cd redoclip
   ```
3. Start it:
   ```bash
   ./reclip.sh
   ```
4. Open **http://localhost:8899** in your browser.

### Run it with Docker instead

```bash
docker build -t redoclip . && docker run -p 8899:8899 redoclip
```

Then open **http://localhost:8899**.

## How to use it

1. Paste one or more video links into the box.
2. Choose **MP4** (video) or **MP3** (audio).
3. Click **Fetch** to load the thumbnails and info.
4. Pick a quality if you want to.
5. Click **Download** on one video, or **Download All**.

## Settings

You change these with environment variables:

| Variable | Default | What it does |
| --- | --- | --- |
| `PORT` | `8899` | The port the server uses. |
| `HOST` | `127.0.0.1` | Who can reach it. Use `0.0.0.0` so other devices on your network can open it. |
| `RECLIP_NO_UPDATE` | not set | Set to `1` to skip the yt-dlp update at startup. |

Example, so a phone or another computer on your Wi-Fi can use it:

```bash
HOST=0.0.0.0 ./reclip.sh
```

Then open `http://<your-computer-ip>:8899` on the other device.

> **Docker note:** the Docker image always listens on `0.0.0.0:8899`, so `PORT` and `HOST` are ignored there. To use a different port, change the left number in `-p`, for example `-p 9000:8899`. `RECLIP_NO_UPDATE` still works: `docker run -e RECLIP_NO_UPDATE=1 ...`.

## Put it online for free (Vercel + Render)

The page lives on **Vercel** and the downloader runs on **Render**. Both have free plans.

### Step 1: Render (the downloader)

1. Sign in at [render.com](https://render.com) with GitHub.
2. Click **New** then **Web Service**, and pick this repo.
3. Set **Language** to **Docker** and **Instance Type** to **Free**.
4. Click **Create Web Service** and wait for the build to finish.
5. Copy your Render address, which looks like `your-app.onrender.com`.

### Step 2: Vercel (the page)

1. Open `vercel.json` in this repo and replace the address after `https://` in the `destination` line with your Render address.
2. Sign in at [vercel.com](https://vercel.com) with GitHub and click **Add New** then **Project**.
3. Pick this repo. Leave **Framework Preset** as **Other** and click **Deploy**.
4. Open the address Vercel gives you.

### Good to know

- **The free Render plan sleeps** after about 15 minutes of no use. The first request afterwards can take around a minute.
- **YouTube and some other sites may block downloads** that come from cloud servers like Render. If that happens, run RedoClip on your own computer instead.
- **Downloaded files are temporary** on the free plan and disappear when the service restarts.

## For developers

Run the tests (they don't need yt-dlp or internet):

```bash
pip install flask
python -m unittest discover -s . -p "test_*.py" -t .
```

The server also has a `/health` endpoint that returns `{"status": "ok"}`, handy for uptime checks on Render or Docker.

## Supported sites

Anything [yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md), including TikTok, Instagram, Twitter/X, Reddit, Facebook, Vimeo, Twitch, Dailymotion, SoundCloud, Loom, Streamable, Pinterest, Tumblr, Threads, LinkedIn and many more.

## Built with

- **Backend:** Python and Flask
- **Frontend:** plain HTML, CSS and JavaScript in one file
- **Download engine:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [ffmpeg](https://ffmpeg.org/)

## Credits

RedoClip is built on top of **[ReClip](https://github.com/averygan/reclip)**, created by **Avery Gan** ([@averygan](https://github.com/averygan)). Thank you for making it open source.

Thanks also to the ReClip contributors, [@jouls0217](https://github.com/jouls0217) and [@AmanoSpica](https://github.com/AmanoSpica), and to the [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [ffmpeg](https://ffmpeg.org/) teams whose tools do the real work.

The original commit history is kept in this repo, so every contributor's work is still credited there.

## Disclaimer

This tool is for personal use only. Respect copyright laws and the terms of service of the sites you download from. The developers are not responsible for any misuse of this tool.

## License

[MIT](LICENSE). The original ReClip code stays under its MIT license, and the license text and copyright notice are kept as required.
