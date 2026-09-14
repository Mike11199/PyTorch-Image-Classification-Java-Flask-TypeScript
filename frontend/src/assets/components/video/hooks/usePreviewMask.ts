import { useEffect, useRef, useState } from "react";
import { drawDetections } from "../player/drawDetections";
import type { VideoAppearance, VideoStatus } from "../types";

export const usePreviewMask = (
  status: VideoStatus | null,
  appearance: VideoAppearance
) => {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [loaded, setLoaded] = useState<{ url: string; image: ImageBitmap } | null>(
    null
  );
  const [error, setError] = useState("");
  const url = status?.previewMaskUrl;

  useEffect(() => {
    if (!url) return;
    const controller = new AbortController();
    let image: ImageBitmap | undefined;
    setError("");

    const loadMask = async () => {
      try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error("The preview mask could not be loaded.");
        image = await createImageBitmap(await response.blob());
        if (controller.signal.aborted) image.close();
        else setLoaded({ url, image });
      } catch (error) {
        if (!controller.signal.aborted) setError((error as Error).message);
      }
    };

    void loadMask();
    return () => {
      controller.abort();
      image?.close();
    };
  }, [url]);

  useEffect(() => {
    const element = canvas.current;
    const context = element?.getContext("2d", { willReadFrequently: true });
    if (!element || !context) return;
    context.clearRect(0, 0, element.width, element.height);
    if (!loaded || loaded.url !== url) return;
    const { image } = loaded;
    element.width = image.width;
    element.height = image.height;
    const frame = {
      time: status?.previewTime || 0,
      detections: status?.previewDetections || [],
    };
    const layout = {
      width: image.width,
      height: image.height,
      columns: 1,
      chunkFrames: 1,
      frames: [frame],
    };
    drawDetections(context, image, layout, 0, appearance, null);
  }, [loaded, url, status?.previewDetections, status?.previewTime, appearance]);

  return { canvas, error };
};
