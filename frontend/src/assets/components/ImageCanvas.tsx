import { LineWave } from "react-loader-spinner";
import { useEffect, useState, useMemo } from "react";
import { PyTorchImageResponseType } from "./types";
import { createClassColorMap } from "./FunctionUtils";

interface ImageCanvasProps {
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
  // Memoized classColorMap for performance
  const classColorMap = useMemo(
    () => createClassColorMap(boundingBoxData),
    [boundingBoxData, colorMapCounter]
  );

  const [cachedMaskImage, setCachedMaskImage] = useState<ImageBitmap | null>(
    null
  );

  // Function to render masks onto a canvas
  useEffect(() => {
    const generateMaskBitmap = async () => {
      if (
        !pyTorchMasksArray ||
        !pyTorchMasksArray.length ||
        !image ||
        !boundingBoxData?.boxes
      ) {
        setCachedMaskImage(null);
        return;
      }

      const maskCanvas = document.createElement("canvas");
      maskCanvas.width = image.width;
      maskCanvas.height = image.height;
      const maskCtx = maskCanvas.getContext("2d");
      if (!maskCtx) return;

      const maskData = maskCtx.createImageData(image.width, image.height);
      const data = maskData.data;

      // Batch update pixels for all masks
      pyTorchMasksArray.forEach((mask, index) => {
        const className = boundingBoxData.classes[index];
        const classColor = classColorMap[className] || "rgb(0, 0, 0)";
        const [r, g, b] = classColor.match(/\d+/g)?.map(Number) ?? [0, 0, 0];
        const alpha = Math.round((pyTorchMaskOpacity / 100) * 255);

        mask.forEach((row, y) => {
          row.forEach((pixel, x) => {
            if (pixel === 1) {
              const offset = (y * image.width + x) * 4;
              data[offset] = r; // Red
              data[offset + 1] = g; // Green
              data[offset + 2] = b; // Blue
              data[offset + 3] = alpha; // Alpha
            }
          });
        });
      });

      maskCtx.putImageData(maskData, 0, 0);
      const bitmap = await createImageBitmap(maskCanvas);
      setCachedMaskImage(bitmap);
    };

    generateMaskBitmap();
  }, [
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
        ctx.drawImage(cachedMaskImage, 0, 0);
      }

      // Draw bounding boxes
      boundingBoxData.boxes.forEach((box, i) => {
        const [x, y, width, height] = box.map(Math.round);
        const className = boundingBoxData.classes[i];
        const accuracy = (boundingBoxData.scores[i] * 100).toFixed(1);

        // Get class color and apply opacity
        const classColor = classColorMap[className] || "rgb(0, 0, 0)";
        const [r, g, b] = classColor.match(/\d+/g)?.map(Number) ?? [0, 0, 0];
        const rgbaColor = `rgba(${r}, ${g}, ${b}, ${pyTorchOpacity / 100})`;

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
    image,
    boundingBoxData,
    cachedMaskImage,
    pyTorchBoxLineWidth,
    pyTorchBoxFontSize,
    pyTorchBoxXOffset,
    pyTorchBoxYOffset,
    pyTorchOpacity,
  ]);

  return (
    <div
      id="boundingBoxCanvasDiv"
      className="h-full flex"
      style={{ backgroundColor: "#272822" }}
    >
      {loading && (
        <div className="w-full flex justify-center">
          <LineWave height="100" width="100" color="green" />
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
