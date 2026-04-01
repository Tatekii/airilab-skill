#!/usr/bin/env python3
"""
AiriLab task status checker.

Always prints a machine-readable line in the form `status:<value>`.
"""

import json
import sys
from pathlib import Path

import requests

CONFIG_DIR = Path.home() / '.openclaw' / 'skills' / 'airilab' / 'config'
TOKEN_FILE = CONFIG_DIR / '.env'
PROJECT_FILE = CONFIG_DIR / 'project_config.json'
STATUS_URL = 'https://cn.airilab.com/api/CrudRouters/getOneRecord'


def get_token():
    if not TOKEN_FILE.exists():
        return None

    with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('AIRILAB_API_KEY='):
                return line.split('=', 1)[1].strip()
    return None


def get_project_config():
    if not PROJECT_FILE.exists():
        return None
    try:
        with open(PROJECT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def normalize_status(raw_status: str) -> str:
    value = (raw_status or '').strip().lower()
    if value in {'completed', 'success', 'succeeded', 'done'}:
        return 'completed'
    if value in {'failed', 'failure', 'error'}:
        return 'failed'
    if value in {'processing', 'running', 'sending_now'}:
        return 'processing'
    if value in {'queued', 'pending', ''}:
        return 'pending'
    return 'pending'


def check_status(job_id: str) -> str:
    token = get_token()
    if not token:
        print('error:missing_token')
        print('status:error')
        return 'error'

    project = get_project_config()
    if not project:
        print('error:missing_project')
        print('status:error')
        return 'error'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'projectId': project.get('projectId'),
        'teamId': project.get('teamId', 0),
        'language': 'chs',
        'desiredGenerationId': job_id,
    }

    try:
        response = requests.post(STATUS_URL, headers=headers, json=payload, timeout=30)
        result = response.json()

        if result.get('status') != 200:
            print(f"error:api_{result.get('message', 'unknown')}")
            print('status:error')
            return 'error'

        data = result.get('data', {})
        models = data.get('projectGenerationModel', [])
        if not models:
            print('status:pending')
            return 'pending'

        model = models[0]
        medias = model.get('projectMedias', [])
        if medias:
            print('status:completed')
            print(f'image_count:{len(medias)}')
            for i, media in enumerate(medias, 1):
                url = media.get('url')
                if url:
                    print(f'image{i}:{url}')
            return 'completed'

        raw_status = model.get('status') or model.get('generationStatus') or ''
        status = normalize_status(str(raw_status))
        print(f'status:{status}')
        return status

    except requests.exceptions.RequestException as e:
        print(f'error:network_{e}')
        print('status:error')
        return 'error'
    except Exception as e:
        print(f'error:unexpected_{e}')
        print('status:error')
        return 'error'


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Check task status')
    parser.add_argument('--job-id', required=True, help='Task job ID')
    args = parser.parse_args()

    status = check_status(args.job_id)
    sys.exit(0 if status != 'error' else 1)
