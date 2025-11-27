import re
import json
import subprocess
import git
import sys

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


configPath = "config.json"
def main():
    file = json.load(open(configPath, 'r'))
    nextMode = 0
    try:
        nextMode = int(sys.argv[1])
    except Exception as e:
        nextMode = 0
    if nextMode == 0:
        print("Not incrementing version, proceeding to push...")
    else:
        file["version"] = bump_version(file["version"], nextMode)
        print(f"Advancing to version {file["version"]}..")
        json.dump(file, open(configPath, 'w'), indent=4)
    commitMessage = f"Version {file["version"]} Release"
    print(f"Pushing with commitMessage \"{commitMessage}\"")
    git_push_all(message=commitMessage)


if __name__ == "__main__":
    main()