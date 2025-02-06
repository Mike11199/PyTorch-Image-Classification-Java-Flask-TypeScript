import { useState } from "react";
import ImageCanvas from "./ImageCanvas";
import {
  createImageURLFromBlob,
  convertImageUrlToImage,
} from "./FunctionUtils";
import JSONBox from "./JSONBox";
import { PyTorchImageResponseType } from "./types";
import { fetchPyTorchAnalysis } from "./FunctionUtils";
import { Toaster } from "react-hot-toast";
import { showErrorToast } from "./FunctionUtils";
import { DropzoneContainer } from "./DropzoneContainer";
import { SliderConfig, SlidersContainer } from "./SlidersContainer.tsx";

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
  const [isError, setIsError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const slidersConfig: SliderConfig[] = [
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

  const pyTorchResultsFromImageBlob = async (imageBlob: Blob) => {
    try {
      // showWarningToast();
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
      <div className="flex-1 flex-col bg-[linear-gradient(#1c2a3f_0%,#223146_5%,#223146_95%,#1c2a3f_100%)] md:p-12 pb-12">
        <div className="flex gap-4 w-full flex-col md:flex-row md:mt-0 mt-6">
          <ImageClassificationPageDescription />
          <DropzoneContainer
            fetchPyTorchAnalysisUsingUploadedImage={
              fetchPyTorchAnalysisUsingUploadedImage
            }
            fetchPyTorchAnalysisUsingImageURL={
              fetchPyTorchAnalysisUsingImageURL
            }
            loading={loading}
            inputValue={inputValue}
            setInputValue={setInputValue}
            uploadedImages={uploadedImages}
            setUploadedImages={setUploadedImages}
            setColorMapCounter={setColorMapCounter}
          />
        </div>

        <SlidersContainer {...{ slidersConfig }} />

        {/* JSONBox and ImageCanvas */}
        <div className="flex flex-col md:flex-row gap-8 mt-4 h-[50rem]">
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

const ImageClassificationPageDescription = () => {
  return (
    <div className="text-sm text-gray-200 text-left bg-black bg-opacity-60 p-6 md:p-12 md:rounded-xl w-full md:w-[60%] ">
      <h1 className="font-bold mb-4 md:mb-4 text-orange-600">
        App Description
      </h1>
      <div className="ml-2 md:ml-8">
        <li className="mb-4 md:mb-6">
          Use buttons below to send a request to a pre-trained PyTorch{" "}
          <strong className="text-red-700">fasterrcnn_resnet50_fpn_v2</strong>{" "}
          computer vision model called by a custom{" "}
          <strong className="text-red-700">inference.py</strong> script.
        </li>
      </div>
      <h1 className="font-bold mb-4 md:mb-4 mt-14 md:mt-14 text-orange-600">
        Model Description
      </h1>
      <div className="ml-2 md:ml-8">
        <li className="mb-4 md:mb-6">
          Faster R-CNN is an acronym for a Region-based CNN (Convolutional
          Neural Network). It utilizes a ResNet-50 (50 layer Residual Network)
          as the CNN backbone. The backbone incorporates a FPN (Feature Pyramid
          Network) for feature extraction from each image. A RPN (Region
          Proposal Network) slides a small CNN over the feature map to generate
          region proposals, which represent potential objects of interest.
        </li>
      </div>
      <div className="w-full flex justify-center">
        <img
          className="my-8 flex w-[50rem] rounded-lg shadow-2xl"
          alt="faster-r-cnn-pipeline"
          src="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703965451/faster_rcnn_o7riso.png"
        ></img>
      </div>
      <div className="ml-2 md:ml-8">
        <li className="mb-4 md:mb-6">
          Region of Interest (ROI) pooling is then applied to these regions to
          generate fixed-size feature maps. These feature maps are passed to two
          separate branches in the network, the box head, responsible for
          generate bounding box coordinates, and a class head, used to predict
          class labels of objects. After this process, class labels/scores and
          bounding boxes for detected objects are returned from the model.
        </li>
      </div>
      <h1 className="font-bold mb-4 md:mb-4 mt-14 md:mt-14 text-orange-600">
        Model Deployment
      </h1>
      <div className="ml-2 md:ml-8">
        <li className="mb-4 md:mb-4">
          The model and <strong className="text-red-700">inference.py</strong>{" "}
          script is provisioned on a Flask microservice running in an EC2. A
          Java Spring Boot API takes requests from the front end and sends an
          image as multipart form-data to the model. The Flask endpoint converts
          this data into a NumPy array, and normalizes its pixel values for
          input into the PyTorch model. Inference results from the model are
          then returned as JSON to the front end to be plotted on the image.
        </li>
      </div>
    </div>
  );
};
