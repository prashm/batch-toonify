"""Convert photos to cartoons with Gemini (Nano Banana Pro).

Usage (use `python3` instead of `python` on macOS if the venv isn't active):
    python cartoonize.py --test path/to/photo.jpg [--prompt "..."]   # instant, full price
    python cartoonize.py --bulk [input_dir] [--prompt "..."]         # instant, full price
    python cartoonize.py --batch-submit [input_dir] [--prompt "..."] # Batch API, 50% off, <=24h
    python cartoonize.py --batch-status
    python cartoonize.py --batch-fetch
"""

import argparse
import base64
import io
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

import config

register_heif_opener()  # lets Pillow open iPhone .heic/.heif photos

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

# Inputs are the user's own photos, so allow very large ones (e.g. 100+ MP panoramas)
# without Pillow's decompression-bomb warning.
Image.MAX_IMAGE_PIXELS = None

load_dotenv()
if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
    sys.exit("No API key found. Copy .env.example to .env in this folder and set "
             "GEMINI_API_KEY=your-key (see README.md, Step 1).")
client = genai.Client()  # reads GEMINI_API_KEY from the environment


def output_path_for(src: Path) -> Path:
    return Path(config.OUTPUT_DIR) / f"{src.stem}_cartoon.png"


def build_config() -> types.GenerateContentConfig:
    image_config = {}
    if "pro" in config.MODEL:  # image_size is only supported by the Pro model
        image_config["image_size"] = config.IMAGE_SIZE
    if config.ASPECT_RATIO:
        image_config["aspect_ratio"] = config.ASPECT_RATIO
    return types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        image_config=types.ImageConfig(**image_config) if image_config else None,
    )


def prepare_jpeg(src: Path) -> bytes:
    """Fix phone-photo rotation, convert to RGB (handles HEIC/PNG alpha), downscale, encode JPEG."""
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    img.thumbnail((config.MAX_INPUT_PX, config.MAX_INPUT_PX))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()


def is_quota_blocked(e: errors.APIError) -> bool:
    """True for quota errors that retrying won't fix (e.g. free tier with limit 0)."""
    return e.code == 429 and "free_tier" in str(e)


def convert_one(src: Path, prompt: str) -> Path:
    """Cartoonize one image and return the saved output path."""
    img = types.Part.from_bytes(data=prepare_jpeg(src), mime_type="image/jpeg")
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=config.MODEL,
                contents=[prompt, img],
                config=build_config(),
            )
            break
        except errors.APIError as e:
            if is_quota_blocked(e):
                raise
            retryable = e.code == 429 or (e.code or 0) >= 500
            if not retryable or attempt == config.MAX_RETRIES:
                raise
            wait = 2**attempt * 5
            print(f"  {src.name}: API error {e.code}, retrying in {wait}s...")
            time.sleep(wait)

    for part in (response.parts or []):
        if part.inline_data and part.inline_data.data:
            out = output_path_for(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            Image.open(io.BytesIO(part.inline_data.data)).save(out, "PNG")
            return out

    reason = response.candidates[0].finish_reason if response.candidates else "no candidates"
    raise RuntimeError(f"no image returned (finish reason: {reason})")


# ---------- Batch API ----------

DONE_STATES = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}


def load_state() -> dict:
    path = Path(config.BATCH_STATE_FILE)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_state(state: dict) -> None:
    Path(config.BATCH_STATE_FILE).write_text(json.dumps(state, indent=2), encoding="utf-8")


def encode_for_batch(src: Path) -> str:
    """Return the prepared image as base64 JPEG."""
    return base64.b64encode(prepare_jpeg(src)).decode()


def batch_generation_config() -> dict:
    image_config = {"imageSize": config.IMAGE_SIZE}
    if config.ASPECT_RATIO:
        image_config["aspectRatio"] = config.ASPECT_RATIO
    return {"responseModalities": ["IMAGE"], "imageConfig": image_config}


def run_batch_submit(input_dir: str, prompt: str) -> None:
    state = load_state()
    pending = {str(p) for job in state.values() if not job.get("fetched") for p in job["keys"].values()}
    sources = sorted(p for p in Path(input_dir).iterdir() if p.suffix.lower() in IMAGE_EXTS)
    todo = [p for p in sources if not output_path_for(p).exists() and str(p) not in pending]
    print(f"Found {len(sources)} images, {len(sources) - len(todo)} already done or in a pending batch, "
          f"{len(todo)} to submit.")
    if not todo:
        return

    work = Path("batch_work")
    work.mkdir(exist_ok=True)
    jsonl = work / f"requests_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    keys = {}
    with jsonl.open("w", encoding="utf-8") as f:
        for i, src in enumerate(todo):
            key = f"img-{i:05d}"
            keys[key] = str(src)
            request = {
                "contents": [{"parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": encode_for_batch(src)}},
                ]}],
                "generation_config": batch_generation_config(),
            }
            f.write(json.dumps({"key": key, "request": request}) + "\n")
    print(f"Wrote {jsonl} ({jsonl.stat().st_size / 1e6:.1f} MB), uploading...")

    uploaded = client.files.upload(file=str(jsonl), config=types.UploadFileConfig(mime_type="jsonl"))
    job = client.batches.create(model=config.MODEL, src=uploaded.name,
                                config={"display_name": f"cartoonize-{jsonl.stem}"})
    state[job.name] = {"created": time.strftime("%Y-%m-%d %H:%M:%S"), "count": len(keys),
                       "image_size": config.IMAGE_SIZE, "keys": keys, "fetched": False}
    save_state(state)
    print(f"Submitted batch job {job.name} with {len(keys)} images.")
    print("Check progress with --batch-status; download results with --batch-fetch (usually within 24h).")


