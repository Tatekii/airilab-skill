#!/usr/bin/env python3
"""
AiriLab API client.
Synchronous mode: submit and block until final result is ready.
"""

import json
import time
from typing import Any, Dict, List, Optional

import requests

try:
    from .auth import AiriLabAuth
    from .config import AiriLabConfig
    from .job_store import append_job_event, init_db as init_job_store, save_job as save_job_record
    from .upload import AiriLabUpload
except ImportError:  # pragma: no cover
    from auth import AiriLabAuth
    from config import AiriLabConfig
    from upload import AiriLabUpload
    try:
        from job_store import append_job_event, init_db as init_job_store, save_job as save_job_record
    except ImportError:  # pragma: no cover
        append_job_event = None
        init_job_store = None
        save_job_record = None


GENERATE_URL = "https://cn.airilab.com/api/Universal/Generate"
STATUS_URL_TEMPLATE = "https://cn.airilab.com/api/Universal/Job/{job_id}"
RESULT_URL = "https://cn.airilab.com/api/CrudRouters/getOneRecord"

WORKFLOW_MJ = 0
WORKFLOW_UPSCALE = 16
WORKFLOW_ATMOSPHERE = 13

SYNC_POLL_INTERVAL_SECONDS = 5
SYNC_TIMEOUT_SECONDS = 210

DEFAULT_HEADERS = {
    "accept": "text/plain",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "content-type": "application/json",
    "origin": "https://cn.airilab.com",
    "user-agent": "Mozilla/5.0",
}


