import type { VideoFrame } from "../types";

export const frameAtTime = (frames: VideoFrame[], time: number) => {
  let start = 0;
  let end = frames.length;
  while (start < end) {
    const middle = (start + end) >>> 1;
    if (frames[middle].time <= time + 0.0001) start = middle + 1;
    else end = middle;
  }
  return Math.max(0, start - 1);
};

/** Follow decoded frame timestamps, with animation-frame polling as a fallback. */
export const observeVideoFrames = (
  video: HTMLVideoElement,
  frames: VideoFrame[],
  draw: (time: number) => void
) => {
  let callback = 0;
  let stopped = false;
  const frameCallbacks = typeof video.requestVideoFrameCallback === "function";

  if (frameCallbacks) {
    const tick: VideoFrameRequestCallback = (_now, metadata) => {
      draw(metadata.mediaTime);
      if (!stopped) callback = video.requestVideoFrameCallback(tick);
    };
    callback = video.requestVideoFrameCallback(tick);
  } else {
    let lastFrame = -1;
    const tick = () => {
      const index = frameAtTime(frames, video.currentTime);
      if (index !== lastFrame) {
        lastFrame = index;
        draw(video.currentTime);
      }
      callback = requestAnimationFrame(tick);
    };
    callback = requestAnimationFrame(tick);
  }

  return () => {
    stopped = true;
    if (frameCallbacks) video.cancelVideoFrameCallback(callback);
    else cancelAnimationFrame(callback);
  };
};
