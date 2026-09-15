"""Store mask coverage as compressed one-byte detection IDs."""

import gzip


class MaskIds:
    """Gzip consecutive row-major uint8 frames; ID n selects detections[n - 1]."""

    def __init__(self, assets, prefix, directory, chunk_frames):
        self.assets = assets
        self.prefix = prefix
        self.directory = directory
        self.width = self.height = 0
        self.chunk_frames = chunk_frames
        self.frames = []
        self.keys = []

    def add(self, ids, index, last_frame):
        """Append one indexed frame and publish a complete chunk."""
        if not self.width:
            self.height, self.width = ids.shape
        if ids.shape != (self.height, self.width):
            raise ValueError("Mask ID frames do not have a consistent resolution.")
        self.frames.append(ids.tobytes())
        if len(self.frames) == self.chunk_frames or last_frame:
            self.save(index // self.chunk_frames)

    def save(self, chunk):
        """Compress raw IDs and release the chunk buffer."""
        path = self.directory / "masks.mask"
        path.write_bytes(gzip.compress(b"".join(self.frames), compresslevel=6, mtime=0))
        # Gzip is the payload format, not HTTP Content-Encoding.
        key = f"{self.prefix}/masks/{chunk:04d}.mask"
        self.assets.put_file(key, path, "application/octet-stream")
        self.keys.append(key)
        self.frames.clear()
