"""Deploy the repo to a Hugging Face Space via the hub upload API.

Used by .github/workflows/deploy.yml. Uploads the working tree as a single commit to
``HF_SPACE_ID`` using ``HF_TOKEN``. Prefers the commit API over ``git push`` because the
git-over-HTTPS endpoint rate-limits (429) aggressively under frequent deploys.

Exits 0 (no-op) when credentials are absent, so the workflow stays green pre-setup.
Retries with backoff on transient HTTP errors.
"""

from __future__ import annotations

import os
import sys
import time

IGNORE = [
    ".git*",
    ".github/*",
    ".venv/*",
    "**/__pycache__/*",
    "*.pyc",
    ".ruff_cache/*",
    ".pytest_cache/*",
    ".env*",
    "tests/*",
    "scripts/*",
    "handover.md",
    "DESIGN_BRIEF.md",
    "uv.lock",
]


def main() -> int:
    token = os.environ.get("HF_TOKEN")
    space_id = os.environ.get("HF_SPACE_ID")
    if not token or not space_id:
        print("::notice::HF_TOKEN or HF_SPACE_ID not set; skipping deploy.")
        return 0

    from huggingface_hub import HfApi
    from huggingface_hub.utils import HfHubHTTPError

    api = HfApi(token=token)
    sha = os.environ.get("GITHUB_SHA", "local")[:7]

    delay = 15
    for attempt in range(1, 6):
        try:
            api.upload_folder(
                repo_id=space_id,
                repo_type="space",
                folder_path=".",
                ignore_patterns=IGNORE,
                commit_message=f"Deploy {sha}",
            )
            print(f"Uploaded to Space {space_id} on attempt {attempt}.")
            return 0
        except HfHubHTTPError as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if attempt == 5 or status not in (429, 500, 502, 503, 504):
                print(f"::error::Upload failed ({status}): {exc}")
                return 1
            print(f"::warning::Upload attempt {attempt} failed ({status}); retrying in {delay}s.")
            time.sleep(delay)
            delay *= 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
