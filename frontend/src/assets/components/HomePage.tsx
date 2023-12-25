import axios from "axios";

const HomePage = () => {
  const fetchData = async () => {
    try {
      const response = await axios.post("/api/image-url-pytorch", {});
      console.log("Response:", response?.data?.message);
      alert(response?.data?.message);
    } catch (error: any) {
      console.error("Error:", error.message);
    }
  };

  return (
    <>
      <div className="h-screen bg-slate-600 pt-8">
        <button
          onClick={() => fetchData()}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Submit Image URL
        </button>
        <input className="ml-8 border-2 border-black"></input>
      </div>
    </>
  );
};

export default HomePage;
