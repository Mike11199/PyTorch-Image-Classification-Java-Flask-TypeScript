"""Pack ten mask frames into each transparent PNG image."""

from PIL import Image

from ..config import ATLAS_COLUMNS, ATLAS_ROWS, CHUNK_FRAMES


class MaskAtlas:
    """Hold at most one unfinished mask atlas in memory."""

    def __init__(self, assets, prefix, directory):
        """Track output keys and the current atlas image."""
        self.assets = assets
        self.prefix = prefix
        self.directory = directory
        self.image = None
        self.keys = []
        self.width = self.height = 0

    def add(self, overlay, index, last_frame):
        """Paste one mask and save the atlas when it is full or final."""
        self.width, self.height = overlay.size
        slot = index % CHUNK_FRAMES
        if slot == 0:
            self.image = Image.new(
                "RGBA", (self.width * ATLAS_COLUMNS, self.height * ATLAS_ROWS)
            )
        position = (
            (slot % ATLAS_COLUMNS) * self.width,
            (slot // ATLAS_COLUMNS) * self.height,
        )
        self.image.paste(overlay, position)
        if slot == CHUNK_FRAMES - 1 or last_frame:
            self.save(index // CHUNK_FRAMES)

    def save(self, chunk):
        """Publish a completed atlas and release its pixels."""
        key = f"{self.prefix}/masks/{chunk:04d}.png"
        path = self.directory / "masks.png"
        self.image.save(path, compress_level=3)
        self.assets.put_file(key, path, "image/png")
        self.keys.append(key)
        self.close()

    def close(self):
        """Release an unfinished atlas after cancellation or failure."""
        if self.image is not None:
            self.image.close()
            self.image = None
