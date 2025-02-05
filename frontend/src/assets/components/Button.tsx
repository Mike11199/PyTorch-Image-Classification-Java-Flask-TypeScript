import { ColorRing } from "react-loader-spinner";
import clsx from "clsx";

interface ButtonProps {
  buttonOnClick: () => Promise<void> | void;
  loading?: boolean;
  buttonText: string;
  color: string;
  hoverColor: string;
}

const Button = ({
  buttonOnClick,
  loading=false,
  buttonText,
  color,
  hoverColor,
}: ButtonProps) => {
  const buttonStyle = clsx(
    `text-gray-200`,
    `font-semibold`,
    `py-2`,
    `w-full`,
    ` shadow-black shadow-md`,
    `px-2`,
    `text-sm`,
    `active:scale-95`,
    `transition-transform duration-300 ease-linear`,
    color,
    hoverColor
  );
  return (
    <>
      <div className="flex justify-center gap-14 w-full">
        <button
          onClick={() => buttonOnClick()}
          className={buttonStyle}
          disabled={loading}
        >
          <div className="flex ">
            <div className=" w-11/12">{buttonText}</div>
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
