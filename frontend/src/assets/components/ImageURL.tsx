interface ImageURLProps {
  urlInputValue: string;
  setterURLInputValue: React.Dispatch<React.SetStateAction<string>>;
}

const ImageURL = ({ urlInputValue, setterURLInputValue }: ImageURLProps) => {
  return (
    <>
      <div className="flex flex-col justify-center items-center text-center gap-6">
        <select
          onChange={(e) => setterURLInputValue(e.target.value)}
          className="w-full text-center bg-slate-800 text-gray-200 outline-2 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
          id="image_url_options"
          name="image_url_options"
        >
          <option value="https://assets.machine-learning-projects.com/images/labrador.jpg">
            Labrador
          </option>
          <option value="https://assets.machine-learning-projects.com/images/winter-road.jpg">
            Winter Road
          </option>
          <option value="https://assets.machine-learning-projects.com/images/elephant.jpg">
            Elephant
          </option>
          <option value="https://assets.machine-learning-projects.com/images/new-york-crosswalk.jpg">
            New York Traffic
          </option>
          <option value="https://assets.machine-learning-projects.com/images/cats-and-dogs.webp">
            Cats and Dogs
          </option>
          <option value="https://assets.machine-learning-projects.com/images/city-crosswalk.jpg">
            City Crosswalk
          </option>
          <option value="https://assets.machine-learning-projects.com/images/nat-geo-collage.png">
            Nat Geo Collage
          </option>
          <option value="https://assets.machine-learning-projects.com/images/cat.jpg">
            Cat Image
          </option>
        </select>
        <input
          className="w-full bg-slate-800 text-gray-200 outline-2 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
          type="text"
          id="inputField"
          value={urlInputValue}
          onChange={(e) => setterURLInputValue(e.target.value)}
        />
      </div>
    </>
  );
};

export default ImageURL;
