import JSONPretty from "react-json-pretty";
import "react-json-pretty/themes/monikai.css";
import { LineWave } from "react-loader-spinner";

interface JSONBoxProps {
  loading: boolean;
  pyTorchImageResponseString: string;
}

const JSONBox = ({ loading, pyTorchImageResponseString }: JSONBoxProps) => {
  return (
    <>
      <div
        className={`text-left pl-4 h-full ${!loading ? 'overflow-auto' : ''}`}
        style={{ backgroundColor: "#272822" }}
      >
      {loading && (
          <div className="w-full flex justify-center">
            <LineWave height="100" width="100" color="green" />
          </div>
        )}
        <JSONPretty
          className="w-full h-full"
          style={{ backgroundColor: "#272822" }}
          id="json-pretty"
          data={!loading && pyTorchImageResponseString}
        ></JSONPretty>
      </div>
    </>
  );
};

export default JSONBox;
