import json
import os
from pathlib import Path
import tomllib


def list_repos(fp: str):
    """
    Input: a string path to a directory, ie "/home/kabir/repos"
    Output: a list of subdirectory names (just the names, not full paths)
    """
    return [f.name for f in os.scandir(fp) if f.is_dir()]


def read_git_log(repo: str):
    """
    Input: a string path to a single directory, ie "/home/kabir/repos/my-app"

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
    source_dir = Path(repo)
    files = source_dir.glob('git_log.txt')
    flag = False
    for file in files:
        with file.open('r') as file_handle:
            for line in file_handle:
                if line.startswith('Date:') and not flag:
                    parts = line.split()
                    ret["last_commit_date"] = f"{parts[1].strip()} {parts[2].strip()} {parts[3].strip()}"
                    flag = True
                else:
                    commit_list = ret["recent_commits"]
                    if len(commit_list) < 10 and line.startswith("    "):
                        commit_list.append(line.strip())

    return ret


def read_dependencies(repo: str):
    """
    Input: a string path to a single repo directory, e.g. "/home/kabir/repos/my-app"

    Output: a list of strings, e.g.:
    ["express", "axios", "lodash"]
    """
    ret = []
    source_dir = Path(repo)
    files = source_dir.glob('package.json')
    for file in files:
        with open(file) as f:
            json_data = json.load(f)
            ret.extend(json_data["dependencies"].keys())

    toml_files = source_dir.glob('pyproject.toml')
    for file in toml_files:
        with open(file, 'rb') as f:
            data = tomllib.load(f)
            ret.extend([tool for tool in data["project"]["dependencies"]])
    if len(ret) > 0:
        return ret
    else:
        # Look at file extensions
        extension_set = set()
        for _, _, files in os.walk(repo):
            for file in files:
                extension_set.add(file.split(".")[-1].lower())

        language_extensions = {"py": "Python", "ts": "TypeScript",
                               "js": "JavaScript", "go": "Golang", "rb": "Ruby", "sh": "Bash", "json": "JSON", "c": "C"}

        for extension in language_extensions:
            if extension in extension_set:
                ret.append(language_extensions[extension])

    return ret