def run_batch_status() -> None:
    state = load_state()
    if not state:
        print("No batch jobs submitted yet.")
        return
    for name, info in state.items():
        job = client.batches.get(name=name)
        fetched = " (fetched)" if info.get("fetched") else ""
        print(f"{name}: {job.state.name}{fetched}, {info['count']} images, submitted {info['created']}")


def extract_image(response: dict) -> bytes | None:
    for cand in response.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            data = part.get("inlineData") or part.get("inline_data")
            if data and data.get("data"):
                return base64.b64decode(data["data"])
    return None


def run_batch_fetch() -> None:
    state = load_state()
    for name, info in state.items():
        if info.get("fetched"):
            continue
        job = client.batches.get(name=name)
        if job.state.name not in DONE_STATES:
            print(f"{name}: still {job.state.name}, try again later.")
            continue
        if job.state.name != "JOB_STATE_SUCCEEDED":
            print(f"{name}: ended as {job.state.name}; its images can be resubmitted with --batch-submit.")
            info["fetched"] = True
            continue

        content = client.files.download(file=job.dest.file_name)
        ok, failed = 0, []
        for line in content.decode("utf-8").splitlines():
            if not line.strip():
                continue
            result = json.loads(line)
            src = Path(info["keys"].get(result.get("key"), result.get("key", "?")))
            data = extract_image(result.get("response", {}))
            if data is None:
                failed.append(f"{src.name} ({result.get('error') or 'no image returned'})")
                continue
            out = output_path_for(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            Image.open(io.BytesIO(data)).save(out, "PNG")
            ok += 1
        info["fetched"] = True
        print(f"{name}: saved {ok} images to {config.OUTPUT_DIR}/, {len(failed)} failed.")
        for f in failed:
            print(f"  FAIL {f}")
        if failed:
            print("  Run --batch-submit again to retry the failed images.")
    save_state(state)


def run_test(path: str, prompt: str) -> None:
    src = Path(path)
    print(f"Converting {src} with {config.MODEL}...")
    out = convert_one(src, prompt)
    print(f"Saved: {out}")
    open_file(out)


def open_file(path: Path) -> None:
    """Open the result in the OS's default image viewer; never fail the run if that's not possible."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception:
        pass


def run_bulk(input_dir: str, prompt: str) -> None:
    sources = sorted(p for p in Path(input_dir).iterdir() if p.suffix.lower() in IMAGE_EXTS)
    todo = [p for p in sources if not output_path_for(p).exists()]
    skipped = len(sources) - len(todo)
    print(f"Found {len(sources)} images, {skipped} already done, {len(todo)} to convert.")

    ok, failed = 0, []
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as pool:
        futures = {pool.submit(convert_one, p, prompt): p for p in todo}
        for fut in as_completed(futures):
            src = futures[fut]
            try:
                print(f"  OK   {src.name} -> {fut.result()}")
                ok += 1
            except Exception as e:
                print(f"  FAIL {src.name}: {e}")
                failed.append(src.name)

    print(f"\nDone: {ok} converted, {skipped} skipped, {len(failed)} failed.")
    if failed:
        print("Failed files:", ", ".join(failed))


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert photos to cartoons with Gemini.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--test", metavar="IMAGE", help="convert a single image and open it")
    mode.add_argument("--bulk", nargs="?", const=config.INPUT_DIR, metavar="DIR",
                      help=f"convert every image in DIR (default: {config.INPUT_DIR})")
    mode.add_argument("--batch-submit", nargs="?", const=config.INPUT_DIR, metavar="DIR",
                      help="submit every image in DIR as a Batch API job (50%% cheaper, up to 24h)")
    mode.add_argument("--batch-status", action="store_true", help="show the state of submitted batch jobs")
    mode.add_argument("--batch-fetch", action="store_true", help="download results of finished batch jobs")
    parser.add_argument("--prompt", default=config.PROMPT, help="override the style prompt")
    args = parser.parse_args()

    try:
        if args.test:
            run_test(args.test, args.prompt)
        elif args.bulk:
            run_bulk(args.bulk, args.prompt)
        elif args.batch_submit:
            run_batch_submit(args.batch_submit, args.prompt)
        elif args.batch_status:
            run_batch_status()
        else:
            run_batch_fetch()
    except errors.APIError as e:
        if is_quota_blocked(e):
            sys.exit(
                f"Quota error: your API key is on the Gemini free tier, which doesn't allow "
                f"{config.MODEL}.\nEnable billing for the key's project at "
                f"https://aistudio.google.com/apikey, then try again."
            )
        sys.exit(f"API error {e.code}: {e.message}")


if __name__ == "__main__":
    main()
