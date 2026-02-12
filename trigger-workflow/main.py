import os
import sys
import requests
import json 
import random

def set_env():
    github_api_url=os.environ["GITHUB_API_URL"]
    workflow_file=os.environ["INPUT_WORKFLOW_FILE"]
    repo=os.environ["INPUT_REPO"]
    owner=os.environ["INPUT_OWNER"]
    branch=os.environ["INPUT_BRANCH"]
    token=os.environ["INPUT_TOKEN"]
    raw_inputs=os.environ.get("INPUT_INPUTS", "{}")
    wait_until=os.environ("INPUT_WAIT_UNTIL")

    try:
        if not raw_inputs.strip():
            inputs = {}
        else:
            inputs = json.loads(raw_inputs)
    except json.JSONDecodeError:
        print(f"⚠️ Warning: input is not a valid JSON: {raw_inputs}")
        inputs = {}

    if wait_until == "true":
        random_numbers = [random.randint(1, 100) for _ in range(8)]
        print(f"Random integer: {random_numbers}")
        trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token,wait_until)
    else:
        trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token)



def trigger_workflow(github_api_url, workflow_file, repo, inputs, owner, branch, token):
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

    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        fh.write(f'myOutput={workflow_file}')
    
def wait_until();
    print("TeST")

if __name__ == "__main__":
    set_env()