class AiriLabAPI:
    """AiriLab API client."""

    def __init__(self, config: Optional[AiriLabConfig] = None):
        self.config = config or AiriLabConfig()
        self.auth = AiriLabAuth(self.config)
        self.upload = AiriLabUpload(self.config)

    def _ensure_ready(self) -> Dict[str, Any]:
        auth_result = self.auth.ensure_authenticated()
        if not auth_result["authenticated"]:
            return {
                "ready": False,
                "needs_auth": True,
                "needs_project": False,
                "token": None,
                "project": None,
                "message": auth_result["message"],
            }

        project = self.config.get_project()
        if not project:
            return {
                "ready": False,
                "needs_auth": False,
                "needs_project": True,
                "token": auth_result["token"],
                "project": None,
                "message": "需要先选择项目",
            }

        return {
            "ready": True,
            "needs_auth": False,
            "needs_project": False,
            "token": auth_result["token"],
            "project": project,
            "message": "就绪",
        }

    def _build_payload(
        self,
        workflow_id: int,
        project: Dict[str, Any],
        base_image: Optional[str] = None,
        prompt: str = "",
        reference_images: Optional[List[str]] = None,
        image_count: int = 4,
        **kwargs,
    ) -> Dict[str, Any]:
        if workflow_id == WORKFLOW_MJ:
            payload = {
                "model": 0,
                "orientation": 0,
                "imageRatio": 0,
                "referenceImage": [{"url": url, "type": 0} for url in (reference_images or [])[:3]]
                if reference_images
                else [],
                "prompt": prompt,
                "workflowId": WORKFLOW_MJ,
                "additionalPrompt": prompt,
                "designLibraryName": "No Style",
                "designLibraryId": 99,
                "firstTierName": "No Style",
                "firstTierId": 9999,
                "secondTierName": "No Style",
                "secondTierId": 9999,
                "styleId": 9999,
                "cameraViewName": "No Camera",
                "cameraViewId": 9999,
                "graphicStyleId": 9999,
                "atmosphereId": 99,
                "atmosphereType": "",
                "additionalNegativePrompt": "",
                "imageType": "",
                "inputFidelityLevel": 0,
                "controlLevel": 0,
                "baseImage": "",
                "maskImage": "",
                "originalImage": "",
                "initialCNImage": "",
                "horizontalPercentage": 0,
                "verticalPercentage": 0,
                "firstFrame": "",
                "imageTail": "",
                "videoPrompt": 0,
                "timeLapse": 0,
                "cameraSpeed": 0,
                "privateModel": "",
                "height": 0,
                "width": 0,
                "megapixels": 2.25,
                "angleIndex": 0,
                "imageCount": image_count,
                "language": "chs",
                "teamId": project["teamId"],
                "projectId": project["projectId"],
                "projectName": project["projectName"],
            }
        elif workflow_id == WORKFLOW_UPSCALE:
            payload = {
                "initialCNImage": None,
                "baseImage": base_image or "",
                "workflowId": WORKFLOW_UPSCALE,
                "additionalPrompt": "",
                "referenceImage": [],
                "designLibraryName": "No Style",
                "designLibraryId": 99,
                "firstTierName": "No Style",
                "firstTierId": 9999,
                "secondTierName": "No Style",
                "secondTierId": 9999,
                "styleId": 9999,
                "cameraViewName": "No Camera",
                "cameraViewId": 9999,
                "graphicStyleId": 9999,
                "atmosphereId": 99,
                "atmosphereType": "",
                "additionalNegativePrompt": "",
                "imageType": "",
                "inputFidelityLevel": 0,
                "controlLevel": 0,
                "maskImage": "",
                "originalImage": "",
                "horizontalPercentage": 0,
                "verticalPercentage": 0,
                "firstFrame": "",
                "imageTail": "",
                "videoPrompt": 0,
                "timeLapse": 0,
                "cameraSpeed": 0,
                "prompt": "",
                "privateModel": "",
                "height": kwargs.get("height", 816),
                "width": kwargs.get("width", 1288),
                "angleIndex": 0,
                "imageCount": 1,
                "language": "chs",
                "teamId": project["teamId"],
                "projectId": project["projectId"],
                "projectName": project["projectName"],
            }
        elif workflow_id == WORKFLOW_ATMOSPHERE:
            payload = {
                "workflowId": WORKFLOW_ATMOSPHERE,
                "baseImage": base_image or "",
                "prompt": prompt,
                "additionalPrompt": prompt,
                "referenceImage": [{"url": reference_images[0], "type": 0}]
                if reference_images and len(reference_images) > 0
                else [],
                "imageCount": image_count,
                "language": "chs",
                "teamId": project["teamId"],
                "projectId": project["projectId"],
                "projectName": project["projectName"],
                "initialCNImage": None,
                "designLibraryName": "No Style",
                "designLibraryId": 99,
                "firstTierName": "No Style",
                "firstTierId": 9999,
                "secondTierName": "No Style",
                "secondTierId": 9999,
                "styleId": 9999,
                "cameraViewName": "No Camera",
                "cameraViewId": 9999,
                "graphicStyleId": 9999,
                "atmosphereId": 99,
                "atmosphereType": "",
                "additionalNegativePrompt": "",
                "imageType": "",
                "inputFidelityLevel": 0,
                "controlLevel": 0,
                "maskImage": "",
                "originalImage": "",
                "horizontalPercentage": 0,
                "verticalPercentage": 0,
                "firstFrame": "",
                "imageTail": "",
                "videoPrompt": 0,
                "timeLapse": 0,
                "cameraSpeed": 0,
                "privateModel": "",
                "height": kwargs.get("height", 816),
                "width": kwargs.get("width", 1288),
                "angleIndex": 0,
            }
        else:
            payload = {
                "workflowId": workflow_id,
                "imageCount": image_count,
                "language": "chs",
                "teamId": project["teamId"],
                "projectId": project["projectId"],
                "projectName": project["projectName"],
            }
        return payload

    def _build_headers(self, token: str, project_id: int) -> Dict[str, str]:
        headers = DEFAULT_HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"
        headers["referer"] = f"https://cn.airilab.com/stdio/workspace/{project_id}"
        return headers

    @staticmethod
    def _normalize_status(raw_status: str) -> str:
        value = (raw_status or "").strip().lower()
        if value in {"completed", "success", "succeeded", "done", "api_count"}:
            return "completed"
        if value in {"failed", "failure", "error"}:
            return "failed"
        if value in {"processing", "running", "sending_now", "in_progress"}:
            return "processing"
        if value in {"queued", "pending", ""}:
            return "pending"
        return "pending"

    def _check_job_status(self, token: str, job_id: str) -> str:
        headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
        url = STATUS_URL_TEMPLATE.format(job_id=job_id)
        response = requests.get(url, headers=headers, timeout=30)
        result = response.json()
        if result.get("status") != 200:
            raise RuntimeError(f"status api error: {result.get('message', 'unknown')}")
        data = result.get("data", {})
        return self._normalize_status(str(data.get("status") or ""))

    def _fetch_result(self, token: str, project: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "projectId": project.get("projectId", 0),
            "teamId": project.get("teamId", 0),
            "language": "chs",
            "desiredGenerationId": job_id,
        }
        response = requests.post(RESULT_URL, headers=headers, json=payload, timeout=30)
        result = response.json()

        if result.get("status") != 200:
            return {
                "success": False,
                "output_urls": [],
                "thumbnail_url": None,
                "toolset": None,
                "message": f"API error: {result.get('message', 'Unknown')}",
            }

        data = result.get("data", {})
        models = data.get("projectGenerationModel", [])
        if not models:
            return {
                "success": False,
                "output_urls": [],
                "thumbnail_url": None,
                "toolset": None,
                "message": "No generation model found",
            }

        model = models[0]
        medias = model.get("projectMedias", [])
        if not medias:
            return {
                "success": False,
                "output_urls": [],
                "thumbnail_url": None,
                "toolset": None,
                "message": "No output media yet",
            }

        output_urls = [m.get("url", "") for m in medias if m.get("url")]
        thumbnail_url = output_urls[0] if output_urls else None

        workflow_name = model.get("workflowName", "unknown")
        workflow_head = workflow_name.split()[0] if workflow_name else ""
        toolset_map = {"MJ": "mj", "Upscale": "upscale", "Trans": "atmosphere"}

        return {
            "success": True,
            "output_urls": output_urls,
            "thumbnail_url": thumbnail_url,
            "toolset": toolset_map.get(workflow_head, "unknown"),
            "message": f"Fetched {len(output_urls)} image(s)",
        }

    def _wait_for_result(self, token: str, project: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        deadline = time.time() + SYNC_TIMEOUT_SECONDS
        last_status = "pending"

        while time.time() < deadline:
            status = self._check_job_status(token, job_id)
            last_status = status

            if append_job_event:
                append_job_event(job_id, "status_polled", f"Polled status: {status}")

            if status in {"pending", "processing"}:
                time.sleep(SYNC_POLL_INTERVAL_SECONDS)
                continue

            if status == "failed":
                return {
                    "success": False,
                    "status": status,
                    "message": "Job failed on server.",
                    "output_urls": [],
                    "thumbnail_url": None,
                    "toolset": None,
                }

            fetch_result = self._fetch_result(token, project, job_id)
            fetch_result["status"] = status
            return fetch_result

        return {
            "success": False,
            "status": last_status,
            "message": f"Timed out after {SYNC_TIMEOUT_SECONDS} seconds while waiting for result.",
            "output_urls": [],
            "thumbnail_url": None,
            "toolset": None,
        }

    def submit_task(self, workflow_id: int, **kwargs) -> Dict[str, Any]:
        if "payload" in kwargs:
            return {
                "success": False,
                "job_id": None,
                "message": "Invalid call: direct payload override is not allowed. Use _build_payload only.",
                "needs_auth": False,
                "needs_project": False,
                "round_complete": False,
                "notify_async": False,
            }

        ready = self._ensure_ready()
        if not ready["ready"]:
            return {
                "success": False,
                "job_id": None,
                "message": ready["message"],
                "needs_auth": ready["needs_auth"],
                "needs_project": ready["needs_project"],
                "round_complete": False,
                "notify_async": False,
            }

        payload = self._build_payload(workflow_id, ready["project"], **kwargs)
        headers = self._build_headers(token=ready["token"], project_id=ready["project"]["projectId"])

        try:
            response = requests.post(GENERATE_URL, headers=headers, json=payload, timeout=30)
            result = response.json()
            if result.get("status") != 200:
                return {
                    "success": False,
                    "job_id": None,
                    "message": result.get("message", "提交失败"),
                    "needs_auth": False,
                    "needs_project": False,
                    "round_complete": False,
                    "notify_async": False,
                }

            data = result.get("data", {})
            job_id = data.get("jobId")
            if not job_id:
                return {
                    "success": False,
                    "job_id": None,
                    "message": "Submit succeeded but jobId is missing.",
                    "needs_auth": False,
                    "needs_project": False,
                    "round_complete": False,
                    "notify_async": False,
                }

            if job_id and init_job_store and save_job_record:
                try:
                    init_job_store()
                    tool_map = {WORKFLOW_MJ: "mj", WORKFLOW_UPSCALE: "upscale", WORKFLOW_ATMOSPHERE: "atmosphere"}
                    user_id = str(kwargs.get("user_id") or kwargs.get("userId") or "unknown")
                    chat_id = str(kwargs.get("chat_id") or kwargs.get("chatId") or "unknown")
                    tool = str(kwargs.get("tool") or tool_map.get(workflow_id, "unknown"))
                    save_job_record(
                        job_id=job_id,
                        user_id=user_id,
                        chat_id=chat_id,
                        tool=tool,
                        input_params={"workflow_id": workflow_id, "payload": payload},
                    )
                    if append_job_event:
                        append_job_event(job_id, "submitted", "Job accepted by API (sync mode)")
                except Exception:
                    pass

            wait_result = self._wait_for_result(ready["token"], ready["project"], job_id)
            if not wait_result.get("success", False):
                return {
                    "success": False,
                    "job_id": job_id,
                    "message": f"Job finished without usable output: {wait_result.get('message', 'unknown')}",
                    "needs_auth": False,
                    "needs_project": False,
                    "round_complete": True,
                    "notify_async": False,
                    "status": wait_result.get("status"),
                    "output_urls": wait_result.get("output_urls", []),
                    "thumbnail_url": wait_result.get("thumbnail_url"),
                    "toolset": wait_result.get("toolset"),
                }

            return {
                "success": True,
                "job_id": job_id,
                "message": f"Job completed: {job_id}. Retrieved {len(wait_result.get('output_urls', []))} image(s).",
                "needs_auth": False,
                "needs_project": False,
                "round_complete": True,
                "notify_async": False,
                "status": wait_result.get("status", "completed"),
                "output_urls": wait_result.get("output_urls", []),
                "thumbnail_url": wait_result.get("thumbnail_url"),
                "toolset": wait_result.get("toolset"),
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "job_id": None,
                "message": f"Network error: {str(e)}",
                "needs_auth": False,
                "needs_project": False,
                "round_complete": False,
                "notify_async": False,
            }

    def mj_render(self, prompt: str, reference_images: Optional[List[str]] = None, image_count: int = 4) -> Dict[str, Any]:
        refs = reference_images or []
        if len(refs) > 3:
            return {
                "success": False,
                "job_id": None,
                "message": "MJ supports at most 3 reference images.",
                "needs_auth": False,
                "needs_project": False,
                "round_complete": False,
                "notify_async": False,
            }
        return self.submit_task(
            workflow_id=WORKFLOW_MJ,
            prompt=prompt,
            reference_images=refs,
            image_count=image_count,
        )

    def upscale(self, base_image: str, width: int = 1288, height: int = 816) -> Dict[str, Any]:
        return self.submit_task(
            workflow_id=WORKFLOW_UPSCALE,
            base_image=base_image,
            width=width,
            height=height,
        )

    def atmosphere_transform(
        self,
        base_image: str,
        prompt: str,
        reference_image: Optional[str] = None,
        image_count: int = 4,
    ) -> Dict[str, Any]:
        reference_images = [reference_image] if reference_image else None
        return self.submit_task(
            workflow_id=WORKFLOW_ATMOSPHERE,
            base_image=base_image,
            prompt=prompt,
            reference_images=reference_images,
            image_count=image_count,
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AiriLab API caller")
    parser.add_argument("--tool", required=True, choices=["mj", "upscale", "atmosphere"], help="Tool type")
    parser.add_argument("--prompt", help="Prompt text (for mj and atmosphere)")
    parser.add_argument("--base-image", help="Base image URL (for upscale and atmosphere)")
    parser.add_argument(
        "--reference-image",
        action="append",
        help="Reference image URL, repeat this option to pass multiple images",
    )
    parser.add_argument("--image-count", type=int, default=4, help="Number of images")

    args = parser.parse_args()
    reference_images = args.reference_image or []

    config = AiriLabConfig()
    api = AiriLabAPI(config)

    if args.tool == "mj":
        if not args.prompt:
            print("ERR MJ requires --prompt")
        elif len(reference_images) > 3:
            print("ERR MJ supports at most 3 reference images.")
        else:
            result = api.mj_render(args.prompt, reference_images=reference_images, image_count=args.image_count)
            if result["success"]:
                print(f"OK {result['message']}")
                for i, url in enumerate(result.get("output_urls", []), 1):
                    print(f"image{i}: {url}")
                if result.get("thumbnail_url"):
                    print(f"thumbnail: {result['thumbnail_url']}")
            else:
                print(f"ERR {result['message']}")

    elif args.tool == "upscale":
        if not args.base_image:
            print("ERR Upscale requires --base-image")
        else:
            result = api.upscale(args.base_image)
            if result["success"]:
                print(f"OK {result['message']}")
                for i, url in enumerate(result.get("output_urls", []), 1):
                    print(f"image{i}: {url}")
                if result.get("thumbnail_url"):
                    print(f"thumbnail: {result['thumbnail_url']}")
            else:
                print(f"ERR {result['message']}")

    elif args.tool == "atmosphere":
        if not args.base_image or not args.prompt:
            print("ERR Atmosphere requires --base-image and --prompt")
        elif len(reference_images) > 1:
            print("ERR Atmosphere supports at most 1 reference image.")
        else:
            result = api.atmosphere_transform(
                args.base_image,
                args.prompt,
                reference_image=reference_images[0] if reference_images else None,
                image_count=args.image_count,
            )
            if result["success"]:
                print(f"OK {result['message']}")
                for i, url in enumerate(result.get("output_urls", []), 1):
                    print(f"image{i}: {url}")
                if result.get("thumbnail_url"):
                    print(f"thumbnail: {result['thumbnail_url']}")
            else:
                print(f"ERR {result['message']}")
