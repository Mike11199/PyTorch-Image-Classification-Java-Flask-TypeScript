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
          <option value="https://assets.machine-learning-projects.com/images/labrador_retriever_xi8k9z.6f53bb98b098d4d1.jpg">
            Labrador
          </option>
          <option value="https://assets.machine-learning-projects.com/images/winter_road_aiqpqk.bb00416e98289dce.jpg">
            Winter Road
          </option>
          <option value="https://assets.machine-learning-projects.com/images/Elephant_aoojxl.4958b1960c5f86c9.jpg">
            Elephant
          </option>
          <option value="https://assets.machine-learning-projects.com/images/new_york_crosswalk_hsyblv.214aadd6b868d6e1.jpg">
            New York Traffic
          </option>
          <option value="https://assets.machine-learning-projects.com/images/cats_and_dogs_original_bjnbbj.deea681becc7f815.webp">
            Cats and Dogs
          </option>
          <option value="https://assets.machine-learning-projects.com/images/city_crosswalk_k83x4d.e6c00bd941dae8be.jpg">
            City Crosswalk
          </option>
          <option value="https://assets.machine-learning-projects.com/images/nat_geo_collage_aufbyo.a473cd24dbb6a8a6.png">
            Nat Geo Collage
          </option>
          <option value="https://assets.machine-learning-projects.com/images/20171225_184853_srzt72.2054284e1e217df6.jpg">
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
