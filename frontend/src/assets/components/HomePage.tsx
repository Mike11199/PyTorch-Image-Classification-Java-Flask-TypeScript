import axios from "axios";
import { useState } from "react";
import DropZone from "./Dropzone";
import Button from "./Button";
import ImageCanvas from "./ImageCanvas";
import {
  createImageURLFromBlob,
  convertImageUrlToImage,
  trimPytorchDataObject,
} from "./FunctionUtils";
import JSONBox from "./JSONBox";
import ImageURL from "./ImageURL";
import { PyTorchImageResponseType } from "./types";

const HomePage = () => {
  const [inputValue, setInputValue] = useState(
    "https://images.saymedia-content.com/.image/t_share/MjAxMjg4MjkxNjI5MTQ3Njc1/labrador-retriever-guide.jpg"
  );
  const [pyTorchResponseObj, setPyTorchResponseObj] =
    useState<PyTorchImageResponseType | null>(null);
  const [pyTorchResponseString, setPyTorchResponseString] =
    useState<string>("");
  const [loading, setLoading] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<Blob[]>([]);
  const [canvasImage, setCanvasImage] = useState<HTMLImageElement | null>(null);

  const fetchPyTorchAnalysis = async (imageBlob: Blob) => {
    setLoading(true);
    setPyTorchResponseString("");
    setPyTorchResponseObj(null);

    try {
      const formData = new FormData();
      formData.append("image", imageBlob, "image.jpg");
      const response = await axios.post("/api/image-url-pytorch", formData);
      const parsedPyTorchData = trimPytorchDataObject(response?.data) ?? null;
      setPyTorchResponseObj(parsedPyTorchData);
      setPyTorchResponseString(JSON.stringify(parsedPyTorchData, null, 2));
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
      <div className="min-h-screen h-auto bg-slate-700 pt-12 pb-12">
        <div className="text-sm text-white text-left mx-4 md:mx-44 mt-4 mb-16">
          <li className="mb-4 md:mb-0">
            Use buttons below to send a request to a pre-trained PyTorch{" "}
            <strong className="text-red-700">fasterrcnn_resnet50_fpn_v2</strong>{" "}
            computer vision model called by a custom{" "}
            <strong className="text-red-700">inference.py</strong> script.
          </li>
          <li className="mb-4 md:mb-0">
            Model is deployed to a SageMaker HTTP endpoint. The Express.js
            server calls an AWS API Gateway endpoint via Axios with binary image
            data included directly in the request body.
          </li>
          <li className="mb-4 md:mb-0">
            The API Gateway then calls a lambda, which converts the raw image
            data to base64 and sends it directly to the PyTorch model.
          </li>
          <li className="mb-4 md:mb-0">
            In the <strong className="text-red-700">inference.py</strong>{" "}
            script, I decode the base64 image data to a NumPy array, then to a
            tensor with Torch, as input for the model.
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

        <ImageURL
          urlInputValue={inputValue}
          setterURLInputValue={setInputValue}
        />
        <Button
          buttonOnClick={() => fetchPyTorchAnalysisUsingImageURL(inputValue)}
          loading={loading}
          buttonText={"Submit Image URL"}
        />
        <div className="flex flex-col md:flex-row mt-16 mx-4 md:mx-44 h-[50rem]">
          <div className="w-full md:w-2/12 h-[25rem] md:h-full md:mb-0 mb-8 md:mr-8">
            <JSONBox
              loading={loading}
              pyTorchImageResponseString={pyTorchResponseString}
            />
          </div>
          <div className="w-full md:w-10/12 h-[25rem] md:h-full">
            <ImageCanvas
              loading={loading}
              image={canvasImage}
              boundingBoxData={pyTorchResponseObj}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default HomePage;
