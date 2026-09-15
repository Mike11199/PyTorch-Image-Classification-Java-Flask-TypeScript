/** Keep nearby mask images decoded, including the first image for looping. */

export const createMaskCache = (urls: string[], lookAhead = 2) => {
  const images = new Map<number, ImageBitmap>();
  const pending = new Map<number, Promise<ImageBitmap>>();
  const controller = new AbortController();
  let center = 0;

  const trim = () => {
    for (const [index, image] of images) {
      const nearby = index >= center - 1 && index <= center + lookAhead;
      if (index !== 0 && !nearby) {
        image.close();
        images.delete(index);
      }
    }
  };

  const download = async (index: number) => {
    if (controller.signal.aborted) throw new Error("Player closed");
    const response = await fetch(urls[index], { signal: controller.signal });
    if (!response.ok)
      throw new Error(
        "Masks could not be loaded. Reload the result to refresh its access links."
      );
    const image = await createImageBitmap(await response.blob());
    if (controller.signal.aborted) {
      image.close();
      throw new Error("Player closed");
    }
    images.set(index, image);
    trim();
    return image;
  };

  const load = (index: number): Promise<ImageBitmap> => {
    const image = images.get(index);
    if (image) return Promise.resolve(image);
    const existing = pending.get(index);
    if (existing) return existing;
    const request = download(index).finally(() => pending.delete(index));
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
  };

  // Wait for a useful runway before resuming, rather than one sheet at a time.
  const buffer = () => {
    const last = Math.min(center + lookAhead, urls.length - 1);
    const requests: Promise<ImageBitmap>[] = [];
    for (let index = center; index <= last; index++) requests.push(load(index));
    return Promise.all(requests);
  };

  const moveTo = (index: number) => {
    center = index;
    trim();
  };

  const get = (index: number) => images.get(index);

  const dispose = () => {
    controller.abort();
    for (const image of images.values()) image.close();
    images.clear();
  };

  return { get, load, moveTo, prefetch, buffer, dispose };
};
