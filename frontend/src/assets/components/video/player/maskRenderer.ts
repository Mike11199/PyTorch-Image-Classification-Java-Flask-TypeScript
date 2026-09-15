/** Load and paint the mask for each presented frame, pausing on missing images. */
import type { VideoAppearance, VideoManifest } from "../types";
import { drawDetections } from "./drawDetections";
import { frameAtTime, observeVideoFrames } from "./frameTiming";
import { createMaskCache } from "./maskCache";

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
  const context = canvas.getContext("2d", { willReadFrequently: true })!;
  // Aim for a second ahead, limiting retained RGBA pixels to roughly 64 MiB.
  // Reserve space for the current, previous, and first sheets (kept for looping).
  const sheetBytes = manifest.width * manifest.height * manifest.columns *
    Math.ceil(manifest.chunkFrames / manifest.columns) * 4;
  const secondFrame = frameAtTime(manifest.frames, manifest.frames[0].time + 1);
  const lookAhead = Math.max(1, Math.min(
    Math.ceil(secondFrame / manifest.chunkFrames),
    Math.floor(64 * 1024 * 1024 / sheetBytes) - 3,
    6
  ));
  const cache = createMaskCache(manifest.maskUrls, lookAhead);
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
      drawDetections(context, image, manifest, index, appearance, selected);
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
