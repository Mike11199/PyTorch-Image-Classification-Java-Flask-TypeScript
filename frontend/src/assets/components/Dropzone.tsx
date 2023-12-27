import { useDropzone } from "react-dropzone";
import { useCallback, useState, useMemo } from "react";

const DropZone = ({ buttonFunction }: any) => {
  const [selectedImages, setSelectedImages] = useState<any>([]);
  //const [uploadStatus, setUploadStatus] = useState<any>("");
  const onDrop = useCallback((acceptedFiles: any, rejectedFiles: any) => {
    acceptedFiles.forEach((file: any) => {
      setSelectedImages([file]);
    });
  }, []);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
  } = useDropzone({ onDrop });

  const handleImageUpload = async () => {
    //setUploadStatus("Uploading....");

    const formData = new FormData();
    const blobs = selectedImages.map((file: any) => {
      return new Blob([file], { type: file.type });
    });

    console.log(blobs)
    console.log(blobs);
    blobs.forEach((image: any) => {
      console.log(`Type of image at index :`,  image);

      formData.append('image', image, 'image.jpg');
    });



    buttonFunction(blobs[0])

    try {
      //   const response = await axios.post(
      //     "https://cloudinary-react-dropzone.vercel.app/api/upload",
      //     formData
      //   );
      //   console.log(response.data);
      
      //setUploadStatus("upload successful");
    } catch (error) {
      console.log("" + error);
      //      setUploadStatus("Upload failed..");
    }
  };

  const style = useMemo(
    () => ({
      ...(isDragAccept ? { borderColor: "#00e676" } : {}),
      ...(isDragReject ? { borderColor: "#ff1744" } : {}),
    }),
    [isDragAccept, isDragReject]
  );

  return (
    <div className="mx-44">
      <div
        className="flex flex-col gap-12 items-center justify-center w-full min-h-60  border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-bray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-600"
        {...getRootProps({ style })}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p className="text-white mt-12">Drop file(s) here ...</p>
        ) : (
          <p className="text-white mt-12">
            Drag and drop file(s) here, or click to select files
          </p>
        )}
        {selectedImages.length == 0 && (
          <svg
            className="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400"
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 16"
          >
            <path
              stroke="currentColor"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
            />
          </svg>
        )}
        <div className="mb-12">
          {selectedImages.length > 0 &&
            selectedImages.map((image: any, index: any) => (
              <img
                className="h-44 rounded-md shadow-md"
                src={`${URL.createObjectURL(image)}`}
                key={index}
                alt=""
              />
            ))}
        </div>
      </div>

      <div className="mt-8 mb-16">
        <button
          className="bg-red-800 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-sm"
          onClick={handleImageUpload}
        >
          Submit Uploaded Image File
        </button>
        {/* <p className="text-white">{uploadStatus}</p> */}
      </div>
    </div>
  );
};

export default DropZone;
