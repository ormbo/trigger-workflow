import os
import sys
import requests
import json 
import random
import time

def set_env():
    github_api_url=os.environ["GITHUB_API_URL"]
    workflow_file=os.environ["INPUT_WORKFLOW_FILE"]
    repo=os.environ["INPUT_REPO"]
    owner=os.environ["INPUT_OWNER"]
    branch=os.environ["INPUT_BRANCH"]
    token=os.environ["INPUT_TOKEN"]
    raw_inputs=os.environ.get("INPUT_INPUTS", "{}")
    wait_until_complete=os.environ.get("INPUT_WAIT_UNTIL_COMPLETE", "false")
    correlation_id=os.environ.get("INPUT_CORRELATION_ID")

    try:
        if not raw_inputs.strip():
            inputs = {}
        else:
            inputs = json.loads(raw_inputs)
    except json.JSONDecodeError:
        print(f"⚠️ Warning: input is not a valid JSON: {raw_inputs}")
        inputs = {}

    if wait_until_complete == "true" and not correlation_id:
        print("⚠️ No CorrelationID provided. Generating a random one for tracking...")
        random_numbers = random.randint(10000000, 99999999)
        inputs["correlation_id"] = f'{random_numbers}'
    elif wait_until_complete == "true" and correlation_id:
        inputs["correlation_id"] = correlation_id
        print(f"🔖 Using provided CorrelationID: {correlation_id} for tracking.")

    trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token, wait_until_complete)



def trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token, wait_until_complete):
    headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28" 
    }
    data = {
        "ref"       : branch,
        "inputs"    : inputs
    }

    url=f'{github_api_url}/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches'

    try:
        print(f"🚀 Triggering: {url}")
        response = requests.post(f'{url}',headers=headers, json=data)
        
        if response.status_code == 204:
            print("✅ Workflow triggered successfully!")
        else:
            print(f"❌ Failed to trigger workflow. Status: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending request: {e}")
        sys.exit(1)

    if wait_until_complete == "true":
        wait_for_workflow_completion(github_api_url, workflow_file, owner, repo, branch, token, inputs["correlation_id"])
    else:
        trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token)


def wait_for_workflow_completion(github_api_url, workflow_file, owner, repo, branch, token, correlation_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    target_run_id = None
    list_url = f"{github_api_url}/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"

    print(f"🔍 Searching for run with Name: {correlation_id}...")

    for attempt in range(15):  # Try for 30 seconds (15 * 2s)
        time.sleep(2)
        

        try:
            resp = requests.get(list_url, headers=headers, params={"per_page": 10, "event": "workflow_dispatch", "branch":f'{branch}'})
            resp.raise_for_status() # Check for HTTP errors
            runs = resp.json().get("workflow_runs", [])
        except Exception as e:
            print(f"⚠️ API Error: {e}")
            continue

        for run in runs:
            if correlation_id in run['name'] or correlation_id in run['display_title']:
                target_run_id = run['id']
                print(f"✅ Found matching Run ID: {target_run_id}")
                break 
        
        if target_run_id:
            break
        
        print(f"   Attempt {attempt+1}: Run not found yet...")

    if not target_run_id:
        print("❌ Timeout: Could not find the workflow run.")
        sys.exit(1)

    print(f"👀 Tracking status for Run ID: {target_run_id}")
    
    while True:
        status_url = f"{github_api_url}/repos/{owner}/{repo}/actions/runs/{target_run_id}"
        resp = requests.get(status_url, headers=headers)
        
        if resp.status_code != 200:
            print(f"❌ Error fetching status: {resp.text}")
            sys.exit(1)
            
        data = resp.json()
        status = data.get('status')
        conclusion = data.get('conclusion')
        
        print(f"⏳ Status: {status}")

        if status == "completed":
            if conclusion == "success":
                print("✅ Workflow finished successfully!")
                return
            else:
                print(f"❌ Workflow failed with conclusion: {conclusion}")
                sys.exit(1)
        
        time.sleep(10)

if __name__ == "__main__":
    set_env()
