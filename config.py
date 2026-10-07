"""All settings for the photo -> cartoon converter."""

# Nano Banana Pro. Use "gemini-2.5-flash-image" (Nano Banana) for cheaper/faster runs.
MODEL = "gemini-3-pro-image-preview"
#MODEL = "gemini-2.5-flash-image"

# The style instruction sent with every photo. See README.md for more style examples.
PROMPT = (
    "Convert this photo into a high-quality cartoon illustration. Keep each person's eye color, "
    "skin tone, hair color, facial features, pose and expression the same, and do not add, "
    "remove, or change any people. Do not add any text."
)

# Output resolution: "1K" or "2K" (same price; 4K costs ~2x and is not allowed here).
IMAGE_SIZE = "2K"
assert IMAGE_SIZE in ("1K", "2K"), "IMAGE_SIZE must be '1K' or '2K'"

# None keeps the input's aspect ratio; otherwise e.g. "1:1", "4:3", "16:9".
ASPECT_RATIO = None

INPUT_DIR = "input"
OUTPUT_DIR = "output"
MAX_WORKERS = 3
MAX_RETRIES = 3

# Inputs are downscaled so the longest side is at most this many pixels before upload.
MAX_INPUT_PX = 2048

# Batch API (50% cheaper, results within ~24h).
BATCH_STATE_FILE = "batch_jobs.json"
