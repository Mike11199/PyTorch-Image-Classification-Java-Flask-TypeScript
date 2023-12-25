import express from "express";

const router = express.Router();

router.post("/image-url-pytorch", (req, res) => {
  try {
    return res.json({ message: 'hello from the server 😎' });
  } catch (err) {
    return res
      .status(400)
      .json({ error: "Bad Request - Missing or invalid data." });
  }
});

export default router;
