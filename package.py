import re
import json
import subprocess
import sys
import os
from pathlib import Path

max_file_size_bytes = 10 * 1024 * 1024
parentPath = Path(__file__).parent

def bump_version(ver: str, mode: int = 0) -> str:
    match = re.match(r"v(\d+)\.(\d+)([a-z]?)$", ver)
    if not match:
        raise ValueError("Invalid version format")

    major, minor, suffix = match.groups()
    major, minor = int(major), int(minor)

    # MODE 1 → remove suffix & bump number
    if mode == 10:
        minor += 1
        return f"v{major}.{minor:02d}"

    # MODE 0 logic below:

    # no suffix → add 'a'
    if suffix == "":
        return f"v{major}.{minor:02d}a"

    # suffix a–y → increment letter
    if suffix < "z":
        next_suffix = chr(ord(suffix) + 1)
        return f"v{major}.{minor:02d}{next_suffix}"

    # suffix z → bump number, drop suffix
    minor += 1
    return f"v{major}.{minor:02d}"

def git_push_all(message="auto commit"):
    # stage everything
    subprocess.run(["git", "add", "--all"], check=True)

    # commit (won't fail if nothing to commit)
    subprocess.run(["git", "commit", "-m", message], check=False)

    # push
    subprocess.run(["git", "push"], check=True)

def split_file(input_file, splitFilesJSON):
    output_dir = os.path.dirname(input_file)
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(input_file)
    rel_path = os.path.relpath(input_file)
    part_num = 1
    splitFilesJSON[rel_path] = []

    with open(input_file, "rb") as f:
        while True:
            chunk = f.read(max_file_size_bytes)
            if not chunk:
                break
            part_file = os.path.join(output_dir, f"{base_name}.part{part_num}")
            with open(part_file, "wb") as pf:
                pf.write(chunk)
            splitFilesJSON[rel_path].append(os.path.relpath(part_file))
            print(f"Created: {part_file}")
            part_num += 1

def calculate_file_size():
    total_size = 0
    for dirpath, _, filenames in os.walk(parentPath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size

configPath = "config.json"
def main():
    file = json.load(open(configPath, 'r'))

    # Version increment
    nextMode = 0
    try:
        nextMode = int(sys.argv[1])
    except Exception as e:
        nextMode = 0
    if nextMode == 0:
        print("Not incrementing version, proceeding to push...")
    elif nextMode > 0:
        file["version"] = bump_version(file["version"], nextMode)
        print(f"Advancing to version {file["version"]}..")
    else:
        print(f"Not advancing version because nextMode is negative (nextMode = {nextMode})")

    # Splitting Files
    split_file("Build/UnityPlayer.dll", file["split_files"])
    sizeInBytes = calculate_file_size()
    print(f"Total File Size: {calculate_file_size() / 1024 / 1024 :.1f} MB")
    file["total_size"] = sizeInBytes

    json.dump(file, open(configPath, 'w'), indent=4)

    # Commit
    if (nextMode < 0):
        print(f"Not pushing because nextMode is negative (nextMode = {nextMode})")
    else:
        commitMessage = f"Version {file["version"]} Release"
        print(f"Pushing with commitMessage \"{commitMessage}\"")
        git_push_all(message=commitMessage)
    


if __name__ == "__main__":
    main()