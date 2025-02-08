import { PyTorchImageResponseType } from "./types";
import axios from "axios";
import toast from "react-hot-toast";
import { useState } from "react";

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
      masks_array: pyTorchData?.masks_array,
    };

    return modifiedBoundingBoxData;
  } catch (error) {
    return null;
  }
}

export const fetchPyTorchAnalysis = async (imageBlob: Blob, apiUrl: string) => {
  const formData = new FormData();
  formData.append("image", imageBlob, "image.jpg");
  const response = await axios.post(apiUrl, formData);
  const parsedPyTorchData = trimPytorchDataObject(response?.data) ?? null;
  return parsedPyTorchData;
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
    // if (className == "dog") {
    //   classColorMap[className] = `rgb(161, 8, 8)`;
    // }
    // if (className == "cat") {
    //   classColorMap[className] = `rgb(100, 3, 100)`;
    // }
    if (className && !classColorMap[className]) {
      classColorMap[className] = getRandomColor();
    }
  }
  return classColorMap;
}

function CloseButton() {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => toast.dismiss()}
      style={{
        marginLeft: "auto",
        backgroundColor: hovered ? "#a11e1e" : "#bb2323",
        color: "#c0bcbc",
        borderRadius: "2px",
        padding: "2px 6px",
        cursor: "pointer",
        fontWeight: "bold",
        boxShadow: "1px 1px 5px 0px #000000",
      }}
    >
      ✕
    </button>
  );
}
export const showWarningToast = () => {
  toast.dismiss();
  toast(
    <div style={{ display: "flex", alignItems: "center" }}>
      <span style={{ marginRight: 8 }}>⚠️</span>
      <span style={{ flex: 1, textAlign: "center" }}>
        Please wait. This can take 10-30 seconds.
      </span>
      <CloseButton />
    </div>,
    {
      style: {
        padding: "16px",
        backgroundColor: "#2c2c2c",
        color: "#fff",
        borderRadius: "8px",
      },
      duration: 1500,
    }
  );
};

export const showErrorToast = (msg: string) => {
  toast.dismiss();
  toast(
    <div
      style={{
        display: "flex",
        alignItems: "center",
        fontSize: "1rem",
        gap: "1rem",
      }}
    >
      <span style={{ marginRight: 8 }}>⚠️</span>
      <span style={{ flex: 1, textAlign: "center" }}>{msg}</span>
      <CloseButton />
    </div>,
    {
      style: {
        background: "linear-gradient( #131212, #131212)",
        color: "#f0f0f0",
        borderRadius: "8px",
        boxShadow: "5px 5px 15px 0px #000000",
      },
      duration: 1500,
    }
  );
};
