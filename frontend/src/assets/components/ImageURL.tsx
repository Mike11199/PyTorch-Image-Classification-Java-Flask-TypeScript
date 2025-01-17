interface ImageURLProps {
  urlInputValue: string;
  setterURLInputValue: React.Dispatch<React.SetStateAction<string>>;
}

const ImageURL = ({ urlInputValue, setterURLInputValue }: ImageURLProps) => {
  return (
    <>
      <div className="text-black mx-4 md:mx-44 mt-12 flex flex-col justify-center items-center text-center">
        <select
          onChange={(e) => setterURLInputValue(e.target.value)}
          className="mb-2 w-52 text-center mx-4 md:mx-44 bg-slate-500 outline-2 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500 tex"
          id="image_url_options"
          name="image_url_options"
        >
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1737100366/labrador_retriever_xi8k9z.jpg">
            Labrador
          </option>
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703831056/winter_road_aiqpqk.jpg">
            Winter Road
          </option>
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1737100677/Elephant_aoojxl.jpg">
            Elephant
          </option>
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703831905/new_york_crosswalk_hsyblv.jpg">
            New York Traffic
          </option>
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1737100598/cats_and_dogs_original_bjnbbj.webp">
            Cats and Dogs
          </option>
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1737100516/city_crosswalk_k83x4d.jpg">
            City Crosswalk
          </option>
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703823336/nat_geo_collage_aufbyo.png">
            Nat Geo Collage
          </option>
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703829029/20171225_184853_srzt72.jpg">
            Cat Image
          </option>
        </select>
      </div>

      <div className="flex justify-center gap-24 w-full mt-8">
        <input
          className="mb-8 w-full mx-4 md:mx-44 bg-slate-500 outline-2 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
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
