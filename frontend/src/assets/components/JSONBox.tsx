import JSONPretty from "react-json-pretty";
import "react-json-pretty/themes/monikai.css";

interface JSONBoxProps {
  loading: boolean;
  pyTorchImageResponseString: string;
}

const JSONBox = ({ loading, pyTorchImageResponseString }: JSONBoxProps) => {
  return (
    <>
      <div
        className="overflow-auto text-left pl-4 h-full"
        style={{ backgroundColor: "#272822" }}
      >
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
