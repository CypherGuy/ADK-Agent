import datetime
import json
import os
from pathlib import Path
import subprocess
import tomllib
import config


def list_repos(repos_path):
    """
    Lists all repositories in the configured repos directory where the 
    last commit was made over REPO_STALENESS_DAYS days ago.

    Output: a list of subdirectory names (just the names, not full paths)
    """
    results = []
    for f in os.scandir(repos_path):
        if f.is_dir() and not f.name.startswith(".") and f.name not in config.EXCLUDED_REPOS:
            git_log_response = subprocess.run(["git", "log", "-1", "--pretty=format:%at"],
                                              cwd=f, capture_output=True)
            if git_log_response.returncode == 0:
                try:
                    last_commit_date = datetime.datetime.fromtimestamp(
                        int(git_log_response.stdout.decode().strip()))
                    if (datetime.datetime.now() - last_commit_date).days < config.REPO_STALENESS_DAYS:
                        continue

                    results.append(f.name)
                except IndexError:  # No git history
                    continue
    return results


def read_git_log(repo: str):
    """
    Input: a repository name, ie "full/absolute/path/to/BloodReview"
    Output: a dict with two keys:


    {
        "last_commit_date": "2026-05-07 14:23:11 +0000",  # string
        "recent_commits": [                                 # list of strings, max 10
            "feat: Add feature",
            "fix: Implement fix",
            ...
        ]
    }
"""
    ret = {"last_commit_date": "", "recent_commits": []}
    source_dir = config.REPOS_PATH / repo
    git_log_response = subprocess.run(["git", "log", "--max-count=10"],
                                      cwd=source_dir, capture_output=True)

    if git_log_response.returncode != 0:
        return ret

    git_log = git_log_response.stdout.split(b"\n")

    if git_log == ['']:
        return ret

    flag = False
    for line in git_log:
        if line.startswith(b'Date:') and not flag:
            # e.g. "2026-05-07 14:23:11 +0000" — must have time and offset
            parts = line.decode().split()
            dt = datetime.datetime.strptime(
                f"{parts[2]} {parts[3]} {parts[5]} {parts[4]} {parts[6]}", "%b %d %Y %H:%M:%S %z")
            ret["last_commit_date"] = dt.date().isoformat()

            flag = True
        else:
            commit_list = ret["recent_commits"]
            if len(commit_list) < 10 and line.startswith(b"    "):
                commit_list.append(line.decode("utf-8").strip())

    return ret


def read_dependencies(repo: str):
    """
    Input: a repository name, ie "full/absolute/path/to/BloodReview"

    Output: a list of strings, e.g.:
    ["express", "axios", "lodash"]
    """

    # We search for files which tend to contain dependencies
    # and extract dependencies in the,

    ret = []
    source_dir = config.REPOS_PATH / repo
    files = source_dir.glob('requirements.txt')
    for file in files:
        with open(file) as f:
            requirements = [line.strip() for line in f if line.strip()
                            and not line.startswith('#')]
            ret.extend(requirements)

    files = source_dir.glob('package.json')
    for file in files:
        with open(file) as f:
            json_data = json.load(f)
            ret.extend(json_data.get("dependencies", {}).keys())

    toml_files = source_dir.glob('pyproject.toml')
    for file in toml_files:
        with open(file, 'rb') as f:
            data = tomllib.load(f)
            ret.extend(data.get("project", {}).get("dependencies", []))
    if len(ret) > 0:
        return ret
    else:
        # Look at file extensions
        SKIP_DIRS = {'venv', '.venv', 'node_modules', '__pycache__', '.git'}
        extension_set = set()
        for root, dirs, files in os.walk(source_dir):
            depth = root.replace(str(source_dir), '').count(os.sep)

            # Skips files we didn't actually code like venv and node_modules
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            if depth >= 2:
                dirs.clear()
            for file in files:
                extension_set.add(file.split(".")[-1].lower())

        # We don't include Python because for me personally, I use it in practically
        # every project so no point trying to include it in underused technologies.
        language_extensions = {"ts": "TypeScript",
                               "js": "JavaScript", "go": "Golang", "rb": "Ruby", "sh": "Bash", "json": "JSON", "java": "Java", "ps1": "PowerShell", "tf": "Terraform"}

        for extension in language_extensions:
            if extension in extension_set:
                ret.append(language_extensions[extension])

    return ret
