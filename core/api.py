#!/usr/bin/env python3
"""
AiriLab API 璋冪敤

鏁村悎鍘?api-list 鎶€鑳界殑鏍稿績鍔熻兘锛?
1. 鎻愪氦浠诲姟锛圡J 娓叉煋銆佸垱鎰忔斁澶с€佹皼鍥磋浆鎹級
2. 鑷姩澶勭悊璁よ瘉鍜岄」鐩厤缃?
3. 缁熶竴鐨勯敊璇鐞?
"""

import requests
import json
from typing import Dict, Any, List

try:
    from .config import AiriLabConfig
    from .auth import AiriLabAuth
    from .upload import AiriLabUpload
except ImportError:  # pragma: no cover
    from config import AiriLabConfig
    from auth import AiriLabAuth
    from upload import AiriLabUpload

try:
    from .job_store import append_job_event, init_db as init_job_store, save_job as save_job_record
except ImportError:  # pragma: no cover
    try:
        from job_store import append_job_event, init_db as init_job_store, save_job as save_job_record
    except ImportError:  # pragma: no cover
        append_job_event = None
        init_job_store = None
        save_job_record = None

# API 绔偣
GENERATE_URL = "https://cn.airilab.com/api/Universal/Generate"
WORKFLOW_MJ = 0
WORKFLOW_UPSCALE = 16
WORKFLOW_ATMOSPHERE = 13

# 璇锋眰澶存ā鏉?
DEFAULT_HEADERS = {
    "accept": "text/plain",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "content-type": "application/json",
    "origin": "https://cn.airilab.com",
    "user-agent": "Mozilla/5.0"
}


