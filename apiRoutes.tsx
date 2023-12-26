import express from "express";
import axios from "axios";

const router = express.Router();

const fetchImageAnalysisUsingURL = async (imageUrl: string) => {
  const apiKey = process.env.API_KEY_AWS;
  const apiPytorchImageURL = process.env.AWS_GATEWAY_API_URL;

  console.log("Function fetchImageAnalysisUsingURL is called. ")
  //console.log("API Key:", apiKey);
  //console.log("API Pytorch Image URL:", apiPytorchImageURL);

  try {
    const response = await axios.post(apiPytorchImageURL ?? "", {
      image_url: imageUrl
    });
    console.log("Response:", response?.data);
    return response?.data
  } catch (error: any) {
    console.error("Error:", error.message);
  }
};

router.post("/image-url-pytorch", async (req, res) => {
  try {
    const { imageUrl } = req.body;

    if (!imageUrl) {
      return res
        .status(400)
        .json({ error: "Bad Request - Missing image_url in the request body." });
    }

    const response = await fetchImageAnalysisUsingURL(imageUrl)


    return res.json(response);
  } catch (err) {
    return res
      .status(400)
      .json({ error: "Bad Request - Missing or invalid data." });
  }
});

export default router;
