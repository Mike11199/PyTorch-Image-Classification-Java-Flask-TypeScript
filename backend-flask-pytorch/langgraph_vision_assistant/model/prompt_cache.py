"""Best-effort disk snapshot of the single llama.cpp slot across model switches."""

import hashlib
import logging
import os
from pathlib import Path
import tempfile
from contextlib import suppress

LOGGER = logging.getLogger(__name__)


class PromptCache:
    def __init__(self, settings):
        self.directory = Path(os.getenv(
            'LLM_PROMPT_CACHE_DIR', str(Path(tempfile.gettempdir()) / 'qwen-prompt-cache'),
        ))
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.is_symlink() or (
            hasattr(os, 'getuid') and self.directory.stat().st_uid != os.getuid()
        ):
            raise PermissionError('Prompt cache directory must be owned by this process user')
        self.directory.chmod(0o700)
        # Version includes our fixed context/KV settings; file identities invalidate
        # snapshots after a model or runtime replacement, without hashing GB files.
        identities = ['v1:ctx8192:kq8_0:vq8_0']
        for value in (settings.model_path, settings.server_path):
            path = Path(value).resolve()
            stat = path.stat()
            identities.append(f'{path}:{stat.st_size}:{stat.st_mtime_ns}')
        self.filename = hashlib.sha256('|'.join(identities).encode()).hexdigest() + '.bin'

    def restore(self, transport):
        path = self.directory / self.filename
        if not path.is_file():
            return
        try:
            result = transport.slot('restore', self.filename)
            LOGGER.info('Prompt cache restored: %s', result)
        except (OSError, ValueError) as error:
            LOGGER.warning('Prompt cache restore skipped: %s', error)
            with suppress(OSError):
                path.unlink(missing_ok=True)

    def save(self, transport):
        temporary = self.filename + '.tmp'
        try:
            result = transport.slot('save', temporary)
            (self.directory / temporary).replace(self.directory / self.filename)
            LOGGER.info('Prompt cache saved: %s', result)
        except (OSError, ValueError) as error:
            LOGGER.warning('Prompt cache save skipped: %s', error)
