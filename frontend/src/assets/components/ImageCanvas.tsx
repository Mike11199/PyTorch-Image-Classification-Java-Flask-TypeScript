import { LineWave } from "react-loader-spinner";
import { useEffect } from "react";

interface ImageCanvasProps {
  loading: boolean;
  image?: any;
  boundingBoxData?: string;
}

const ImageCanvas = ({ loading, image, boundingBoxData }: ImageCanvasProps) => {
  const drawBoundingBoxes = (image: any, boundingBoxData: any) => {
    if (!image || !boundingBoxData) return;
    const canvas = document.getElementById(
      "boundingBoxCanvas"
    ) as HTMLCanvasElement;
    const ctx = canvas?.getContext("2d");

    if (!ctx) {
      //console.error("2D context not supported");
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
        ctx.strokeStyle = "red";
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, width - x, height - y);

        ctx.fillStyle = "red";
        ctx.font = "bold 12px Arial";
        ctx.fillText(
          `${formattedClassName} ${(accuracy * 100).toFixed(1)}% `,
          x + 5,
          y + 15
        );
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
    drawBoundingBoxes(image, boundingBoxData);
  }, [image, boundingBoxData]);

  return (
    <>
      <div
        id="boundingBoxCanvasDiv"
        className="mt-8 mx-44 h-[50rem] bg-black text-green-500 text-left flex justify-center align-middle"
      >
        {loading && (
          <div>
            <LineWave height="100" width="100" color="green" />
          </div>
        )}
        {!loading && (
          <canvas
            className=" object-contain  h-full w-full"
            id="boundingBoxCanvas"
          ></canvas>
        )}
      </div>
    </>
  );
};

export default ImageCanvas;
