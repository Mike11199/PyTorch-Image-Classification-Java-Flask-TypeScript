import axios from "axios";
import { useState } from "react";
import { LineWave } from "react-loader-spinner";
import DropZone from "./Dropzone";
import Button from "./Button";
import ImageCanvas from "./ImageCanvas";
import { convertImageUrlToImage, createImageURLFromBlob } from "./utils";

const HomePage = () => {
  const [inputValue, setInputValue] = useState(
    "https://images.saymedia-content.com/.image/t_share/MjAxMjg4MjkxNjI5MTQ3Njc1/labrador-retriever-guide.jpg"
  );
  const [pyTorchImageResponse, setPyTorchImageResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<any>([]);
  const [canvasImage, setCanvasImage] = useState<any>(null);

  const boundingBoxData = pyTorchImageResponse
    ? JSON.parse(pyTorchImageResponse)
    : null;

  const fetchPyTorchAnalysis = async (imageBlob: any) => {
    setLoading(true);
    setPyTorchImageResponse("");

    try {
      const formData = new FormData();
      formData.append("image", imageBlob, "image.jpg");
      const response = await axios.post("/api/image-url-pytorch", formData);
      setPyTorchImageResponse(JSON.stringify(response?.data, null, 2));
      const imageURLFromBlob = await createImageURLFromBlob(imageBlob);
      setCanvasImage(imageURLFromBlob);
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

    if (!imageBlob) {
      alert("Please enter a valid image URL before submitting.");
      return;
    }
    await fetchPyTorchAnalysis(imageBlob);
  };

  const handleSubmitUploadedImageButton = async () => {
    if (uploadedImages.length === 0) {
      alert("Please upload an image before submitting.");
      return;
    }
    await fetchPyTorchAnalysis(uploadedImages[0]);
  };

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
          <Button
            buttonOnClick={handleSubmitUploadedImageButton}
            loading={loading}
            buttonText={"Submit Image File"}
          />
        </div>

        <div className="text-sm text-white mb-8 font-semibold">
          OR Enter an Image URL below
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
        <Button
          buttonOnClick={() => fetchPyTorchAnalysisUsingImageURL(inputValue)}
          loading={loading}
          buttonText={"Submit Image URL"}
        />

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
              City Crosswalk
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
        <ImageCanvas
          loading={loading}
          image={canvasImage}
          boundingBoxData={boundingBoxData}
        />
      </div>
    </>
  );
};

export default HomePage;
