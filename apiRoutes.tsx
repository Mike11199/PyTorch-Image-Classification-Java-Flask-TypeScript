import express from "express";
import axios from "axios";

const router = express.Router();

const fetchData = async () => {
  try {
    const response = await axios.post("/api/image-url-pytorch", {});
    console.log("Response:", response?.data?.message);
    alert(response?.data?.message);
  } catch (error: any) {
    console.error("Error:", error.message);
  }
};

router.post("/image-url-pytorch", (req, res) => {
  try {
    const apiKey = process.env.API_KEY_AWS;
    const sampleImageUrl =
      "https://images.freeimages.com/images/large-previews/bd1/cat-1404368.jpg";

    if (apiKey) {
      console.log(`API Key: ${apiKey}`);
    } else {
      console.error("API Key not set.");
    }

    return res.json({ message: "hello from the server 😎" });
  } catch (err) {
    return res
      .status(400)
      .json({ error: "Bad Request - Missing or invalid data." });
  }
});

export default router;
