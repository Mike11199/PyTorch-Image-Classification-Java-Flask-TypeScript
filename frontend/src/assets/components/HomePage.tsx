import axios from "axios";
import { useState } from "react";
import { LineWave, ColorRing } from "react-loader-spinner";
import DropZone from "./Dropzone";

const HomePage = () => {
  const [inputValue, setInputValue] = useState(
    "https://images.saymedia-content.com/.image/t_share/MjAxMjg4MjkxNjI5MTQ3Njc1/labrador-retriever-guide.jpg"
  );
  const [pyTorchImageResponse, setPyTorchImageResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<any>([]);

  function clearCanvas() {
    const canvas = document.getElementById(
      "boundingBoxCanvas"
    ) as HTMLCanvasElement;
    const ctx = canvas?.getContext("2d");

    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  const fetchPyTorchAnalysis = async (imageBlob: any) => {
    setLoading(true);
    setPyTorchImageResponse("");
    clearCanvas();

    try {
      const formData = new FormData();
      formData.append("image", imageBlob, "image.jpg");
      console.log(imageBlob);
      const response = await axios.post("/api/image-url-pytorch", formData);
      const jsonString = JSON.stringify(response?.data, null, 2);
      setPyTorchImageResponse(jsonString);
      // draw image on canvas
      const image = new Image();
      const imageUrl = URL.createObjectURL(imageBlob);
      image.src = imageUrl;
      image.onload = () => drawBoundingBoxes(image, response?.data);
      return response?.data;
    } catch (error: any) {
      console.error("Error:", error.message);
      if (error.response) {
        console.error("Response Data:", error.response.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchPyTorchAnalysisUsingImageURL = async (imageUrl: string) => {
    const imageBlob = await convertImageUrlToImage(imageUrl);
    await fetchPyTorchAnalysis(imageBlob);
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

  async function convertImageUrlToImage(imageUrl: any) {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      return blob;
    } catch (error) {
      console.error("Error converting image to base64:", error);
      throw error;
    }
  }

  return (
    <>
      <div className="min-h-screen h-auto bg-slate-700 pt-8 pb-12">
        <div className="text-sm text-white text-left mx-44 mb-14 mt-14">
          <li>
            Use buttons below to send a request to a pre-trained PyTorch{" "}
            <strong className="text-red-700">fasterrcnn_resnet50_fpn_v2</strong>{" "}
            computer vision model called by a custom{" "}
            <strong className="text-red-700">inference.py</strong> script.
          </li>
          <li>
            Model is deployed to a SageMaker HTTP Endpoint. The express server
            calls an AWS API Gateway, which in turn calls a lambda to invoke the
            SageMaker endpoint.
          </li>
        </div>

        <DropZone
          setterUploadedImages={setUploadedImages}
          uploadedImages={uploadedImages}
          loading={loading}
        />
        <div className="mt-8 mb-16">
          <button
            className="bg-red-800 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-sm w-72"
            onClick={() => fetchPyTorchAnalysis(uploadedImages[0])}
          >
            <div className="flex justify-center items-center gap-4">
              Submit Uploaded Image File
              {loading && (
                <ColorRing
                  height="20"
                  width="20"
                  colors={[
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                  ]}
                />
              )}
            </div>
          </button>
        </div>

        <div className="text-sm text-white mb-8 font-semibold">
          OR Enter an Image URL below
        </div>
        <div id="toast"></div>
        <div className="flex justify-center gap-24 w-full">
          <input
            className="mb-8 w-full mx-44"
            type="text"
            id="inputField"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
        </div>
        <div className="flex justify-center gap-14">
          <button
            onClick={() => fetchPyTorchAnalysisUsingImageURL(inputValue)}
            className="bg-red-800 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-sm w-72"
          >
            <div className="flex justify-center items-center gap-4">
              Submit Image URL
              {loading && (
                <ColorRing
                  height="20"
                  width="20"
                  colors={[
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                  ]}
                />
              )}
            </div>
          </button>
        </div>
        <div className="text-white text-left mx-44 mt-12">
          <label htmlFor="cars">Choose a pre-selected image URL</label>
          <select
            onChange={(e) => setInputValue(e.target.value)}
            className="text-black ml-6"
            id="image_url_options"
            name="image_url_options"
          >
            <option
              selected
              value="https://images.saymedia-content.com/.image/t_share/MjAxMjg4MjkxNjI5MTQ3Njc1/labrador-retriever-guide.jpg"
            >
              Labrador
            </option>
            <option value="https://upload.wikimedia.org/wikipedia/commons/b/bc/Elephant.jpg">
              Elephant
            </option>
            <option value="https://i.guim.co.uk/img/media/00cbd8cdb8ef7ff8e89fcd835f1cd0fa6adce5f6/8_0_2544_1527/master/2544.jpg?width=1200&quality=85&auto=format&fit=max&s=24e5c33c75542aba0cce59b3fe05b79a">
              Cats and Dogs
            </option>
            <option value="https://images.unsplash.com/photo-1602940659805-770d1b3b9911?q=80&w=1932&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D">
              Times Square
            </option>
          </select>
        </div>
        <div className="mt-8 mx-44 h-40 overflow-auto bg-black text-green-500 text-left flex justify-center align-middle">
          {loading && (
            <div>
              <LineWave height="100" width="100" color="green" />
            </div>
          )}
          {!loading && pyTorchImageResponse}
        </div>
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
      </div>
    </>
  );
};

export default HomePage;
