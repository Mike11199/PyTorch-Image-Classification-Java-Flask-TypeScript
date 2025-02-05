import { useEffect, useState } from "react";
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
import { Toaster } from "react-hot-toast";
import { showWarningToast, showErrorToast } from "./FunctionUtils";


const MaskRCNNPage = () => {
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
  const [pyTorchMaskOpacity, setPyTorchMaskOpacity] = useState<number>(50);
  const [colorMapCounter, setColorMapCounter] = useState(0);
  const [pyTorchMasksArray, setPyTorchMasksArray] = useState<number[][][]>([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 365);
  const [activeSlider, setActiveSlider] = useState<string>("Mask Opacity");

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);


  const slidersConfig = [
    {
      name: "Mask Opacity",
      min: 0,
      max: 100,
      value: pyTorchMaskOpacity,
      setter: setPyTorchMaskOpacity,
    },
    {
      name: "Box Opacity",
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


  const [isError, setIsError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const pyTorchResultsFromImageBlob = async (imageBlob: Blob) => {
    // showWarningToast();
    setLoading(true);
    setIsError(false);

    try {
      const parsedPyTorchData = await fetchPyTorchAnalysis(
        imageBlob,
        "/api-java-spring-boot/image-url-pytorch-mask"
      );

      if (parsedPyTorchData) {
        const { masks_array, ...dataWithoutMasks } = parsedPyTorchData;
        setPyTorchMasksArray(masks_array || []);
        setPyTorchResponseObj(dataWithoutMasks);
        setPyTorchResponseString(JSON.stringify(dataWithoutMasks, null, 2));
      } else {
        setPyTorchResponseObj(null);
        setPyTorchResponseString("");
        setPyTorchMasksArray([]);
      }
      const imageURLFromBlob = await createImageURLFromBlob(imageBlob);
      setCanvasImage(imageURLFromBlob);
    } catch (error: any) {
      console.error("Error:", error?.response?.data);
      setErrorMessage(error?.response?.data);
      setIsError(true);

      setPyTorchResponseObj(null);
      setPyTorchResponseString("");
    } finally {
      setLoading(false);
    }
  };

  const fetchPyTorchAnalysisUsingImageURL = async (imageUrl: string) => {
    const imageBlob = await convertImageUrlToImage(imageUrl);
    if (!imageBlob) {
      showErrorToast("Please enter a valid image URL before submitting.");
      return;
    }
    await pyTorchResultsFromImageBlob(imageBlob);
  };

  const fetchPyTorchAnalysisUsingUploadedImage = async () => {
    if (uploadedImages.length === 0) {
      showErrorToast("Please upload an image before submitting.");
      return;
    }
    await pyTorchResultsFromImageBlob(uploadedImages[0]);
  };

  return (
    <>
      <Toaster />
      <div className="flex-1 flex-col bg-[linear-gradient(#263447_0%,#1e2938_10%,#1e2938_90%,#263447_100%)] pt-12 pb-12">
        <div className="text-sm text-white text-left mx-4 md:mx-44 mt-2 mb-16">
          <h1 className="font-bold mb-4 md:mb-4">App Description</h1>
          <div className="ml-2 md:ml-8">
            <li className="mb-4 md:mb-6">
              Use buttons below to send a request to a pre-trained PyTorch{" "}
              <strong className="text-red-700">maskrcnn_resnet50_fpn_v2</strong>{" "}
              computer vision model called by a custom{" "}
              <strong className="text-red-700">inference.py</strong> script.
            </li>
          </div>
          <h1 className="font-bold mb-4 md:mb-4 mt-14 md:mt-14">
            Model Description
          </h1>
          <div className="ml-2 md:ml-8">
            <li className="mb-4 md:mb-6">
              Mask R-CNN is an Instance Segmentation model. It identifies and
              generates a pixel-wide mask for each individual object in an
              image, clearly defining each object's boundaries. This is made
              possible by an extra "mask head" branch which uses Region of
              Interest Align (ROIAlign) pooling to extract features. It also
              incorporates object detection, outputting a bounding box in
              addition to the mask. This is unlike semantic segmentation, which
              does not distinguish between individual objects.
            </li>
          </div>
          <div className="w-full flex justify-center">
            <img
              className="my-4 flex w-[40rem] rounded-lg shadow-2xl"
              alt="faster-r-cnn-pipeline"
              src="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1736038071/instance_segmentation_qafce9.png"
            ></img>
          </div>
        </div>

        <DropZone
          setterUploadedImages={setUploadedImages}
          uploadedImages={uploadedImages}
          loading={loading}
        />

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
        {/* 
        <div className="w-full flex justify-center items-center mt-6 ">
          <strong className="text-red-700 text-center mx-4">
            Warning: this can take anywhere from 10 to 60 seconds while the
            model runs.
          </strong>
        </div> */}
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
        <div className="mt-4 flex flex-col justify-center md:flex-row md:mx-44">
          {isMobile ? (
            <div className="w-full flex flex-col items-center">
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
                className="md:w-2/12 flex justify-center text-white text-center md:text-left"
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
              pyTorchMaskOpacity={pyTorchMaskOpacity}
              pyTorchMasksArray={pyTorchMasksArray}
              isError={isError}
              errorMessage={errorMessage}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default MaskRCNNPage;
