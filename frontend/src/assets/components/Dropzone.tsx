import { useDropzone } from "react-dropzone";
import { useCallback, useMemo } from "react";
import { FileRejection } from "react-dropzone";

interface DropZoneProps {
  uploadedImages: Blob[];
  setterUploadedImages: React.Dispatch<React.SetStateAction<Blob[]>>;
  loading: boolean;
}

const DropZone = ({
  setterUploadedImages,
  uploadedImages,
  loading,
}: DropZoneProps) => {
  const onDrop = useCallback(
    async (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      for (const file of acceptedFiles) {
        const blob = await fileToBlob(file);
        setterUploadedImages([blob]);
        console.log(file);
        console.log(blob);
      }
    },
    []
  );

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
  } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "image/*": [".jpg", ".jpeg", ".png"],
    },
  });

  const style = useMemo(
    () => ({
      ...(isDragAccept ? { borderColor: "#00e676" } : {}),
      ...(isDragReject ? { borderColor: "#ff1744" } : {}),
    }),
    [isDragAccept, isDragReject]
  );

  const fileToBlob = (file: File): Promise<Blob> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => {
        const blob = new Blob([reader.result as ArrayBuffer], {
          type: file.type,
        });
        resolve(blob);
      };
      reader.readAsArrayBuffer(file);
    });
  };

  return (
    <div className="h-[70%]">
      <div
        className="flex flex-col gap-12 items-center justify-center border-2  border-dashed rounded-lg
        cursor-pointer dark:hover:bg-bray-800 dark:bg-gray-800 hover:bg-gray-700  border-gray-600
        hover:border-gray-500 h-full"
        {...getRootProps({ style })}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p className="text-gray-200 mt-12 text-center">Drop file(s) here ...</p>
        ) : loading ? (
          <p className="text-gray-200 mt-12 text-center">Processing image...</p>
        ) : (
          <p className="text-gray-200 mt-12 text-center">
            Drag and drop file(s) here, or click to select files
          </p>
        )}
        {uploadedImages.length == 0 && (
          <svg
            className="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400"
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 16"
          >
            <path
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
            />
          </svg>
        )}
        <div className="mb-12">
          {uploadedImages.length > 0 &&
            uploadedImages.map((image: Blob, index: number) => (
              <img
                className="h-44 rounded-md shadow-md"
                src={`${URL.createObjectURL(image)}`}
                key={index}
                alt=""
              />
            ))}
        </div>
      </div>
    </div>
  );
};

export default DropZone;
