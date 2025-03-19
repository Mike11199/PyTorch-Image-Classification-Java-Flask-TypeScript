import Button from "./Button";
import DropZone from "./Dropzone";
import ImageURL from "./ImageURL";
import ReactGA from "react-ga4";
import { useLocation } from "react-router-dom";

interface DropzoneContainerProps {
  fetchPyTorchAnalysisUsingUploadedImage: () => Promise<void>;
  fetchPyTorchAnalysisUsingImageURL: (url: string) => Promise<void>;
  loading: boolean;
  inputValue: string;
  setInputValue: React.Dispatch<React.SetStateAction<string>>;
  uploadedImages: Blob[];
  setUploadedImages: React.Dispatch<React.SetStateAction<Blob[]>>;
  setColorMapCounter: React.Dispatch<React.SetStateAction<number>>;
}

export const DropzoneContainer: React.FC<DropzoneContainerProps> = ({
  fetchPyTorchAnalysisUsingUploadedImage,
  fetchPyTorchAnalysisUsingImageURL,
  loading,
  inputValue,
  setInputValue,
  uploadedImages,
  setUploadedImages,
  setColorMapCounter,
}) => {
  const location = useLocation();
  const currentPage = location.pathname;

  return (
    <div className="flex flex-col bg-black bg-opacity-60 p-6 md:p-12 md:rounded-xl justify-between w-full md:w-[40%] gap-12 md:gap-0 shadow-md shadow-black">
      <DropZone
        setterUploadedImages={setUploadedImages}
        uploadedImages={uploadedImages}
        loading={loading}
      />
      <ImageURL
        urlInputValue={inputValue}
        setterURLInputValue={setInputValue}
      />
      {/* Buttons */}
      <div className="flex gap-4 justify-between w-full flex-col md:flex-row">
        <Button
          color="bg-[#0c2c46]"
          hoverColor="hover:bg-[#114d7e]"
          buttonOnClick={() => {
            ReactGA.event({
              category: "Image Analysis",
              action: "Submit Image URL Button Clicked",
              label: `Submit Image URL 🌐 - ${currentPage}`,
            });
            fetchPyTorchAnalysisUsingImageURL(inputValue);
          }}
          loading={loading}
          buttonText="Submit Image URL 🌐"
        />
        <Button
          color="bg-[#0c2c46]"
          hoverColor="hover:bg-[#114d7e]"
          buttonOnClick={() => {
            ReactGA.event({
              category: "Image Analysis",
              action: "Submit Image File Button Clicked",
              label: `Submit Image File 📷 - ${currentPage}`,
            });
            fetchPyTorchAnalysisUsingUploadedImage();
          }}
          loading={loading}
          buttonText="Submit Image File 📷"
        />
        <Button
          color="bg-[#000000]"
          hoverColor="hover:bg-[#111111]"
          buttonOnClick={() => setColorMapCounter((prev) => prev + 1)}
          buttonText="Regenerate Colors 🎨"
          loading={loading}
        />
      </div>
    </div>
  );
};
