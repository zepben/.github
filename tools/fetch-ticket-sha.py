import os
import re
import subprocess


def fetch_ticket_or_sha() -> str:
    # Clickup Ticket regex
    regex = r"(PROJ|EWB|EDNAR|BD|DEV|OPS|SUPPORT)-[0-9]{1,5}"

    # Detect TaskID
    github_ref = os.environ.get("GITHUB_REF", "")
    match = re.search(regex, github_ref)

    if match:
        # match.group(0) contains the exact matched identifier
        print(github_ref)
    else:
        print(subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip())

if __name__ == "__main__":
    fetch_ticket_or_sha()
