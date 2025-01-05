import { LineWave } from "react-loader-spinner";
import { useEffect, useState, useMemo } from "react";
import { PyTorchImageResponseType } from "./types";
import { createClassColorMap } from "./FunctionUtils";

interface ImageCanvasProps {
  loading: boolean;
  image?: HTMLImageElement | undefined | null;
  boundingBoxData?: PyTorchImageResponseType | null;
  pyTorchBoxLineWidth: number;
  pyTorchBoxFontSize: number;
  pyTorchBoxXOffset: number;
  pyTorchBoxYOffset: number;
  colorMapCounter: number;
  pyTorchOpacity: number;
  pyTorchMaskOpacity?: number;
  pyTorchMasksArray?: number[][][];
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
  pyTorchMaskOpacity,
  pyTorchMasksArray
}: ImageCanvasProps) => {
  const [classColorMap, setClassColorMap] = useState(
    createClassColorMap(boundingBoxData)
  );

  // Update classColorMap when colorMapCounter or boundingBoxData changes
  useEffect(() => {
    setClassColorMap(createClassColorMap(boundingBoxData));
  }, [colorMapCounter, boundingBoxData]);

  // **Helper Function to Extract RGB Components**
  const extractRGB = (rgbString: string): string => {
    // Expected format: 'rgb(r, g, b)'
    const matches = rgbString?.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (matches) {
      const r = matches[1];
      const g = matches[2];
      const b = matches[3];
      return `${r}, ${g}, ${b}`;
    }
    return '0, 0, 0'; // Default to black if parsing fails
  };

  // **Cache the Mask Image Using useMemo**
  const cachedMaskImage = useMemo(() => {
    if (!pyTorchMasksArray || pyTorchMasksArray?.length === 0 || !image || !boundingBoxData || !pyTorchMaskOpacity) return null;

    // Create an off-screen canvas for mask rendering
    const maskCanvas = document.createElement('canvas');
    maskCanvas.width = image.width;
    maskCanvas.height = image.height;
    const maskCtx = maskCanvas.getContext('2d');
    if (!maskCtx) return null;

    // Iterate through each mask (assuming one mask per box)
    boundingBoxData?.boxes?.forEach((box, i) => {
      const className = boundingBoxData.classes[i];
      const classColor = classColorMap[className];
      const alpha = pyTorchMaskOpacity * 0.01; // Adjust opacity as needed

      const mask = pyTorchMasksArray[i];
      if (!mask) return;

      const rgb = extractRGB(classColor);

      mask?.forEach((row, y) => {
        row?.forEach((pixel, x) => {
          if (pixel === 1) {
            // Correctly construct RGBA string
            maskCtx.fillStyle = `rgba(${rgb}, ${alpha})`;
            maskCtx.fillRect(x, y, 1, 1);
          }
        });
      });
    });

    // Convert the mask canvas to a data URL
    return maskCanvas.toDataURL();
  }, [pyTorchMasksArray, boundingBoxData, classColorMap, image, pyTorchMaskOpacity]);

  // **Function to Draw Bounding Boxes and Overlay Masks**
  const drawBoundingBoxes = (
    image: HTMLImageElement | undefined | null,
    boundingBoxData: PyTorchImageResponseType | null,
    cachedMaskImage: string | null
  ) => {
    if (!image || !boundingBoxData) return;
    const canvas = document.getElementById(
      "boundingBoxCanvas"
    ) as HTMLCanvasElement;
    const ctx = canvas?.getContext("2d");

    if (!ctx) {
      return;
    }

    // Set canvas dimensions
    canvas.height = image.height;
    canvas.width = image.width;

    // Draw the base image
    ctx.drawImage(image, 0, 0);

    // **Draw the Cached Mask Image**
    if (cachedMaskImage) {
      const maskImg = new Image();
      maskImg.src = cachedMaskImage;
      maskImg.onload = () => {
        ctx.drawImage(maskImg, 0, 0);
        // After drawing masks, draw bounding boxes
        drawBoundingBoxesOverlays(ctx, boundingBoxData);
      };
    } else {
      // If no masks, just draw bounding boxes
      drawBoundingBoxesOverlays(ctx, boundingBoxData);
    }
  };

  // **Separate Function to Draw Bounding Boxes and Labels**
  const drawBoundingBoxesOverlays = (
    ctx: CanvasRenderingContext2D,
    boundingBoxData: PyTorchImageResponseType
  ) => {
    for (let i = 0; i < boundingBoxData.boxes.length; i++) {
      const box = boundingBoxData.boxes[i];
      const className = boundingBoxData.classes[i];
      const accuracy = boundingBoxData.scores[i];
      const formattedClassName =
        className.charAt(0).toUpperCase() + className.slice(1).toLowerCase();

      const [x, y, width, height] = box.map((value: number) => value);
      if (!isNaN(x) && !isNaN(y) && !isNaN(width) && !isNaN(height)) {
        const classColor = classColorMap[className];

        const alpha = pyTorchOpacity * 0.01;
        if (classColor) {
          const rgb = extractRGB(classColor);
          ctx.strokeStyle = `rgba(${rgb}, ${alpha})`;
          ctx.fillStyle = `rgba(${rgb}, ${alpha})`;
        }
        ctx.lineWidth = pyTorchBoxLineWidth;
        ctx.strokeRect(x, y, width - x, height - y);

        ctx.font = `bold ${pyTorchBoxFontSize}px Arial`;
        ctx.fillText(
          `${formattedClassName} ${(accuracy * 100).toFixed(1)}% `,
          x + pyTorchBoxXOffset,
          y + pyTorchBoxYOffset
        );
      }
    }
  };

  // **Function to Clear the Canvas**
  function clearCanvas() {
    const canvas = document.getElementById(
      "boundingBoxCanvas"
    ) as HTMLCanvasElement;
    const ctx = canvas?.getContext("2d");

    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  // **Clear Canvas When Loading State Changes**
  useEffect(() => {
    clearCanvas();
  }, [loading]);

  // **Draw Bounding Boxes and Masks When Dependencies Change**
  useEffect(() => {
    drawBoundingBoxes(image, boundingBoxData ?? null, cachedMaskImage);
  }, [
    image,
    boundingBoxData,
    pyTorchBoxLineWidth,
    pyTorchBoxFontSize,
    pyTorchBoxXOffset,
    pyTorchBoxYOffset,
    colorMapCounter,
    classColorMap,
    pyTorchOpacity,
    cachedMaskImage
  ]);

  return (
    <>
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
        {!loading && (
          <canvas
            className="object-contain h-full w-full"
            id="boundingBoxCanvas"
          ></canvas>
        )}
      </div>
    </>
  );
};

export default ImageCanvas;
