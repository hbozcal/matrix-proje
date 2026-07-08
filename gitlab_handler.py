import asyncio
import requests
import config

async def create_issue(title, description, labels):
    gl_url = f"{config.GITLAB_URL}/api/v4/projects/{config.GITLAB_PROJECT_ID}/issues"
    gl_headers = {"PRIVATE-TOKEN": config.GITLAB_TOKEN}
    gl_payload = {"title": title, "description": description, "labels": labels}
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: requests.post(gl_url, headers=gl_headers, json=gl_payload, timeout=10))
    return response

async def add_comment(issue_iid, body):
    gl_url = f"{config.GITLAB_URL}/api/v4/projects/{config.GITLAB_PROJECT_ID}/issues/{issue_iid}/notes"
    gl_headers = {"PRIVATE-TOKEN": config.GITLAB_TOKEN}
    gl_payload = {"body": body}
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: requests.post(gl_url, headers=gl_headers, json=gl_payload, timeout=10))
    return response

async def close_issue(issue_iid):
    gl_url = f"{config.GITLAB_URL}/api/v4/projects/{config.GITLAB_PROJECT_ID}/issues/{issue_iid}"
    gl_headers = {"PRIVATE-TOKEN": config.GITLAB_TOKEN}
    gl_payload = {"state_event": "close"}
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: requests.put(gl_url, headers=gl_headers, json=gl_payload, timeout=10))
    return response