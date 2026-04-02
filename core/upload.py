#!/usr/bin/env python3
"""
AiriLab image upload client.
"""

from pathlib import Path
from typing import Dict

import requests

try:
    from .config import AiriLabConfig
except ImportError:  # pragma: no cover
    from config import AiriLabConfig

UPLOAD_URL = "https://cn.airilab.com/api/Workflow/UploadMedia"
QUOTA_EXCEEDED_STATUS = 203


class AiriLabUpload:
    """Upload media files to AiriLab storage."""

    def __init__(self, config: AiriLabConfig = None):
        self.config = config or AiriLabConfig()

    def upload_image(self, file_path: str, image_part: str = "base-image", team_id: int = 0) -> Dict[str, object]:
        token = self.config.get_token()
        if not token:
            return {
                "success": False,
                "url": None,
                "message": "Token not found. Please login first.",
            }

        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "url": None,
                "message": f"File not found: {path}",
            }

        try:
            with open(path, "rb") as f:
                files = {"myFile": (path.name, f, "image/jpeg")}
                data = {
                    "imagePart": image_part,
                    "teamId": str(team_id),
                }

                response = requests.post(
                    UPLOAD_URL,
                    headers={"Authorization": f"Bearer {token}"},
                    files=files,
                    data=data,
                    timeout=60,
                )
                result = response.json()

                status_code = result.get("status")
                backend_message = str(result.get("message", ""))

                if status_code == 200:
                    url = result.get("data", {}).get("path", "")
                    return {
                        "success": True,
                        "url": url,
                        "message": f"Upload succeeded: {url}",
                    }

                if status_code == QUOTA_EXCEEDED_STATUS or "generation limit exceeded" in backend_message.lower():
                    return {
                        "success": False,
                        "url": None,
                        "message": "Generation quota exceeded. Please top up or upgrade your plan before continuing.",
                    }

                return {
                    "success": False,
                    "url": None,
                    "message": f"Upload failed: {result}",
                }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "url": None,
                "message": f"Network error: {e}",
            }
        except Exception as e:
            return {
                "success": False,
                "url": None,
                "message": f"Upload error: {e}",
            }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AiriLab image upload")
    parser.add_argument("file", help="Path to image file")
    parser.add_argument(
        "--type",
        dest="image_type",
        default="base-image",
        choices=["base-image", "reference-image", "mask-image", "video-thumbnail"],
        help="Image part type",
    )
    parser.add_argument("--team-id", type=int, default=0, help="Team ID")

    args = parser.parse_args()

    config = AiriLabConfig()
    upload = AiriLabUpload(config)

    result = upload.upload_image(args.file, args.image_type, args.team_id)
    if result["success"]:
        print(f"OK {result['message']}")
    else:
        print(f"ERR {result['message']}")
