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
import { fetchPyTorchAnalysisMask } from "./FunctionUtils";
import PyTorchSlider from "./PyTorchSlider";

const MaskRCNNPage = () => {
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
  const [pyTorchBoxLineWidth, setPyTorchBoxLineWidth] = useState<number>(3);
  const [pyTorchBoxFontSize, setPyTorchBoxFontSize] = useState<number>(12);
  const [pyTorchBoxXOffset, setPyTorchBoxXOffset] = useState<number>(5);
  const [pyTorchBoxYOffset, setPyTorchBoxYOffset] = useState<number>(15);
  const [pyTorchOpacity, setPyTorchOpacity] = useState<number>(100);
  const [colorMapCounter, setColorMapCounter] = useState(0);
  const [pyTorchMasksArray, setPyTorchMasksArray] = useState<number[][][]>([]);

  useEffect(() => {
    console.log(pyTorchMasksArray);
    console.log(
      `Total number of 1's in masks_array: ${
        pyTorchMasksArray.flat(2).filter((x) => x === 1).length
      }`
    );
    console.log(
      `Total number of 0's in masks_array: ${
        pyTorchMasksArray.flat(2).filter((x) => x === 0).length
      }`
    );
  }, [pyTorchMasksArray]);


  const pyTorchResultsFromImageBlob = async (imageBlob: Blob) => {
    setLoading(true);

    try {
      const parsedPyTorchData = await fetchPyTorchAnalysisMask(imageBlob);

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
    } catch (error) {
      console.error("Error fetching PyTorch analysis:", error);
      setPyTorchResponseObj(null);
      setPyTorchResponseString("");
      setPyTorchMasksArray([]);
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
              className="my-8 flex w-[70rem] rounded-lg shadow-2xl"
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

        <div className="mt-8 mb-16">
          <Button
            color={"bg-red-700"}
            hoverColor={"hover:bg-red-600"}
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
          color={"bg-red-700"}
          hoverColor={"hover:bg-red-600"}
          buttonOnClick={() => fetchPyTorchAnalysisUsingImageURL(inputValue)}
          loading={loading}
          buttonText={"Submit Image URL"}
        />
        <div className="mt-32">
          <Button
            color={"bg-purple-900"}
            hoverColor={"hover:bg-purple-800"}
            buttonOnClick={() =>
              setColorMapCounter((prevCounter) => prevCounter + 1)
            }
            loading={loading}
            buttonText={"Regenerate Colors"}
          />
        </div>
        <div className="mt-4 flex flex-col justify-center md:flex-row md:mx-44">
          <div className=" md:w-2/12 flex justify-center text-white">
            <PyTorchSlider
              minValue={0}
              maxValue={100}
              setterValue={pyTorchOpacity}
              setterFunction={setPyTorchOpacity}
              sliderName={"Opacity"}
            />
          </div>
          <div className=" md:w-2/12 flex justify-center text-white">
            <PyTorchSlider
              minValue={1}
              maxValue={20}
              setterValue={pyTorchBoxLineWidth}
              setterFunction={setPyTorchBoxLineWidth}
              sliderName={"Box Line Width"}
            />
          </div>
          <div className="md:w-2/12 flex justify-center text-white">
            <PyTorchSlider
              minValue={1}
              maxValue={65}
              setterValue={pyTorchBoxFontSize}
              setterFunction={setPyTorchBoxFontSize}
              sliderName={"Label Font Size"}
            />
          </div>
          <div className=" md:w-3/12 flex justify-center text-white">
            <PyTorchSlider
              minValue={-200}
              maxValue={200}
              setterValue={pyTorchBoxXOffset}
              setterFunction={setPyTorchBoxXOffset}
              sliderName={"Label X Offset"}
            />
          </div>
          <div className=" md:w-3/12 flex justify-center text-white">
            <PyTorchSlider
              minValue={-200}
              maxValue={200}
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
              colorMapCounter={colorMapCounter}
              pyTorchOpacity={pyTorchOpacity}
              pyTorchMasksArray={pyTorchMasksArray}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default MaskRCNNPage;
