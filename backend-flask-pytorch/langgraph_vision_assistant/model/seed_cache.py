"""Prepare and verify a synthetic native-tool prompt snapshot during image build.

No viewer tools are executed and no visitor data is included. A second model
process must restore the snapshot and reuse most prompt tokens for another scene.
"""
import logging
import os
from pathlib import Path
import shutil
import tempfile

from ..agent.prompt import initial_messages
from ..tools.registry import VIEWER_TOOLS
from ..viewer.state import ViewerContext
from .client import completion_payload
from .runtime import LocalModel


def seed_payload(class_name):
    context = ViewerContext.from_request({
        'message': f'Make {class_name} purple', 'page': 'boxes',
        'availableClasses': [class_name], 'view': {},
    })
    return {**completion_payload(initial_messages(context), VIEWER_TOOLS), 'max_tokens': 1}


def build_seed():
    destination = Path(os.environ['LLM_PROMPT_CACHE_SEED_DIR'])
    destination.mkdir(parents=True, exist_ok=True)
    # Temporary runtime directories simulate two entirely fresh containers.
    with tempfile.TemporaryDirectory() as first:
        os.environ['LLM_PROMPT_CACHE_DIR'] = first
        model = LocalModel()
        try:
            model.create_chat_completion(**seed_payload('car'))
            if model.cache is None:
                raise RuntimeError('Prompt caching was disabled during image build')
            snapshot = model.cache.directory / model.cache.filename
            if not snapshot.is_file() or snapshot.stat().st_size == 0:
                raise RuntimeError('No starter snapshot was saved')
            shutil.copyfile(snapshot, destination / snapshot.name)
        finally:
            model.close()
    with tempfile.TemporaryDirectory() as second:
        os.environ['LLM_PROMPT_CACHE_DIR'] = second
        model = LocalModel()
        try:
            response = model.create_chat_completion(**seed_payload('dog'))
            usage = response.get('usage', {})
            cached = usage.get('prompt_tokens_details', {}).get('cached_tokens', 0)
            total = usage.get('prompt_tokens', 0)
            if total <= 0 or cached < total * 0.5:
                raise RuntimeError(f'Starter cache verification failed: {cached}/{total} tokens reused')
            logging.info('Starter cache verified across model reload: %s/%s prompt tokens reused', cached, total)
        finally:
            model.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    build_seed()
