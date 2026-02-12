import os
import requests  # noqa We are just importing this to prove the dependency installed correctly


def main():
    workflow_file = os.environ["INPUT_WORKFLOW_FILE"]

    my_output = f"The workflow file {workflow_file}"

    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        fh.write(f'myOutput={workflow_file}')


if __name__ == "__main__":
    main()