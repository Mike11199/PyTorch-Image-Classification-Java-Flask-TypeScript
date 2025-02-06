import * as React from "react";
import { styled } from "@mui/material/styles";
import Slider from "@mui/material/Slider";
import MuiInput from "@mui/material/Input";

const Input = styled(MuiInput)`
  width: 42px;
  color: #dfdede !important;
  &::before,
  &::after {
    border-bottom: 0px solid white !important;
  }

  &:hover {
    color: #dfdede !important;
    &::before,
    &::after {
      border-bottom: 0px solid white !important;
    }
  }
`;

const CustomSlider = styled(Slider)({
  "& .MuiSlider-track": {
    color: "#750a0a",
  },

  "& .MuiSlider-thumb": {
    color: "#000000",

    "&:hover, &:focus, &:active": {
      boxShadow: "0 0 15px 10px rgba(255, 0, 0, 0.2) !important",
    },
  },

  "& .MuiSlider-rail": {
    color: "#304970",
  },
});

interface PyTorchSliderProps {
  minValue: number;
  maxValue: number;
  sliderName: string;
  setterValue: number;
  setterFunction: React.Dispatch<React.SetStateAction<number>>;
}

const PyTorchSlider = ({
  sliderName,
  setterValue,
  setterFunction,
  minValue,
  maxValue,
}: PyTorchSliderProps) => {
  const handleSliderChange = (event: Event, newValue: number | number[]) => {
    setterFunction(newValue as number);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue =
      event.target.value === "" ? 0 : Number(event.target.value);
    setterFunction(inputValue);
  };

  const handleBlur = () => {
    if (setterValue < minValue) {
      setterFunction(minValue);
    } else if (setterValue > maxValue) {
      setterFunction(maxValue);
    }
  };

  return (
    <div className="flex-col w-full">
      <div className="flex justify-between ">
        <span className="">{sliderName}</span>
        <Input
          value={setterValue}
          size="small"
          onChange={handleInputChange}
          onBlur={handleBlur}
          inputProps={{
            style: { textAlign: "center" },
            step: 1,
            min: minValue,
            max: maxValue,
            type: "number",
          }}
        />
      </div>
      <CustomSlider
        color="secondary"
        value={setterValue}
        onChange={handleSliderChange}
        aria-labelledby="input-slider"
        min={minValue}
        max={maxValue}
      />
    </div>
  );
};

export default PyTorchSlider;
