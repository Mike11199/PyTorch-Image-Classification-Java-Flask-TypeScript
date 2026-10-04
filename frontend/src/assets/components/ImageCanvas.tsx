import { useEffect, useState, useMemo } from "react";
import { PyTorchImageResponseType } from "./types";
import { createClassColorMap } from "./FunctionUtils";
import NeuralNetworkSpinner from "./NeuralNetworkSpinner";
import type { ViewerState } from "./assistant/types";
import { detectionAlpha, detectionVisible, hexRgb } from "./assistant/viewState";

interface ImageCanvasProps {
  assistantView?: ViewerState;
  loading: boolean;
  image?: HTMLImageElement | null;
  boundingBoxData?: PyTorchImageResponseType | null;
  pyTorchBoxLineWidth: number;
  pyTorchBoxFontSize: number;
  pyTorchBoxXOffset: number;
  pyTorchBoxYOffset: number;
  colorMapCounter: number;
  pyTorchOpacity: number;
  pyTorchMaskOpacity?: number;
  pyTorchMasksArray?: number[][][];
  isError?: boolean;
  errorMessage?: any;
}

const ImageCanvas = ({
  assistantView,
  loading,
  image,
  boundingBoxData,
  pyTorchBoxLineWidth,
  pyTorchBoxFontSize,
  pyTorchBoxXOffset,
  pyTorchBoxYOffset,
  colorMapCounter,
  pyTorchOpacity,
  pyTorchMaskOpacity = 50,
  pyTorchMasksArray,
  isError,
  errorMessage,
}: ImageCanvasProps) => {
  const classColorMap = useMemo(
    () => createClassColorMap(boundingBoxData),
    [boundingBoxData, colorMapCounter]
  );

  const [cachedMaskImage, setCachedMaskImage] = useState<HTMLCanvasElement | null>(
    null
  );

  // Function to render masks onto a canvas
  useEffect(() => {
    const generateMaskBitmap = () => {
      if (
        !pyTorchMasksArray ||
        !pyTorchMasksArray.length ||
        !image ||
        !boundingBoxData?.boxes || assistantView?.showMasks === false
      ) {
        setCachedMaskImage(null);
        return;
      }

      const maskCanvas = document.createElement("canvas");
      // Masks may be computed at lower resolution than the uploaded image.
      const maskHeight = pyTorchMasksArray[0].length;
      const maskWidth = pyTorchMasksArray[0][0]?.length ?? 0;
      if (!maskWidth || !maskHeight) {
        setCachedMaskImage(null);
        return;
      }
      maskCanvas.width = maskWidth;
      maskCanvas.height = maskHeight;
      const maskCtx = maskCanvas.getContext("2d");
      if (!maskCtx) return;

      const maskData = maskCtx.createImageData(maskWidth, maskHeight);
      const data = maskData.data;

      // Batch update pixels for all masks
      pyTorchMasksArray.forEach((mask, index) => {
        const className = boundingBoxData.classes[index];
        if (!detectionVisible({ label: className, score: boundingBoxData.scores[index], box: boundingBoxData.boxes[index] }, assistantView)) return;
        const classColor = classColorMap[className] || "rgb(0, 0, 0)";
        const override = assistantView?.maskColors[className];
        const [r, g, b] = override ? hexRgb(override) : classColor.match(/\d+/g)?.map(Number) ?? [0, 0, 0];
        const alpha = Math.round((pyTorchMaskOpacity / 100) * 255 * detectionAlpha(index, 0, assistantView));

        mask.forEach((row, y) => {
          row.forEach((pixel, x) => {
            if (pixel === 1) {
              const offset = (y * maskWidth + x) * 4;
              data[offset] = r; // Red
              data[offset + 1] = g; // Green
              data[offset + 2] = b; // Blue
              data[offset + 3] = alpha; // Alpha
            }
          });
        });
      });

      maskCtx.putImageData(maskData, 0, 0);
      setCachedMaskImage(maskCanvas);
    };

    generateMaskBitmap();
  }, [
    assistantView,
    pyTorchMasksArray,
    boundingBoxData,
    classColorMap,
    image,
    pyTorchMaskOpacity,
  ]);

  // Draw bounding boxes and masks
  useEffect(() => {
    const drawBoundingBoxes = () => {
      if (!image || !boundingBoxData) return;

      const canvas = document.getElementById(
        "boundingBoxCanvas"
      ) as HTMLCanvasElement;
      const ctx = canvas?.getContext("2d");
      if (!ctx) return;

      canvas.width = image.width;
      canvas.height = image.height;

      // Draw base image
      ctx.drawImage(image, 0, 0);

      // Draw cached mask image
      if (cachedMaskImage) {
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(cachedMaskImage, 0, 0, image.width, image.height);
      }

      // Draw bounding boxes
      boundingBoxData.boxes.forEach((box, i) => {
        if (assistantView?.showBoxes === false || !detectionVisible({ label: boundingBoxData.classes[i], score: boundingBoxData.scores[i], box }, assistantView)) return;
        const [x, y, width, height] = box.map(Math.round);
        const className = boundingBoxData.classes[i];
        const accuracy = (boundingBoxData.scores[i] * 100).toFixed(1);

        // Get class color and apply opacity
        const classColor = classColorMap[className] || "rgb(0, 0, 0)";
        const override = assistantView?.boxColors[className];
        const [r, g, b] = override ? hexRgb(override) : classColor.match(/\d+/g)?.map(Number) ?? [0, 0, 0];
        const rgbaColor = `rgba(${r}, ${g}, ${b}, ${pyTorchOpacity / 100 * detectionAlpha(i, 0, assistantView)})`;

        // Set styles
        ctx.strokeStyle = rgbaColor;
        ctx.lineWidth = pyTorchBoxLineWidth;
        ctx.strokeRect(x, y, width - x, height - y);

        const formattedClassName =
          className.charAt(0).toUpperCase() + className.slice(1).toLowerCase();

        ctx.font = `bold ${pyTorchBoxFontSize}px Arial`;
        ctx.fillStyle = rgbaColor;
        ctx.fillText(
          `${formattedClassName} ${accuracy}%`,
          x + pyTorchBoxXOffset,
          y + pyTorchBoxYOffset
        );
      });
    };

    drawBoundingBoxes();
  }, [
    assistantView,
    image,
    boundingBoxData,
    cachedMaskImage,
    pyTorchBoxLineWidth,
    pyTorchBoxFontSize,
    pyTorchBoxXOffset,
    pyTorchBoxYOffset,
    pyTorchOpacity,
    classColorMap,
  ]);

  return (
    <div
      id="boundingBoxCanvasDiv"
      className="h-full flex md:rounded-md shadow-md shadow-black"
      style={{ backgroundColor: "#000000" }}
    >
      {loading && (
        <div className="w-full flex justify-center">
         < NeuralNetworkSpinner />
        </div>
      )}
      {!loading && !isError && (
        <canvas
          className="object-contain h-full w-full"
          id="boundingBoxCanvas"
        ></canvas>
      )}
      {isError && (
        <div className="w-full flex justify-center text-red-500 font-bold mt-6 mx-12">
          {errorMessage?.error ??
            "An error occurred while reaching the Java API. Please try again later."}
        </div>
      )}
    </div>
  );
};

export default ImageCanvas;
