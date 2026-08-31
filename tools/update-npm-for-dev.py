import json
import subprocess
import datetime
import os

def update_project():
    try:
        # 1. Read the current package.json
        with open('package.json', 'r', encoding='utf-8') as f:
            package_json = json.load(f)

        # 2. Gather the dynamic build data using Git commands
        branch = os.environ.get('GITHUB_REF') or subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('utf-8').strip()
        sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
        build_time = datetime.datetime.now(datetime.UTC).strftime("%B %d, %Y %I:%M:%S %p UTC")
        
        # 3. Drop the new fields into your custom metadata block
        package_json['meta'] = {
            'branch': branch,
            'sha': sha,
            'buildTime': build_time,
        }

        # 4. Give publishing a tag
        package_json['publishConfig']['tag'] = "dev"

        # 5. Save the updated package.json back to disk with proper formatting
        with open('package.json', 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)
            f.write('\n') # Add a final newline character

    except Exception as e:
        print(f"Failed to inject metadata: {e}")
        exit(1)


if __name__ == "__main__":
    update_project()

