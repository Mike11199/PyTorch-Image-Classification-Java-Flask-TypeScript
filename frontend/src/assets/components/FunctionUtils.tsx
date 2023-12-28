import { PyTorchImageResponseType } from "./types";

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
