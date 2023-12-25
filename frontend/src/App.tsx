import './App.css'

function App() {
  return (
    <>
      <div>
      </div>
      <h1 className='border-2 font-semibold bg-slate-600 text-gray-50'>PyTorch Image Classification App</h1>
      <div className="card">
        <button onClick={() => alert('send request wip')} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Submit Image URL
        </button>

        <input className='ml-8 border-2 border-black'>
        </input>
      </div>
    </>
  )
}

export default App
