import express from "express";
import path from "path";
import cors from "cors";
import apiRoutes from './apiRoutes.mjs';

const app = express();
app.use(cors());

if (process.env.NODE_ENV === "production") {
  app.use(
    express.static(
      path.join(new URL("./frontend/dist", import.meta.url).pathname)
    )
  );
  app.get("*", (req, res) =>
    res.sendFile(
      path.resolve(
        new URL("./frontend/dist/index.html", import.meta.url).pathname
      )
    )
  );
} else {
  app.get("/", (req, res) => {
    res.json({ message: "API running..." });
  });
}

app.use(express.json());

app.use("/api", apiRoutes);

const PORT = process.env.PORT || 5001;

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