class AiriLabAPI:
    """AiriLab API client."""
    
    def __init__(self, config: AiriLabConfig = None):
        """
        鍒濆鍖?API 璋冪敤鍣?
        
        鍙傛暟:
            config: 閰嶇疆绠＄悊鍣ㄥ疄渚?
        """
        self.config = config or AiriLabConfig()
        self.auth = AiriLabAuth(self.config)
        self.upload = AiriLabUpload(self.config)
    
    def _ensure_ready(self) -> Dict[str, Any]:
        """
        纭繚宸插噯澶囧ソ锛堣璇?+ 椤圭洰閰嶇疆锛?
        
        杩斿洖:
            dict: {
                'ready': bool,
                'needs_auth': bool,
                'needs_project': bool,
                'token': str | None,
                'project': dict | None,
                'message': str
            }
        """
        # 妫€鏌ヨ璇?
        auth_result = self.auth.ensure_authenticated()
        
        if not auth_result['authenticated']:
            return {
                'ready': False,
                'needs_auth': True,
                'needs_project': False,
                'token': None,
                'project': None,
                'message': auth_result['message']
            }
        
        # 妫€鏌ラ」鐩厤缃?
        project = self.config.get_project()
        
        if not project:
            return {
                'ready': False,
                'needs_auth': False,
                'needs_project': True,
                'token': auth_result['token'],
                'project': None,
                'message': '闇€瑕侀€夋嫨椤圭洰'
            }
        
        return {
            'ready': True,
            'needs_auth': False,
            'needs_project': False,
            'token': auth_result['token'],
            'project': project,
            'message': '灏辩华'
        }
    
    def _build_payload(self, workflow_id: int, project: Dict[str, Any], 
                       base_image: str = None, prompt: str = "",
                       reference_images: List[str] = None, image_count: int = 4,
                       **kwargs) -> Dict[str, Any]:
        """
        鏋勫缓璇锋眰 payload
        
        鍙傛暟:
            workflow_id: 宸ヤ綔娴?ID
            project: 椤圭洰閰嶇疆
            base_image: 鍩哄浘 URL锛堝彲閫夛級
            prompt: 鎻愮ず璇嶏紙鍙€夛級
            reference_images: 鍙傝€冨浘 URL 鍒楄〃锛堝彲閫夛級
            image_count: 鐢熸垚鍥剧墖鏁伴噺
            **kwargs: 鍏朵粬鍙傛暟
        
        杩斿洖:
            dict: 璇锋眰 payload
        """
        # MJ 鍒涙剰娓叉煋宸ヤ綔娴?(workflowId: 0)
        if workflow_id == WORKFLOW_MJ:
            payload = {
                "model": 0,
                "orientation": 0,
                "imageRatio": 0,
                "referenceImage": [
                    {"url": url, "type": 0} for url in (reference_images or [])[:3]
                ] if reference_images else [],
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
                "teamId": project['teamId'],
                "projectId": project['projectId'],
                "projectName": project['projectName']
            }
        
        # 鍒涙剰鏀惧ぇ宸ヤ綔娴?(workflowId: 16)
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
                "height": kwargs.get('height', 816),
                "width": kwargs.get('width', 1288),
                "angleIndex": 0,
                "imageCount": 1,
                "language": "chs",
                "teamId": project['teamId'],
                "projectId": project['projectId'],
                "projectName": project['projectName']
            }
        
        # 姘涘洿杞崲宸ヤ綔娴?(workflowId: 13)
        elif workflow_id == WORKFLOW_ATMOSPHERE:
            payload = {
                "workflowId": WORKFLOW_ATMOSPHERE,
                "baseImage": base_image or "",
                "prompt": prompt,
                "additionalPrompt": prompt,
                "referenceImage": [
                    {"url": reference_images[0], "type": 0}
                ] if reference_images and len(reference_images) > 0 else [],
                "imageCount": image_count,
                "language": "chs",
                "teamId": project['teamId'],
                "projectId": project['projectId'],
                "projectName": project['projectName'],
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
                "height": kwargs.get('height', 816),
                "width": kwargs.get('width', 1288),
                "angleIndex": 0,
            }
        
        else:
            # 榛樿绠€鍖栫殑 payload
            payload = {
                "workflowId": workflow_id,
                "imageCount": image_count,
                "language": "chs",
                "teamId": project['teamId'],
                "projectId": project['projectId'],
                "projectName": project['projectName']
            }
        
        return payload

    def _build_headers(self, token: str, project_id: int) -> Dict[str, str]:
        headers = DEFAULT_HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"
        headers["referer"] = f"https://cn.airilab.com/stdio/workspace/{project_id}"
        return headers

    
    def submit_task(self, workflow_id: int, **kwargs) -> Dict[str, Any]:
        """
        鎻愪氦鐢熸垚浠诲姟
        
        鍙傛暟:
            workflow_id: 宸ヤ綔娴?ID (0=MJ, 16=鍒涙剰鏀惧ぇ锛?3=姘涘洿杞崲)
            **kwargs: 宸ヤ綔娴佺壒瀹氬弬鏁?
        
        杩斿洖:
            dict: {
                'success': bool,
                'job_id': str | None,
                'message': str,
                'needs_auth': bool,
                'needs_project': bool
            }
        """
        # Strong rule: callers must not pass payload directly.
        if 'payload' in kwargs:
            return {
                'success': False,
                'job_id': None,
                'message': 'Invalid call: direct payload override is not allowed. Use _build_payload only.',
                'needs_auth': False,
                'needs_project': False,
                'round_complete': False,
                'notify_async': False
            }

        # 纭繚宸插噯澶囧ソ
        ready = self._ensure_ready()
        
        if not ready['ready']:
            return {
                'success': False,
                'job_id': None,
                'message': ready['message'],
                'needs_auth': ready['needs_auth'],
                'needs_project': ready['needs_project'],
                'round_complete': False,
                'notify_async': False
            }
        
        # 鏋勫缓 payload
        payload = self._build_payload(
            workflow_id,
            ready['project'],
            **kwargs
        )
        
        # 鎻愪氦浠诲姟
        headers = self._build_headers(
            token=ready['token'],
            project_id=ready['project']['projectId']
        )
        
        try:
            response = requests.post(
                GENERATE_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("status") == 200:
                data = result.get("data", {})
                job_id = data.get("jobId")

                # Persist submission so background worker can pick up this job.
                if job_id and init_job_store and save_job_record:
                    try:
                        init_job_store()
                        tool_map = {
                            WORKFLOW_MJ: "mj",
                            WORKFLOW_UPSCALE: "upscale",
                            WORKFLOW_ATMOSPHERE: "atmosphere",
                        }
                        user_id = str(kwargs.get("user_id") or kwargs.get("userId") or "unknown")
                        chat_id = str(kwargs.get("chat_id") or kwargs.get("chatId") or "unknown")
                        tool = str(kwargs.get("tool") or tool_map.get(workflow_id, "unknown"))
                        input_params = {
                            "workflow_id": workflow_id,
                            "payload": payload,
                        }
                        save_job_record(
                            job_id=job_id,
                            user_id=user_id,
                            chat_id=chat_id,
                            tool=tool,
                            input_params=input_params,
                        )
                        if append_job_event:
                            append_job_event(
                                job_id,
                                "submitted",
                                "Job accepted by API and queued for worker polling",
                                details={"workflow_id": workflow_id, "tool": tool},
                            )
                    except Exception:
                        # Do not fail user-visible submit if local queue persistence fails.
                        pass
                
                return {
                    'success': True,
                    'job_id': job_id,
                    'message': f'Job submitted: {job_id}. This round is complete. You will be notified when background processing finishes.',
                    'needs_auth': False,
                    'needs_project': False,
                    'round_complete': True,
                    'notify_async': True
                }
            else:
                return {
                    'success': False,
                    'job_id': None,
                    'message': result.get('message', '鎻愪氦澶辫触'),
                    'needs_auth': False,
                    'needs_project': False,
                    'round_complete': False,
                    'notify_async': False
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'job_id': None,
                'message': f'Network error: {str(e)}',
                'needs_auth': False,
                'needs_project': False,
                'round_complete': False,
                'notify_async': False
            }
    
    # ==================== 蹇嵎鏂规硶 ====================
    
    def mj_render(self, prompt: str, reference_images: List[str] = None, 
                  image_count: int = 4) -> Dict[str, Any]:
        """
        鎻愪氦 MJ 鍒涙剰娓叉煋浠诲姟
        
        鍙傛暟:
            prompt: 鎻愮ず璇?
            reference_images: 鍙傝€冨浘 URL 鍒楄〃锛堟渶澶?3 寮狅級
            image_count: 鐢熸垚鍥剧墖鏁伴噺
        
        杩斿洖:
            dict: 鎻愪氦缁撴灉
        """
        return self.submit_task(
            workflow_id=WORKFLOW_MJ,
            prompt=prompt,
            reference_images=reference_images,
            image_count=image_count
        )
    
    def upscale(self, base_image: str, width: int = 1288, 
                height: int = 816) -> Dict[str, Any]:
        """
        鎻愪氦鍒涙剰鏀惧ぇ浠诲姟
        
        鍙傛暟:
            base_image: 鍩哄浘 URL
            width: 鐩爣瀹藉害
            height: 鐩爣楂樺害
        
        杩斿洖:
            dict: 鎻愪氦缁撴灉
        """
        return self.submit_task(
            workflow_id=WORKFLOW_UPSCALE,
            base_image=base_image,
            width=width,
            height=height
        )
    
    def atmosphere_transform(self, base_image: str, prompt: str,
                             reference_image: str = None,
                             image_count: int = 4) -> Dict[str, Any]:
        """
        鎻愪氦姘涘洿杞崲浠诲姟
        
        鍙傛暟:
            base_image: 鍩哄浘 URL
            prompt: 姘涘洿鎻忚堪
            reference_image: 鍙傝€冨浘 URL锛堟渶澶?1 寮狅級
            image_count: 鐢熸垚鍥剧墖鏁伴噺
        
        杩斿洖:
            dict: 鎻愪氦缁撴灉
        """
        reference_images = [reference_image] if reference_image else None
        
        return self.submit_task(
            workflow_id=WORKFLOW_ATMOSPHERE,
            base_image=base_image,
            prompt=prompt,
            reference_images=reference_images,
            image_count=image_count
        )


# ==================== 鍛戒护琛屽叆鍙?====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AiriLab API 璋冪敤")
    parser.add_argument("--tool", required=True, 
                       choices=["mj", "upscale", "atmosphere"],
                       help="宸ュ叿绫诲瀷")
    parser.add_argument("--prompt", help="Prompt text (for mj and atmosphere)")
    parser.add_argument("--base-image", help="Base image URL (for upscale and atmosphere)")
    parser.add_argument("--image-count", type=int, default=4, help="鐢熸垚鍥剧墖鏁伴噺")
    
    args = parser.parse_args()
    
    config = AiriLabConfig()
    api = AiriLabAPI(config)
    
    if args.tool == "mj":
        if not args.prompt:
            print("鉂?閿欒锛歁J 妯″紡闇€瑕?--prompt 鍙傛暟")
        else:
            result = api.mj_render(args.prompt, image_count=args.image_count)
            if result['success']:
                print(f"鉁?{result['message']}")
            else:
                print(f"鉂?{result['message']}")
    
    elif args.tool == "upscale":
        if not args.base_image:
            print("鉂?閿欒锛氬垱鎰忔斁澶ч渶瑕?--base-image 鍙傛暟")
        else:
            result = api.upscale(args.base_image)
            if result['success']:
                print(f"鉁?{result['message']}")
            else:
                print(f"鉂?{result['message']}")
    
    elif args.tool == "atmosphere":
        if not args.base_image or not args.prompt:
            print("鉂?閿欒锛歛tmosphere 闇€瑕?--base-image 鍜?--prompt 鍙傛暟")
        else:
            result = api.atmosphere_transform(
                args.base_image,
                args.prompt,
                image_count=args.image_count
            )
            if result['success']:
                print(f"鉁?{result['message']}")
            else:
                print(f"鉂?{result['message']}")
