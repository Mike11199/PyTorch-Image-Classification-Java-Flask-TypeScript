import axios from "axios";
import { useState, useEffect } from "react";
import { LineWave } from "react-loader-spinner";

const HomePage = () => {
  const [inputValue, setInputValue] = useState("");
  const [pyTorchImageResponse, setPyTorchImageResponse] = useState("");
  const [imageSrc, setImageSrc] = useState<any>(null);
  const [boundingBoxes, setBoundingBoxes] = useState<any>([]);
  const [loading, setLoading] = useState(false);

  const sampleImageUrl =
    "https://images.freeimages.com/images/large-previews/bd1/cat-1404368.jpg";

  function clearCanvas() {
    const canvas = document.getElementById(
      "boundingBoxCanvas"
    ) as HTMLCanvasElement;
    const ctx = canvas?.getContext("2d");

    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  const fetchPyTorchAnalysisUsingImageURL = async (imageUrl: string) => {
    setLoading(true);
    setImageSrc(null);
    setBoundingBoxes([]);
    setPyTorchImageResponse("");
    clearCanvas();

    try {
      const response = await axios.post("/api/image-url-pytorch", {
        imageUrl: imageUrl,
      });
      const jsonString = JSON.stringify(response?.data, null, 2); // the third argument (2) adds indentation for better readability
      console.log("Response:", jsonString);
      setPyTorchImageResponse(jsonString);
      setBoundingBoxes(response?.data);
      setImageSrc(imageUrl);
    } catch (error: any) {
      console.error("Error:", error.message);
    } finally {
      setLoading(false);
    }
  };

  const drawBoundingBoxes = (image: any, boundingBoxData: any) => {
    const canvas = document.getElementById(
      "boundingBoxCanvas"
    ) as HTMLCanvasElement;
    const ctx = canvas?.getContext("2d");

    if (!ctx) {
      console.error("2D context not supported");
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

  useEffect(() => {
    if (imageSrc) {
      const image = new Image();
      image.src = imageSrc;
      image.onload = () => drawBoundingBoxes(image, boundingBoxes);
    }
  }, [imageSrc, boundingBoxes]);

  return (
    <>
      <div className="min-h-screen h-auto bg-slate-700 pt-8 pb-12">
        <div className="text-sm text-white text-left mx-44 mb-14 mt-14">
          <li>
            Use buttons below to send a request to a pre-trained PyTorch{" "}
            <strong className="text-red-700">fasterrcnn_resnet50_fpn_v2</strong>{" "}
            computer vision model called by a custom inference.py script.
          </li>
          <li>
            Model is deployed to a SageMaker HTTP Endpoint. The express server
            calls an AWS API Gateway, which in turn calls a lambda to invoke the
            SageMaker endpoint.
          </li>
        </div>
        <div className="text-sm text-white mb-4 font-semibold">
          Enter an Image URL below
        </div>
        <div className="flex justify-center gap-24 w-full">
          <input
            className="mb-8 w-full mx-44"
            type="text"
            id="inputField"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
        </div>
        <div className="flex justify-center  gap-24">
          <button
            onClick={() => fetchPyTorchAnalysisUsingImageURL(sampleImageUrl)}
            className="bg-red-800 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-sm"
          >
            Use Sample Image URL
          </button>
          <button
            onClick={() => fetchPyTorchAnalysisUsingImageURL(inputValue)}
            className="bg-blue-800 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded text-sm"
          >
            Submit Image URL
          </button>
        </div>
        <div className="text-white text-left mx-44 mt-12">
          Examples
          <li>
            https://upload.wikimedia.org/wikipedia/commons/b/bc/Elephant.jpg
          </li>
          <li>
            https://images.saymedia-content.com/.image/t_share/MjAxMjg4MjkxNjI5MTQ3Njc1/labrador-retriever-guide.jpg
          </li>
          <li>
            https://i.guim.co.uk/img/media/00cbd8cdb8ef7ff8e89fcd835f1cd0fa6adce5f6/8_0_2544_1527/master/2544.jpg?width=1200&quality=85&auto=format&fit=max&s=24e5c33c75542aba0cce59b3fe05b79a
          </li>
        </div>
        <div className="mt-8 mx-44 h-40 overflow-auto bg-black text-lime-400 text-left flex justify-center align-middle">
          {loading && (
            <div>
              <LineWave height="100" width="100" color="green" />
            </div>
          )}
          {!loading && pyTorchImageResponse}
        </div>
        <div
          id="boundingBoxCanvasDiv"
          className="mt-8 mx-44 h-[50rem] bg-black text-lime-400 text-left flex justify-center align-middle"
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
      </div>
    </>
  );
};

export default HomePage;
