
from typing import List
import os
from pathlib import Path


def list_digest_files(file_path: str) -> List[str]:
    absolute_path = os.path.abspath(file_path)
    if not os.path.isdir(absolute_path):
        raise ValueError(f"Invalid directory: {absolute_path}")
    ret = []

    source_dir = Path(absolute_path)
    files = source_dir.glob('*.txt')
    for file in files:
        ret.append(str(file.name))

    ret = sorted(ret, reverse=True)

    return [f"{absolute_path}/{entry}" for entry in ret]


def read_digest(file_path: str) -> str:
    """
    Input: file_path: str -> A path string to a single .txt digest file

    Output: The raw text content of that file, unchanged
    """

    with open(file_path, "r") as f:
        return "".join(f.readlines())
