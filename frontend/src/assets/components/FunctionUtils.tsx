import { PyTorchImageResponseType } from "./types";
import axios from "axios";

export async function convertImageUrlToImage(
  imageUrl: string
): Promise<Blob | null> {
  try {
    const response = await fetch(imageUrl);
    if (
      response.ok &&
      response.headers.get("content-type")?.startsWith("image/")
    ) {
      const blob = await response.blob();
      return blob;
    } else {
      console.error("Invalid image URL or not an image file.");
      return null;
    }
  } catch (error) {
    console.error("Error fetching image:", error);
    return null;
  }
}

export function createImageURLFromBlob(
  imageBlob: Blob
): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const imageUrl = URL.createObjectURL(imageBlob);
    image.onload = () => {
      resolve(image);
    };
    image.onerror = (error) => {
      reject(error);
    };
    image.src = imageUrl;
  });
}

export function trimPytorchDataObject(pyTorchData: PyTorchImageResponseType) {
  try {
    if (!pyTorchData) return;
    const { scores, classes, boxes, labels } = pyTorchData;
    if (!scores || !classes || !boxes || !labels) return;

    const maxLength = boxes?.length;

    const modifiedBoundingBoxData = {
      scores: scores.slice(0, maxLength),
      classes: classes.slice(0, maxLength),
      boxes: boxes.slice(0, maxLength),
      labels: labels.slice(0, maxLength),
    };

    return modifiedBoundingBoxData;
  } catch (error) {
    return null;
  }
}

export const fetchPyTorchAnalysis = async (imageBlob: Blob) => {
  try {
    const formData = new FormData();
    formData.append("image", imageBlob, "image.jpg");
    const response = await axios.post("/api/image-url-pytorch", formData);
    const parsedPyTorchData = trimPytorchDataObject(response?.data) ?? null;
    return parsedPyTorchData;
  } catch (error: any) {
    console.error("Error:", error.message);
    if (error.response) {
      console.error("Response Data:", error.response.data);
    }
  } finally {
  }
};

export function createClassColorMap(
  boundingBoxData: PyTorchImageResponseType | null | undefined
) {
  const getRandomValue = () => Math.floor(Math.random() * 256);
  const getRandomColor = () =>
    `rgb(${getRandomValue()}, ${getRandomValue()}, ${getRandomValue()})`;

  if (!boundingBoxData) return null;
  const classColorMap: any = {};
  for (let i = 0; i < boundingBoxData.boxes.length; i++) {
    const className = boundingBoxData?.classes[i];
    if (className && !classColorMap[className]) {
      classColorMap[className] = getRandomColor();
    }
  }
  return classColorMap;
}
