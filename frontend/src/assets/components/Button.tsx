import { ColorRing } from "react-loader-spinner";
import clsx from "clsx";

interface ButtonProps {
  buttonOnClick: () => Promise<void> | void;
  loading: boolean;
  buttonText: string;
  color: string;
  hoverColor: string;
}

const Button = ({
  buttonOnClick,
  loading,
  buttonText,
  color,
  hoverColor,
}: ButtonProps) => {
  const buttonStyle = clsx(
    `text-white`,
    `font-bold`,
    `py-2`,
    `px-4`,
    `rounded`,
    `text-sm`,
    `w-60`,
    `active:scale-95`,
    `transition-transform duration-300 ease-linear`,
    color,
    hoverColor
  );
  return (
    <>
      <div className="flex justify-center gap-14">
        <button
          onClick={() => buttonOnClick()}
          className={buttonStyle}
          disabled={loading}
        >
          <div className="flex">
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
