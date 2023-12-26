import axios from "axios";
import { useState } from "react";

const HomePage = () => {
  const [inputValue, setInputValue] = useState("");
  const sampleImageUrl =
    "https://images.freeimages.com/images/large-previews/bd1/cat-1404368.jpg";

  const fetchPyTorchAnalysisUsingImageURL = async (imageUrl: string) => {
    try {
      const response = await axios.post("/api/image-url-pytorch", {
        imageUrl: imageUrl,
      });
      // const data = response?.data
      const jsonString = JSON.stringify(response?.data, null, 2); // the third argument (2) adds indentation for better readability
      console.log("Response:", jsonString);
      alert(jsonString);
    } catch (error: any) {
      console.error("Error:", error.message);
    }
  };

  return (
    <>
      <div className="h-screen bg-slate-600 pt-8">
        <button
          onClick={() => fetchPyTorchAnalysisUsingImageURL(sampleImageUrl)}
          className="bg-red-800 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
        >
          Use Sample Image URL
        </button>
        <button
          onClick={() => fetchPyTorchAnalysisUsingImageURL(inputValue)}
          className="bg-blue-800 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded ml-8 mr-8"
        >
          Submit Image URL
        </button>
        <input
          type="text"
          id="inputField"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />
      </div>
    </>
  );
};

export default HomePage;
