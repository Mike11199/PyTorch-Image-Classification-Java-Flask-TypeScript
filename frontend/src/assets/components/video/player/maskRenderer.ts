/** Follow the video's presented frame and draw its indexed masks. */
import type { VideoAppearance, VideoManifest } from "../types";
import { drawBoxes } from "./drawDetections";
import { frameAtTime, observeVideoFrames } from "./frameTiming";
import { createMaskCache } from "./maskCache";
import { createIdMaskPainter } from "./idMaskPainter";

interface MaskRendererOptions {
  settings: () => { appearance: VideoAppearance; selected: string | null };
  shouldPlay: () => boolean;
  onBuffering: (buffering: boolean) => void;
  onError: (message: string) => void;
  onPlayBlocked: () => void;
}

export const createMaskRenderer = (
  video: HTMLVideoElement,
  canvas: HTMLCanvasElement,
  manifest: VideoManifest,
  options: MaskRendererOptions
) => {
  const context = canvas.getContext("2d")!;
  const frameBytes = manifest.width * manifest.height;
  // Reserve room for current, previous, and first chunks within 32 MiB of IDs.
  const sheetBytes = frameBytes * manifest.chunkFrames;
  const aheadFrame = frameAtTime(manifest.frames, manifest.frames[0].time + 2);
  const lookAhead = Math.max(1, Math.min(
    Math.ceil(aheadFrame / manifest.chunkFrames),
    Math.floor(32 * 1024 * 1024 / sheetBytes) - 3,
    12
  ));
  const cache = createMaskCache(manifest, lookAhead);
  const paint = createIdMaskPainter(context, manifest.width, manifest.height);
  let disposed = false;
  let generation = 0;
  let buffering = true;

  /** Resume after buffering only if the visitor still wants playback. */
  const resumePlayback = async () => {
    if (!options.shouldPlay() || !video.paused || video.ended) return;
    await video.play().catch(() => {
      if (!disposed) options.onPlayBlocked();
    });
  };

  /** Paint the latest requested frame, ignoring superseded requests. */
  const draw = async (mediaTime = video.currentTime) => {
    const current = ++generation;
    const index = frameAtTime(manifest.frames, mediaTime);
    const chunk = Math.floor(index / manifest.chunkFrames);
    cache.moveTo(chunk);

    try {
      if (!cache.get(chunk)) buffering = true;
      if (buffering) {
        video.pause();
        options.onBuffering(true);
        await cache.buffer();
      }
      // Seeking or a newer frame can supersede an in-flight mask request.
      if (disposed || current !== generation) return;
      const image = cache.get(chunk);
      if (!image) return;
      const { appearance, selected } = options.settings();
      const detections = manifest.frames[index].detections;
      const offset = index % manifest.chunkFrames * frameBytes;
      paint(image.subarray(offset, offset + frameBytes), detections, appearance.maskOpacity, appearance.defaultVideo);
      drawBoxes(context, detections, appearance, selected);
      buffering = false;
      options.onBuffering(false);

      cache.prefetch();
      await resumePlayback();
    } catch (error) {
      if (!disposed && current === generation) options.onError((error as Error).message);
    }
  };

  const redraw = () => {
    void draw();
  };
  const stopFrames = observeVideoFrames(video, manifest.frames, draw);
  video.addEventListener("seeked", redraw);
  video.addEventListener("loadeddata", redraw);
  redraw();

  const dispose = () => {
    disposed = true;
    generation++;
    stopFrames();
    cache.dispose();
    video.removeEventListener("seeked", redraw);
    video.removeEventListener("loadeddata", redraw);
  };

  return { redraw, dispose };
};
