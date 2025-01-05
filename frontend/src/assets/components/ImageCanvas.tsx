import { LineWave } from "react-loader-spinner";
import { useEffect, useState } from "react";
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
  pyTorchMasksArray: number[][][];
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
  pyTorchMasksArray
}: ImageCanvasProps) => {
  const [classColorMap, setClassColorMap] = useState(
    createClassColorMap(boundingBoxData)
  );

  useEffect(() => {
    setClassColorMap(createClassColorMap(boundingBoxData));
    drawBoundingBoxes(image, boundingBoxData ?? null);
  }, [colorMapCounter, boundingBoxData]);



const drawBoundingBoxes = (
  image: HTMLImageElement | undefined | null,
  boundingBoxData: PyTorchImageResponseType | null
) => {
  if (!image || !boundingBoxData) return;
  const canvas = document.getElementById(
    "boundingBoxCanvas"
  ) as HTMLCanvasElement;
  const ctx = canvas?.getContext("2d");

  if (!ctx) {
    return;
  }

  canvas.height = image.height;
  canvas.width = image.width;

  ctx.drawImage(image, 0, 0);

  for (let i = 0; i < boundingBoxData.boxes.length; i++) {
    const box = boundingBoxData?.boxes[i];
    const className = boundingBoxData?.classes[i];
    const accuracy = boundingBoxData?.scores[i];
    const formattedClassName =
      className.charAt(0).toUpperCase() + className.slice(1).toLowerCase();

    const [x, y, width, height] = box.map((value: number) => value);
    if (!isNaN(x) && !isNaN(y) && !isNaN(width) && !isNaN(height)) {
      const classColor = classColorMap[className];

      const alpha = pyTorchOpacity * 0.01;
      if (classColor) {
        ctx.strokeStyle = `rgba${classColor.slice(3, -1)},${alpha})`;
        ctx.fillStyle = `rgba${classColor.slice(3, -1)},${alpha})`;
      }
      ctx.lineWidth = pyTorchBoxLineWidth;
      ctx.strokeRect(x, y, width - x, height - y);

      ctx.font = `bold ${pyTorchBoxFontSize}px Arial`;
      ctx.fillText(
        `${formattedClassName} ${(accuracy * 100).toFixed(1)}% `,
        x + pyTorchBoxXOffset,
        y + pyTorchBoxYOffset
      );

      // **Add Mask Drawing Here**
      if (pyTorchMasksArray && pyTorchMasksArray[i]) { // Ensure mask exists for this box
        const mask = pyTorchMasksArray[i];
        for (let row = 0; row < mask.length; row++) {
          for (let col = 0; col < mask[row].length; col++) {
            if (mask[row][col] === 1) {
              // Use the same class color with adjusted opacity for the mask
              ctx.fillStyle = `rgba${classColor.slice(3, -1)},${alpha * 0.5})`; // 50% opacity
              ctx.fillRect(col, row, 1, 1); // Draw pixel
            }
          }
        }
      }
      // **End of Mask Drawing**
    }
  }
};

  function clearCanvas() {
    const canvas = document.getElementById(
      "boundingBoxCanvas"
    ) as HTMLCanvasElement;
    const ctx = canvas?.getContext("2d");

    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  useEffect(() => {
    clearCanvas();
  }, [loading]);

  useEffect(() => {
    drawBoundingBoxes(image, boundingBoxData ?? null);
  }, [
    image,
    boundingBoxData,
    pyTorchBoxLineWidth,
    pyTorchBoxFontSize,
    pyTorchBoxXOffset,
    pyTorchBoxYOffset,
    colorMapCounter,
    classColorMap,
    pyTorchOpacity
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
            className=" object-contain h-full w-full"
            id="boundingBoxCanvas"
          ></canvas>
        )}
      </div>
    </>
  );
};

export default ImageCanvas;
