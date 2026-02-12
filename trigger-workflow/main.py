import os
import sys
import requests  # noqa We are just importing this to prove the dependency installed correctly


def main():
    workflow_file = os.environ["INPUT_WORKFLOW_FILE"]
    repo=os.environ["INPUT_REPO"]
    inputs=os.environ["INPUT_INPUTS"]
    owner=os.environ["INPUT_OWNER"]
    branch=os.environ["INPUT_BRANCH"]
    token=os.environ["INPUT_TOKEN"]

    headers={
        "Authorization" : f"Bearer {token}",
        "Accept"        : "application/vnd.github+json"
    }
    data = {
        "ref"       : f'{branch}',
        "inputs"    : f'{inputs}'
    }


    try:
        response = requests.post(f'$GITHUB_API_URL/{owner}/{repo}/workflows/{workflow_file}/dispatches',json=headers, data=data)
        
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


if __name__ == "__main__":
    main()

