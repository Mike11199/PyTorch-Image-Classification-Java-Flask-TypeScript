import "./App.css";

function App() {
  return (
    <>
      <div className="h-screen bg-slate-600 pt-8">
        <button
          onClick={() => alert("send request wip")}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Submit Image URL
        </button>
        <input className="ml-8 border-2 border-black"></input>
      </div>
    </>
  );
}

export default App;
