# batch-toonify

[![Latest release](https://img.shields.io/github/v/release/prashm/batch-toonify)](https://github.com/prashm/batch-toonify/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/prashm/batch-toonify/total)](https://github.com/prashm/batch-toonify/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Turn a whole folder of real photos into cartoon illustrations, in one consistent style, using Google's
**Nano Banana Pro** (Gemini 3 Pro Image) model.

Consumer apps (Gemini, ChatGPT, and most "cartoon yourself" apps) convert **one photo at a time**, and the
style drifts from photo to photo. `batch-toonify` is a small Python command-line tool that converts
hundreds of photos with the same prompt and settings, and can use Google's **Batch API at half price**.

- **High quality:** uses Nano Banana Pro, which keeps people recognizable while changing the art style.
- **Bulk:** convert a whole folder, either instantly or through the Batch API for **~50% off**.
- **Consistent:** every photo gets the same prompt, resolution and settings.
- **Resumable:** photos that already have a cartoon are skipped, so you can stop, re-run and retry failures for free.
- **Phone-friendly:** reads iPhone `.heic` photos and fixes sideways phone photos automatically.
- **Works on macOS and Windows** (and Linux).

---

## Contents

- [How it works](#how-it-works)
- [What it costs](#what-it-costs)
- [Prerequisites](#prerequisites)
- [Step 1: Get a Gemini API key](#step-1-get-a-gemini-api-key)
- [Step 2: Setup on macOS](#step-2-setup-on-macos)
- [Step 2: Setup on Windows](#step-2-setup-on-windows)
- [Quick start](#quick-start)
- [Command reference](#command-reference)
- [Batch mode in detail](#batch-mode-in-detail)
- [Configuration](#configuration)
- [Prompt examples](#prompt-examples)
- [Troubleshooting](#troubleshooting)
- [Privacy](#privacy)
- [License](#license)

---

## How it works

```
input/                       prepare each photo                     Gemini API                output/
  IMG_0012.HEIC   ──►  rotate upright, convert to JPEG,   ──►  Nano Banana Pro    ──►  IMG_0012_cartoon.png
  beach.jpg            shrink to max 2048px                  + your style prompt      beach_cartoon.png
  ...                                                                                  ...
```

There are two ways to run a folder:

| Mode | Command | Speed | Price |
|---|---|---|---|
| **Instant** | `--bulk` | Results in seconds per photo | Full price |
| **Batch** | `--batch-submit`, then `--batch-fetch` | Google aims for under 24 hours (often much faster) | **About 50% off** |

Use `--test` on one photo to get the style right, then use batch mode for the rest.

## What it costs

You pay Google directly for each image. This tool itself is free. Approximate prices for Nano Banana Pro
at the time of writing:

| Output size | Instant (`--test`, `--bulk`) | Batch (`--batch-submit`) |
|---|---|---|
| 1K or 2K | ~$0.134 per image | ~$0.067 per image |
| 4K | not allowed by this tool (costs ~2x) | – |

So 100 photos cost roughly **$6.70 in batch mode** or $13.40 instantly. 1K and 2K cost the same, which is why
the default is 2K. Prices change, so check [Google's Gemini API pricing page](https://ai.google.dev/gemini-api/docs/pricing)
before large runs.

> **Cheaper option:** set `MODEL = "gemini-2.5-flash-image"` (the original "Nano Banana") in `config.py`.
> It costs much less per image, but quality and likeness are noticeably lower.

## Prerequisites

- **Python 3.10 or newer**
- **A Google account**
- **A Gemini API key on a project with billing enabled.** Nano Banana Pro is **not available on the free tier**.
  With a free-tier key every request fails with a `429 ... limit: 0` error. See [Troubleshooting](#troubleshooting).
- **Git** (optional; you can also download the code as a ZIP)

## Step 1: Get a Gemini API key

1. Go to **<https://aistudio.google.com/apikey>** and sign in with your Google account.
2. Click **Create API key** and copy it. Keep it secret, like a password.
3. On the same page, find the project your key belongs to and click **Set up billing**. Link or create a
   Google Cloud billing account.
4. Wait a few minutes for billing to take effect.

> Tip: set a budget alert in Google Cloud Billing so a large run can't surprise you.

## Step 2: Setup on macOS

Open **Terminal** (Applications → Utilities → Terminal) and run the commands below.

**1. Install Python 3.10+** if `python3 --version` shows an older version or "command not found".
Either download it from <https://www.python.org/downloads/>, or use Homebrew:

```bash
brew install python
```

**2. Download the code.** Easiest: go to the
**[latest release](https://github.com/prashm/batch-toonify/releases/latest)**, download
`batch-toonify-vX.Y.Z.zip` under **Assets**, double-click it to unzip, then in Terminal:

```bash
cd ~/Downloads/batch-toonify-vX.Y.Z
```

(Replace `X.Y.Z` with the version you downloaded.) Or, if you use git:

```bash
git clone https://github.com/prashm/batch-toonify.git
cd batch-toonify
```

**3. Create a virtual environment and install the dependencies:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Your prompt now starts with `(.venv)`. Run `source .venv/bin/activate` again whenever you open a new Terminal window.

**4. Add your API key:**

```bash
cp .env.example .env
open -e .env
```

Replace `your-key-here` with your key, then save. The line should look like `GEMINI_API_KEY=AIza...` with no quotes or spaces.

You're ready. Go to [Quick start](#quick-start).

## Step 2: Setup on Windows

Open **PowerShell** (Start menu → type "PowerShell"). The commands also work in Command Prompt unless noted.

**1. Install Python 3.10+** from <https://www.python.org/downloads/>.
On the first installer screen, **tick "Add python.exe to PATH"**. Alternatively, run:

```powershell
winget install Python.Python.3.12
```

Close and reopen PowerShell, then check that `py --version` works.

**2. Download the code.** Easiest: go to the
**[latest release](https://github.com/prashm/batch-toonify/releases/latest)**, download
`batch-toonify-vX.Y.Z.zip` under **Assets**, right-click it → **Extract All...**, then in PowerShell:

```powershell
cd $HOME\Downloads\batch-toonify-vX.Y.Z\batch-toonify-vX.Y.Z
```

(Windows' "Extract All" creates a folder inside a folder of the same name; replace `X.Y.Z` with the
version you downloaded.) Or, if you use git:

```powershell
git clone https://github.com/prashm/batch-toonify.git
cd batch-toonify
```

**3. Create a virtual environment and install the dependencies:**

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Your prompt now starts with `(.venv)`. Run `.venv\Scripts\activate` again whenever you open a new window.

> **"running scripts is disabled on this system"?** PowerShell blocks the activation script by default.
> Run this once, then try activating again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

**4. Add your API key:**

```powershell
copy .env.example .env
notepad .env
```

Replace `your-key-here` with your key, then save. The line should look like `GEMINI_API_KEY=AIza...` with no quotes or spaces.

You're ready. Go to [Quick start](#quick-start).

## Quick start

All commands are run from the project folder with the virtual environment active. They're the same on
macOS and Windows.

**1. Test one photo and tune the style.**

```bash
python cartoonize.py --test path/to/photo.jpg
```

The cartoon is saved to `output/photo_cartoon.png` and opens automatically. Try other styles without
editing any files:

```bash
python cartoonize.py --test path/to/photo.jpg --prompt "Turn this photo into a Pixar-style 3D cartoon. Keep each person's likeness."
```

Windows paths work too: `python cartoonize.py --test "C:\Users\me\Pictures\photo.jpg"`.

**2. Save the style you like.** Paste your favorite prompt into `PROMPT` in `config.py`.

**3. Put your photos in the `input/` folder** and submit them as a batch (half price):

```bash
python cartoonize.py --batch-submit
```

**4. Check back later** and download the results:

```bash
python cartoonize.py --batch-status
python cartoonize.py --batch-fetch
```

The cartoons appear in `output/`. If you'd rather not wait, use `python cartoonize.py --bulk` to convert
everything instantly at full price.

## Command reference

| Command | What it does |
|---|---|
| `python cartoonize.py --test PHOTO` | Converts one photo instantly and opens the result. Full price. |
| `python cartoonize.py --bulk [FOLDER]` | Converts every photo in `FOLDER` instantly (default `input/`), 3 at a time. Full price. |
| `python cartoonize.py --batch-submit [FOLDER]` | Submits every photo in `FOLDER` (default `input/`) as one Batch API job. ~50% off. |
| `python cartoonize.py --batch-status` | Shows the state of each submitted batch job. |
| `python cartoonize.py --batch-fetch` | Downloads results of finished batch jobs into `output/`. Safe to run any time. |
| `--prompt "..."` | Overrides the style prompt for `--test`, `--bulk` or `--batch-submit`. |
| `python cartoonize.py --help` | Shows all options. |

**Quoting:** wrap prompts and paths with spaces in **double quotes** (`"..."`). This works the same in
macOS Terminal, PowerShell and Command Prompt. Avoid single quotes, which Command Prompt doesn't understand.

**Supported input formats:** `.jpg`, `.jpeg`, `.png`, `.webp`, `.heic`, `.heif` (any capitalization).
Other files in the folder are ignored. Subfolders are not scanned.

**Output:** a PNG named `<original name>_cartoon.png` in `output/`.

## Batch mode in detail

1. **Submit:** `--batch-submit` prepares every photo (rotated upright, shrunk to 2048px, JPEG), packs them
   into one request file in `batch_work/`, uploads it to Google and starts a job. The job ID is saved in
   `batch_jobs.json`, so you can close the terminal or restart your computer.
2. **Wait:** Google's target is **24 hours**, and many jobs finish much sooner. A job that hasn't finished
   after **48 hours expires**.
3. **Fetch:** `--batch-fetch` downloads results for every finished job and saves the images. If a job is
   still running it says so and changes nothing, so it's safe to run whenever you like.

**Retries and resuming:**
- Running `--batch-submit` again only sends photos that **don't have a cartoon yet** and **aren't already
  in a job waiting to be fetched**. You never pay twice for the same photo.
- If some photos fail, `--batch-fetch` lists them with the reason; just run `--batch-submit` again to retry them.
- If a whole job fails or expires, its photos are released and the next `--batch-submit` picks them up.

**Changing the style for photos you've already converted:** the tool skips any photo that already has a
file in `output/`, whatever prompt made it. To redo them in a new style, rename or move the `output/`
folder first (e.g. to `output_style1/`).

## Configuration

All settings live in `config.py`:

| Setting | Default | Meaning |
|---|---|---|
| `MODEL` | `"gemini-3-pro-image-preview"` | Nano Banana Pro. Use `"gemini-2.5-flash-image"` for cheaper, lower-quality results. |
| `PROMPT` | a neutral cartoon prompt | The style instruction sent with every photo. Overridden by `--prompt`. |
| `IMAGE_SIZE` | `"2K"` | Output resolution: `"1K"` or `"2K"` (same price). 4K is blocked to avoid surprise costs. Ignored by the Flash model. |
| `ASPECT_RATIO` | `None` | `None` keeps each photo's own shape; or force one, e.g. `"1:1"`, `"4:3"`, `"16:9"`. |
| `INPUT_DIR` | `"input"` | Default folder for `--bulk` and `--batch-submit`. |
| `OUTPUT_DIR` | `"output"` | Where cartoons are saved. |
| `MAX_WORKERS` | `3` | How many photos `--bulk` converts at the same time. Lower it if you hit rate limits. |
| `MAX_RETRIES` | `3` | Retries for temporary errors (rate limits, server errors) in instant mode. |
| `MAX_INPUT_PX` | `2048` | Photos are shrunk so the longest side is at most this many pixels before upload. |
| `BATCH_STATE_FILE` | `"batch_jobs.json"` | Where submitted batch job IDs are tracked. |

## Prompt examples

The prompt is where most of the quality comes from. Always tell the model to **keep the person's likeness**.
Some starting points:

**Clean 2D cartoon (default)**
```
Convert this photo into a high-quality cartoon illustration. Keep each person's eye color, skin tone, hair color, facial features, pose and expression the same, and do not add, remove, or change any people. Do not add any text.
```

**3D animated movie style**
```
Turn this photo into a 3D animated movie character render with soft lighting and expressive features. Keep each person's likeness, hair, skin tone, clothing and pose. Do not add any text.
```

**Ghibli style** (the author's favorite; tested with great results)
```
Convert this photo into a ghibli cartoon. Make sure to maintain eye color, skin color, hair color and facial features. Make sure the photo subjects are not changed.
```

**Hand-drawn anime / watercolor film style**
```
Convert this photo into a hand-drawn anime film still with soft watercolor backgrounds and warm natural light. Maintain eye color, skin color, hair color and facial features. Make sure the photo subjects are not changed.
```

**Comic book**
```
Redraw this photo as a comic book panel with bold ink outlines, halftone shading and vibrant flat colors. Keep each person's likeness and pose. No speech bubbles or text.
```

**Pets**
```
Convert this pet photo into a cute cartoon illustration with bold outlines and flat colors. Keep the animal's breed, fur colors, markings and eye color exactly the same.
```

> **Selling the results?** Style names like "Pixar", "Disney" or "Studio Ghibli" work in prompts, but
> they're trademarks. Don't use them in product names, listings or marketing.

## Troubleshooting

**`429 RESOURCE_EXHAUSTED ... free_tier ... limit: 0`**
Your key's project doesn't have billing enabled, and the free tier allows zero Nano Banana Pro requests.
Enable billing (see [Step 1](#step-1-get-a-gemini-api-key)), wait a few minutes and try again. The tool
detects this case and stops with a short message instead of retrying.

**`API error 429, retrying in ...s` (without `free_tier`)**
This is a normal rate limit. The tool waits and retries automatically. If it keeps happening with `--bulk`,
lower `MAX_WORKERS` in `config.py` or switch to batch mode.

**`No API key found` / `API key not valid`**
The `.env` file is missing or wrong. It must be in the project folder, named exactly `.env` (not `.env.txt`;
on Windows, turn on "File name extensions" in File Explorer to check), and contain `GEMINI_API_KEY=your-key`.

**Windows: `'python' is not recognized` or the Microsoft Store opens**
Python isn't on your PATH. Use `py` instead of `python` to create the venv, or reinstall Python and tick
**"Add python.exe to PATH"**. After the venv is activated, `python` always works.

**Windows: `running scripts is disabled on this system`**
Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once in PowerShell, or use Command Prompt
and run `.venv\Scripts\activate.bat`.

**`ModuleNotFoundError: No module named 'google'` (or `PIL`, `dotenv`, `pillow_heif`)**
The virtual environment isn't active, or the dependencies weren't installed. Activate it (`source .venv/bin/activate`
on macOS, `.venv\Scripts\activate` on Windows), then run `pip install -r requirements.txt`.

**A photo fails with `no image returned (finish reason: ...)`**
Google's safety filters occasionally refuse an image (for example, some photos of children or with
sensitive content). Try a different prompt, or skip that photo.

**A batch job shows `JOB_STATE_EXPIRED` or `JOB_STATE_FAILED`**
Run `--batch-fetch` (it marks the job as finished), then `--batch-submit` to resubmit those photos.

**The result didn't open automatically after `--test`**
The cartoon is still saved; the path is printed in the terminal. Open it from the `output/` folder.

## Privacy

- Your photos are **sent to Google's Gemini API** to be converted. Read
  [Google's Gemini API terms](https://ai.google.dev/gemini-api/terms) to understand how paid-tier data is handled.
- Get consent before converting photos of other people, especially if you plan to share or sell the results.
- Your API key lives only in `.env`, which is git-ignored.
- `input/`, `output/`, `batch_work/` (which contains encoded copies of your photos) and `batch_jobs.json`
  are all git-ignored, so `git add` won't publish your photos. Delete `batch_work/` after your jobs are fetched
  if you don't want those copies kept on disk.

## Releasing (maintainers)

Releases are what users download, and GitHub counts every download of the attached zip
(shown in the badge at the top). To publish a new version on macOS/Linux with the
[GitHub CLI](https://cli.github.com/) installed and logged in (`gh auth login`):

```bash
./scripts/release.sh 1.0.0
```

The script checks you're on an up-to-date, committed `main`, builds `dist/batch-toonify-v1.0.0.zip`
from the committed files (excluding `scripts/`, `.gitignore`, `.gitattributes`), tags `v1.0.0` and
creates the GitHub Release with auto-generated notes. Download counts per release:

```bash
gh api repos/prashm/batch-toonify/releases --jq '.[] | .tag_name + ": " + ([.assets[].download_count] | add | tostring)'
```

## License

[MIT](LICENSE) © 2026 Prashant Mokkarala
