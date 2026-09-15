/** Keep compressed masks and nearby ID grids in bounded memory, not localStorage. */
import type { VideoManifest } from "../types";

export const createMaskCache = (
  manifest: VideoManifest,
  lookAhead = 2,
) => {
  const urls = manifest.maskUrls;
  const frameBytes = manifest.width * manifest.height;
  if (manifest.maskFormat !== "ids-gzip" ||
      ![manifest.width, manifest.height].every(size => Number.isInteger(size) && size > 0 && size <= 640) ||
      manifest.chunkFrames !== 10 || !manifest.frames.length ||
      urls.length !== Math.ceil(manifest.frames.length / manifest.chunkFrames)) {
    throw new Error("Unsupported mask data. Run the video again.");
  }
  if (typeof DecompressionStream === "undefined") {
    throw new Error("This browser cannot unpack masks. Update your browser to play this result.");
  }
  const images = new Map<number, Uint8Array>();
  const pending = new Map<number, Promise<Uint8Array>>();
  const blobs = new Map<number, Blob>();
  const downloads = new Map<number, Promise<Blob>>();
  const compressedLimit = 8 * 1024 * 1024;
  let compressedBytes = 0;
  let downloadCursor = 0;
  let downloadingAhead = false;
  let decoding = Promise.resolve();
  const controller = new AbortController();
  let center = 0;

  const trim = () => {
    for (const index of images.keys()) {
      const nearby = index >= center - 1 && index <= center + lookAhead;
      if (index !== 0 && !nearby) {
        images.delete(index);
      }
    }
  };

  const download = async (index: number): Promise<Blob> => {
    if (controller.signal.aborted) throw new Error("Player closed");
    const response = await fetch(urls[index], { signal: controller.signal });
    if (!response.ok)
      throw new Error(
        "Masks could not be loaded. Reload the result to refresh its access links."
      );
    const blob = await response.blob();
    if (controller.signal.aborted) throw new Error("Player closed");
    if (blob.size <= compressedLimit) {
      for (const [oldest, cached] of blobs) {
        if (compressedBytes + blob.size <= compressedLimit) break;
        blobs.delete(oldest);
        compressedBytes -= cached.size;
      }
      blobs.set(index, blob);
      compressedBytes += blob.size;
    }
    return blob;
  };

  const compressed = (index: number): Promise<Blob> => {
    const blob = blobs.get(index);
    if (blob) return Promise.resolve(blob);
    const existing = downloads.get(index);
    if (existing) return existing;
    const request = download(index).finally(() => downloads.delete(index));
    downloads.set(index, request);
    return request;
  };

  const decode = async (index: number, blob: Blob) => {
    if (controller.signal.aborted) throw new Error("Player closed");
    const frames = Math.min(manifest.chunkFrames, manifest.frames.length - index * manifest.chunkFrames);
    const image = new Uint8Array(frameBytes * frames);
    const reader = blob.stream().pipeThrough(
      new DecompressionStream("gzip"), { signal: controller.signal },
    ).getReader();
    let offset = 0;
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (offset + value.length > image.length) throw new Error("Mask data has an invalid size.");
        image.set(value, offset);
        offset += value.length;
      }
      if (offset !== image.length) throw new Error("Mask data is incomplete.");
    } finally {
      await reader.cancel().catch(() => undefined);
      reader.releaseLock();
    }
    if (controller.signal.aborted) {
      throw new Error("Player closed");
    }
    images.set(index, image);
    trim();
    return image;
  };

  const load = (index: number): Promise<Uint8Array> => {
    if (!Number.isInteger(index) || index < 0 || index >= urls.length) {
      return Promise.reject(new Error("Invalid mask chunk."));
    }
    const image = images.get(index);
    if (image) return Promise.resolve(image);
    const existing = pending.get(index);
    if (existing) return existing;
    // Serialize decompression to bound temporary buffers during seeks.
    const request = compressed(index).then(blob => {
      const result = decoding.then(() => decode(index, blob));
      decoding = result.then(() => undefined, () => undefined);
      return result;
    }).finally(() => pending.delete(index));
    pending.set(index, request);
    return request;
  };

  const prefetch = () => {
    const last = Math.min(center + lookAhead, urls.length - 1);
    for (let index = center + 1; index <= last; index++) {
      // A failed prefetch can retry when playback reaches that image.
      void load(index)
        .then(trim)
        .catch(() => undefined);
    }
    // Fetch farther ahead without expanding the much larger decoded window.
    if (downloadingAhead || controller.signal.aborted) return;
    downloadingAhead = true;
    void (async () => {
      while (downloadCursor < urls.length && !controller.signal.aborted) {
        if (compressedBytes >= compressedLimit) break;
        const batch: Promise<Blob>[] = [];
        for (let count = 0; count < 2 && downloadCursor < urls.length; count++) {
          batch.push(compressed(downloadCursor++));
        }
        await Promise.all(batch);
      }
    })().catch(() => undefined).finally(() => { downloadingAhead = false; });
  };

  // Wait for a useful runway before resuming, rather than one sheet at a time.
  const buffer = () => {
    const last = Math.min(center + lookAhead, urls.length - 1);
    const requests: Promise<Uint8Array>[] = [];
    for (let index = center; index <= last; index++) requests.push(load(index));
    return Promise.all(requests);
  };

  const moveTo = (index: number) => {
    if (index < center) downloadCursor = index;
    else downloadCursor = Math.max(downloadCursor, index);
    center = index;
    trim();
  };

  const get = (index: number) => images.get(index);

  const dispose = () => {
    controller.abort();
    images.clear();
    blobs.clear();
    compressedBytes = 0;
  };

  return { get, load, moveTo, prefetch, buffer, dispose };
};
