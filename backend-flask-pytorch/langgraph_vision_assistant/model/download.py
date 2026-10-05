"""Download the Qwen model file when building the backend image.

The command-line entry point takes a URL and destination. download streams the
file to a temporary path, checks the GGUF header, then replaces the destination.
GGUF is the model file format loaded by llama.cpp.

Inference reads that saved file through model/settings.py and runtime.py;
serving an assistant request does not invoke this download script.
"""

import pathlib
import sys

import requests


def download(url: str, destination: str) -> None:
    """Download and check a GGUF file before replacing the destination atomically."""
    target = pathlib.Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.download')
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with temporary.open('wb') as output:
            for chunk in response.iter_content(1024 * 1024):
                output.write(chunk)
    with temporary.open('rb') as downloaded:
        if downloaded.read(4) != b'GGUF':
            raise ValueError('The assistant model download is not a GGUF file.')
    temporary.replace(target)


if __name__ == '__main__':
    download(sys.argv[1], sys.argv[2])
