import { useEffect, useMemo, useRef, useState } from "react";
import { createClassColorMap } from "./FunctionUtils";
import NeuralNetworkSpinner from "./NeuralNetworkSpinner";
import type { ViewerControlsState } from "./assistant/state/viewerControls";
import type { Detection } from "./assistant/types";
import { buildMaskOverlay } from "./image/rendering/buildMaskOverlay";
import { drawBoxes } from "./image/rendering/drawBoxes";
import type { PyTorchImageResponseType } from "./types";

interface ImageCanvasProps {
  controls: ViewerControlsState;
  loading: boolean;
  image?: HTMLImageElement | null;
  boundingBoxData?: PyTorchImageResponseType | null;
  masks?: number[][][];
  isError?: boolean;
  errorMessage?: any;
}

function detectionsFrom(data?: PyTorchImageResponseType | null): Detection[] {
  if (!data) return [];
  return data.boxes.map((box, index) => ({
    box,
    label: data.classes[index],
    score: data.scores[index],
  }));
}

const ImageCanvas = ({
  controls,
  loading,
  image,
  boundingBoxData,
  masks = [],
  isError,
  errorMessage,
}: ImageCanvasProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const detections = useMemo(() => detectionsFrom(boundingBoxData), [boundingBoxData]);
  // Keep each generated palette for this image so Undo restores the same colors.
  const palettes = useMemo(() => new Map<number, Record<string, string>>(), [boundingBoxData]);
  const classColorMap = useMemo(() => {
    const version = controls.appearance.paletteVersion;
    let palette = palettes.get(version);
    if (!palette) {
      palette = createClassColorMap(boundingBoxData);
      palettes.set(version, palette);
    }
    return palette;
  }, [boundingBoxData, controls.appearance.paletteVersion, palettes]);
  const [cachedMaskImage, setCachedMaskImage] = useState<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const overlay = buildMaskOverlay(masks, detections, controls, classColorMap);
    if (!overlay || !image) {
      setCachedMaskImage(null);
      return;
    }
    const maskCanvas = document.createElement("canvas");
    maskCanvas.width = overlay.width;
    maskCanvas.height = overlay.height;
    const context = maskCanvas.getContext("2d");
    if (!context) {
      setCachedMaskImage(null);
      return;
    }
    const imageData = context.createImageData(overlay.width, overlay.height);
    imageData.data.set(overlay.pixels);
    context.putImageData(imageData, 0, 0);
    setCachedMaskImage(maskCanvas);
  }, [masks, detections, controls, classColorMap, image]);

  useEffect(() => {
    if (!image || !boundingBoxData) return;
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    canvas.width = image.width;
    canvas.height = image.height;
    context.drawImage(image, 0, 0);
    if (cachedMaskImage) {
      context.imageSmoothingEnabled = false;
      context.drawImage(cachedMaskImage, 0, 0, image.width, image.height);
    }
    drawBoxes(context, detections, controls, classColorMap);
  }, [image, boundingBoxData, cachedMaskImage, detections, controls, classColorMap, loading, isError]);

  return <div id="boundingBoxCanvasDiv"
    className="h-full flex md:rounded-md shadow-md shadow-black"
    style={{ backgroundColor: "#000000" }}>
    {loading && <div className="w-full flex justify-center"><NeuralNetworkSpinner /></div>}
    {!loading && !isError && <canvas ref={canvasRef}
      className="object-contain h-full w-full" id="boundingBoxCanvas" />}
    {isError && <div className="w-full flex justify-center text-red-500 font-bold mt-6 mx-12">
      {errorMessage?.error
        ?? "An error occurred while reaching the Java API. Please try again later."}
    </div>}
  </div>;
};

export default ImageCanvas;
