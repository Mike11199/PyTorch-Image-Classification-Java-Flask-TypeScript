import { useState, useEffect } from "react";
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
import PyTorchSlider from "./PyTorchSlider";

const ImageClassificationPage = () => {
  const [inputValue, setInputValue] = useState(
    "https://res.cloudinary.com/dwgvi9vwb/image/upload/v1737100366/labrador_retriever_xi8k9z.jpg"
  );
  const [pyTorchResponseObj, setPyTorchResponseObj] =
    useState<PyTorchImageResponseType | null>(null);
  const [pyTorchResponseString, setPyTorchResponseString] =
    useState<string>("");
  const [loading, setLoading] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<Blob[]>([]);
  const [canvasImage, setCanvasImage] = useState<HTMLImageElement | null>(null);
  const [pyTorchBoxLineWidth, setPyTorchBoxLineWidth] = useState<number>(3);
  const [pyTorchBoxFontSize, setPyTorchBoxFontSize] = useState<number>(12);
  const [pyTorchBoxXOffset, setPyTorchBoxXOffset] = useState<number>(5);
  const [pyTorchBoxYOffset, setPyTorchBoxYOffset] = useState<number>(15);
  const [pyTorchOpacity, setPyTorchOpacity] = useState<number>(100);
  const [colorMapCounter, setColorMapCounter] = useState(0);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [activeSlider, setActiveSlider] = useState<string>("Opacity");

  const [isError, setIsError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const slidersConfig = [
    {
      name: "Opacity",
      min: 0,
      max: 100,
      value: pyTorchOpacity,
      setter: setPyTorchOpacity,
    },
    {
      name: "Box Line Width",
      min: 1,
      max: 20,
      value: pyTorchBoxLineWidth,
      setter: setPyTorchBoxLineWidth,
    },
    {
      name: "Label Font Size",
      min: 1,
      max: 65,
      value: pyTorchBoxFontSize,
      setter: setPyTorchBoxFontSize,
    },
    {
      name: "Label X Offset",
      min: -200,
      max: 200,
      value: pyTorchBoxXOffset,
      setter: setPyTorchBoxXOffset,
    },
    {
      name: "Label Y Offset",
      min: -200,
      max: 200,
      value: pyTorchBoxYOffset,
      setter: setPyTorchBoxYOffset,
    },
  ];

  const selectedSlider = slidersConfig.find((slider) => slider.name === activeSlider);

  const pyTorchResultsFromImageBlob = async (imageBlob: Blob) => {
    try {
      setLoading(true);
      setIsError(false);
      const parsedPyTorchData = await fetchPyTorchAnalysis(
        imageBlob,
        "/api-java-spring-boot/image-url-pytorch"
      );
      setPyTorchResponseObj(parsedPyTorchData ?? null);
      setPyTorchResponseString(JSON.stringify(parsedPyTorchData, null, 2));
      const imageURLFromBlob = await createImageURLFromBlob(imageBlob);
      setCanvasImage(imageURLFromBlob);
      setLoading(false);
    } catch (error: any) {
      console.error("Error:", error?.response?.data);
      setErrorMessage(error?.response?.data);
      setIsError(true);

      setPyTorchResponseObj(null);
      setPyTorchResponseString("");
      setLoading(false);
    }
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
      <div className="flex-1 flex-col bg-slate-700 pt-12 pb-12">
        {/* Description and Info */}
        <div className="text-sm text-white text-left mx-4 md:mx-44 mt-2 mb-16">

        <h1 className="font-bold mb-4 md:mb-4">App Description</h1>
          <div className="ml-2 md:ml-8">
            <li className="mb-4 md:mb-6">
              Use buttons below to send a request to a pre-trained PyTorch{" "}
              <strong className="text-red-700">
                fasterrcnn_resnet50_fpn_v2
              </strong>{" "}
              computer vision model called by a custom{" "}
              <strong className="text-red-700">inference.py</strong> script.
            </li>
          </div>
          <h1 className="font-bold mb-4 md:mb-4 mt-14 md:mt-14">
            Model Description
          </h1>
          <div className="ml-2 md:ml-8">
            <li className="mb-4 md:mb-6">
              Faster R-CNN is an acronym for a Region-based CNN (Convolutional
              Neural Network). It utilizes a ResNet-50 (50 layer Residual
              Network) as the CNN backbone. The backbone incorporates a FPN
              (Feature Pyramid Network) for feature extraction from each image.
              A RPN (Region Proposal Network) slides a small CNN over the
              feature map to generate region proposals, which represent
              potential objects of interest.
            </li>
          </div>
          <div className="w-full flex justify-center">
            <img
              className="my-8 flex w-[70rem] rounded-lg shadow-2xl"
              alt="faster-r-cnn-pipeline"
              src="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703965451/faster_rcnn_o7riso.png"
            ></img>
          </div>
          <div className="ml-2 md:ml-8">
            <li className="mb-4 md:mb-6">
              Region of Interest (ROI) pooling is then applied to these regions
              to generate fixed-size feature maps. These feature maps are passed
              to two separate branches in the network, the box head, responsible
              for generate bounding box coordinates, and a class head, used to
              predict class labels of objects. After this process, class
              labels/scores and bounding boxes for detected objects are returned
              from the model.
            </li>
          </div>
          <h1 className="font-bold mb-4 md:mb-4 mt-14 md:mt-14">
            Model Deployment
          </h1>
          <div className="ml-2 md:ml-8">
            <li className="mb-4 md:mb-4">
              The model and{" "}
              <strong className="text-red-700">inference.py</strong> script is
              provisioned on a Flask microservice running in an EC2. A Java
              Spring Boot API takes requests from the front end and sends an
              image as multipart form-data to the model. The Flask endpoint
              converts this data into a NumPy array, and normalizes its pixel
              values for input into the PyTorch model. Inference results from
              the model are then returned as JSON to the front end to be plotted
              on the image.
            </li>
          </div>
        </div>

        {/* DropZone */}
        <DropZone
          setterUploadedImages={setUploadedImages}
          uploadedImages={uploadedImages}
          loading={loading}
        />

        {/* Buttons */}
        <div className="mt-8 flex gap-4 flex-col">
          <Button
            color={"bg-red-900"}
            hoverColor={"hover:bg-red-800"}
            buttonOnClick={fetchPyTorchAnalysisUsingUploadedImage}
            loading={loading}
            buttonText={"Submit Image File"}
          />
          <Button
            color={"bg-red-900"}
            hoverColor={"hover:bg-red-800"}
            buttonOnClick={() => fetchPyTorchAnalysisUsingImageURL(inputValue)}
            loading={loading}
            buttonText={"Submit Image URL"}
          />
        </div>

        <ImageURL
          urlInputValue={inputValue}
          setterURLInputValue={setInputValue}
        />

        {/* Warning */}
        <div className="w-full flex justify-center items-center mt-6 ">
          <strong className="text-red-700 text-center mx-4">
            Warning: this can take anywhere from 10 to 60 seconds while the model runs.
          </strong>
        </div>

        {/* Regenerate Colors */}
        <div className="mt-16">
          <Button
            color={"bg-gray-900"}
            hoverColor={"hover:bg-gray-800"}
            buttonOnClick={() =>
              setColorMapCounter((prevCounter) => prevCounter + 1)
            }
            buttonText={"Regenerate Colors"}
          />
        </div>

        {/* Sliders */}
        <div className="mt-4 flex flex-col justify-center md:flex-row md:mx-44">
          {isMobile ? (
            <div className="w-full flex flex-col items-center">
              {/* Dropdown */}
              <select
                value={activeSlider}
                onChange={(e) => setActiveSlider(e.target.value)}
                className="mb-4 p-2 bg-gray-900 text-white rounded w-60 text-center font-bold text-sm transition-transform duration-300 ease-linear"
              >
                {slidersConfig.map((slider) => (
                  <option key={slider.name} value={slider.name}>
                    {slider.name}
                  </option>
                ))}
              </select>

              {/* Single Slider */}
              {selectedSlider && (
                <PyTorchSlider
                  minValue={selectedSlider.min}
                  maxValue={selectedSlider.max}
                  setterValue={selectedSlider.value}
                  setterFunction={selectedSlider.setter}
                  sliderName={selectedSlider.name}
                />
              )}
            </div>
          ) : (
            // Desktop: Show all sliders
            slidersConfig.map((slider) => (
              <div
                key={slider.name}
                className="md:w-2/12 flex justify-center text-white"
              >
                <PyTorchSlider
                  minValue={slider.min}
                  maxValue={slider.max}
                  setterValue={slider.value}
                  setterFunction={slider.setter}
                  sliderName={slider.name}
                />
              </div>
            ))
          )}
        </div>

        {/* JSONBox and ImageCanvas */}
        <div className="flex flex-col md:flex-row gap-8 mt-4 mx-4 md:mx-44 h-[50rem]">
          <div className="w-full md:w-2/12 h-[25rem] md:h-full order-last md:order-first">
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
              colorMapCounter={colorMapCounter}
              pyTorchOpacity={pyTorchOpacity}
              isError={isError}
              errorMessage={errorMessage}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default ImageClassificationPage;
