import { ColorRing } from "react-loader-spinner";

interface ButtonProps {
    buttonOnClick: () => Promise<void>;
    loading: boolean;
    buttonText: string;
  }


const Button = ({buttonOnClick, loading, buttonText}: ButtonProps) => {

    return (
      <>
        <div className="flex justify-center gap-14">
          <button
            onClick={() => buttonOnClick()}
            className="bg-red-800 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-sm w-60 active:scale-95 transition-transform duration-300 ease-linear"
            disabled={loading}
          >
            <div className="flex">
              <div className="w-11/12">
              {buttonText}
              </div>
              <div className="w-1/12">
              {loading && (
                <ColorRing
                  height="20"
                  width="20"
                  colors={[
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                    "#ffffff",
                  ]}
                />
              )}
              </div>
            </div>
          </button>
        </div>
      </>
    );
  };

  export default Button;
