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
    wait_until=os.environ.get("INPUT_WAIT_UNTIL", "false")

    try:
        if not raw_inputs.strip():
            inputs = {}
        else:
            inputs = json.loads(raw_inputs)
    except json.JSONDecodeError:
        print(f"⚠️ Warning: input is not a valid JSON: {raw_inputs}")
        inputs = {}

    if wait_until == "true":
        random_numbers = random.randint(10000000, 99999999)
        print(f"Random integer: {random_numbers}")
        inputs["CorrelationID"] = f'{random_numbers}'
        print(inputs)
        trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token, wait_until)
    else:
        trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token)



def trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token, wait_until):
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

    if wait_until == "true":
        wait_for_workflow_completion(github_api_url, workflow_file, owner, repo, token, inputs["CorrelationID"])
    else:
        trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token)

    # with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
    #     fh.write(f'myOutput={workflow_file}')

def wait_for_workflow_completion(github_api_url, workflow_file, owner, repo, token, correlation_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    target_run_id = None
    list_url = f"{github_api_url}/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"

    print(f"🔍 Searching for run with Name: {correlation_id}...")

    # 1. FIND THE RUN (with retries)
    for attempt in range(15):  # Try for 30 seconds (15 * 2s)
        time.sleep(2)
        
        # Get recent runs triggered by 'workflow_dispatch'
        try:
            resp = requests.get(list_url, headers=headers, params={"per_page": 10, "event": "workflow_dispatch"})
            resp.raise_for_status() # Check for HTTP errors
            runs = resp.json().get("workflow_runs", [])
        except Exception as e:
            print(f"⚠️ API Error: {e}")
            continue

        # Look for the specific correlation ID in the run name
        for run in runs:
            # We use 'in' because sometimes GitHub adds a prefix or suffix
            if correlation_id in run['name'] or correlation_id in run['display_title']:
                target_run_id = run['id']
                print(f"✅ Found matching Run ID: {target_run_id}")
                break  # Break the inner loop (run search)
        
        if target_run_id:
            break  # Break the outer loop (retries)
        
        print(f"   Attempt {attempt+1}: Run not found yet...")

    # Check if we failed to find it after all retries
    if not target_run_id:
        print("❌ Timeout: Could not find the workflow run.")
        sys.exit(1)

    # 2. WAIT FOR COMPLETION
    print(f"🚀 Tracking status for Run ID: {target_run_id}")
    
    while True:
        status_url = f"{github_api_url}/repos/{owner}/{repo}/actions/runs/{target_run_id}"
        resp = requests.get(status_url, headers=headers)
        
        if resp.status_code != 200:
            print(f"❌ Error fetching status: {resp.text}")
            sys.exit(1)
            
        data = resp.json()
        status = data.get('status')       # queued, in_progress, completed
        conclusion = data.get('conclusion') # success, failure, cancelled
        
        print(f"⏳ Status: {status}")

        if status == "completed":
            if conclusion == "success":
                print("✅ Workflow finished successfully!")
                return
            else:
                print(f"❌ Workflow failed with conclusion: {conclusion}")
                sys.exit(1)
        
        time.sleep(5)

if __name__ == "__main__":
    set_env()
