import Button from "./Button";
import DropZone from "./Dropzone";
import ImageURL from "./ImageURL";

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
  return (
    <div className="flex flex-col bg-black bg-opacity-60 p-6 md:p-12 rounded-xl justify-between w-full md:w-[40%] gap-12 md:gap-0">
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
          buttonOnClick={() => fetchPyTorchAnalysisUsingImageURL(inputValue)}
          loading={loading}
          buttonText="Submit Image URL"
        />
        <Button
          color="bg-[#0c2c46]"
          hoverColor="hover:bg-[#114d7e]"
          buttonOnClick={fetchPyTorchAnalysisUsingUploadedImage}
          loading={loading}
          buttonText="Submit Image File"
        />
        <Button
          color="bg-[#0c2c46]"
          hoverColor="hover:bg-[#114d7e]"
          buttonOnClick={() => setColorMapCounter((prev) => prev + 1)}
          buttonText="Regenerate Colors"
        />
      </div>
    </div>
  );
};
