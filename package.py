import re
import json
import subprocess
import git
import sys
import os

max_file_size_bytes = 10 * 1024 * 1024

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

def git_push_all(path=".", message="auto commit"):
    repo = git.Repo(path)

    repo.git.add(all=True)
    repo.index.commit(message)
    origin = repo.remote(name='origin')
    origin.push()

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
    elif nextMode >= 0:
        file["version"] = bump_version(file["version"], nextMode)
        print(f"Advancing to version {file["version"]}..")
    else:
        print(f"Not advancing version because nextMode is negative (nextMode = {nextMode})")

    # Splitting Files
    split_file("Build/UnityPlayer.dll", file["split_files"])

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