import express from "express";
import axios from "axios";
import multer from "multer";

import { Request } from "express";

const router = express.Router();

const storage = multer.memoryStorage();
const fileFilter = (
  req: Request,
  file: Express.Multer.File,
  cb: multer.FileFilterCallback
) => {
  // Check file type or other conditions if needed
  cb(null, true);
};

const upload = multer({ storage, fileFilter });

const fetchImageAnalysisUsingBuffer = async (imageBuffer: any) => {
  const apiKey = process.env.API_KEY_AWS;
  const apiPytorchImageURL = process.env.AWS_GATEWAY_API_URL;

  try {
    const response = await axios.post(apiPytorchImageURL ?? "", imageBuffer, {
      headers: {
        "Content-Type": "image/jpg",
      },
    });

    console.log("Response:", response?.data);
    return response?.data;
  } catch (error: any) {
    console.error("Error:", error);
    if (error?.response) {
      console.error("Response Data:", error.response.data);
    }
  }
};

router.post("/image-url-pytorch", upload.single("image"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        error: "Bad Request - Missing formData or file in the request.",
      });
    }

    const imageBuffer = req.file.buffer;
    console.log(req.file.buffer);
    const response = await fetchImageAnalysisUsingBuffer(imageBuffer);

    return res.json(response);
  } catch (err) {
    return res
      .status(400)
      .json({ error: "Bad Request - Missing or invalid data." });
  }
});

export default router;
