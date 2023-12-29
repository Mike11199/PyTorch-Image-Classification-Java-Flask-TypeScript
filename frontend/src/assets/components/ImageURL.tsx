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
          <option value="https://images.saymedia-content.com/.image/t_share/MjAxMjg4MjkxNjI5MTQ3Njc1/labrador-retriever-guide.jpg">
            Labrador
          </option>
          <option value="https://res.cloudinary.com/dwgvi9vwb/image/upload/v1703831056/winter_road_aiqpqk.jpg">
            Winter Road
          </option>
          <option value="https://upload.wikimedia.org/wikipedia/commons/b/bc/Elephant.jpg">
            Elephant
          </option>
          <option value="https://i.guim.co.uk/img/media/00cbd8cdb8ef7ff8e89fcd835f1cd0fa6adce5f6/8_0_2544_1527/master/2544.jpg?width=1200&quality=85&auto=format&fit=max&s=24e5c33c75542aba0cce59b3fe05b79a">
            Cats and Dogs
          </option>
          <option value="https://images.unsplash.com/photo-1602940659805-770d1b3b9911?q=80&w=1932&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D">
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
