import { useState } from "react";
import DropZone from "./Dropzone";
import Button from "./Button";
import ImageCanvas from "./ImageCanvas";
import {
  createImageURLFromBlob,
  convertImageUrlToImage,
} from "./FunctionUtils";
import JSONBox from "./JSONBox";
import ImageURL from "./ImageURL";
import { PyTorchImageResponseType } from "./types";
import { fetchPyTorchAnalysis } from "./FunctionUtils";
import PyTorchSlider from "./Slider";

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
  const [pyTorchBoxLineWidth, setPyTorchBoxLineWidth] = useState<number>(2);
  const [pyTorchBoxFontSize, setPyTorchBoxFontSize] = useState<number>(12);
  const [pyTorchBoxXOffset, setPyTorchBoxXOffset] = useState<number>(5);
  const [pyTorchBoxYOffset, setPyTorchBoxYOffset] = useState<number>(15);

  const pyTorchResultsFromImageBlob = async (imageBlob: Blob) => {
    setLoading(true);
    const parsedPyTorchData = await fetchPyTorchAnalysis(imageBlob);
    setPyTorchResponseObj(parsedPyTorchData ?? null);
    setPyTorchResponseString(JSON.stringify(parsedPyTorchData, null, 2));
    const imageURLFromBlob = await createImageURLFromBlob(imageBlob);
    setCanvasImage(imageURLFromBlob);
    setLoading(false);
  };

  const fetchPyTorchAnalysisUsingImageURL = async (imageUrl: string) => {
    const imageBlob = await convertImageUrlToImage(imageUrl);
    if (!imageBlob) {
      alert("Please enter a valid image URL before submitting.");
      return;
    }
    await pyTorchResultsFromImageBlob(imageBlob);
  };

  const fetchPyTorchAnalysisUsingUploadedImage = async () => {
    if (uploadedImages.length === 0) {
      alert("Please upload an image before submitting.");
      return;
    }
    await pyTorchResultsFromImageBlob(uploadedImages[0]);
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
            buttonOnClick={fetchPyTorchAnalysisUsingUploadedImage}
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
        <div className="mt-4 flex flex-col justify-center md:flex-row md:mx-44">
          <div className=" md:w-1/4 flex justify-center text-white">
            <PyTorchSlider
              setterValue={pyTorchBoxLineWidth}
              setterFunction={setPyTorchBoxLineWidth}
              sliderName={"Box Line Width"}
            />
          </div>
          <div className=" md:w-1/4 flex justify-center text-white">
            <PyTorchSlider
              setterValue={pyTorchBoxFontSize}
              setterFunction={setPyTorchBoxFontSize}
              sliderName={"Label Font Size"}
            />
          </div>
          <div className=" md:w-1/4 flex justify-center text-white">
            <PyTorchSlider
              setterValue={pyTorchBoxXOffset}
              setterFunction={setPyTorchBoxXOffset}
              sliderName={"Label X Offset"}
            />
          </div>
          <div className=" md:w-1/4 flex justify-center text-white">
            <PyTorchSlider
              setterValue={pyTorchBoxYOffset}
              setterFunction={setPyTorchBoxYOffset}
              sliderName={"Label Y Offset"}
            />
          </div>
        </div>
        <div className="flex flex-col md:flex-row mt-4 mx-4 md:mx-44 h-[50rem]">
          <div className="w-full md:w-2/12 h-[25rem] md:h-full md:mb-0 mb-8 md:mr-8">
            <JSONBox
              loading={loading}
              pyTorchImageResponseString={pyTorchResponseString}
            />
          </div>
          <div className="w-full md:w-10/12 h-[25rem] md:h-full">
            <ImageCanvas
              pyTorchBoxXOffset={pyTorchBoxXOffset}
              pyTorchBoxYOffset={pyTorchBoxYOffset}
              pyTorchBoxFontSize={pyTorchBoxFontSize}
              pyTorchBoxLineWidth={pyTorchBoxLineWidth}
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
