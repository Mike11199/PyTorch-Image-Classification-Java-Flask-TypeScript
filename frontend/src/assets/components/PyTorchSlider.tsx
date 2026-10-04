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
  value: number;
  onChange: (value: number) => void;
  onChangeCommitted?: () => void;
  hideLabels?: boolean;
}

const PyTorchSlider = ({
  sliderName,
  value,
  onChange,
  onChangeCommitted,
  minValue,
  maxValue,
  hideLabels=false,
}: PyTorchSliderProps) => {
  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    onChange(newValue as number);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue =
      event.target.value === "" ? 0 : Number(event.target.value);
    onChange(inputValue);
  };

  const handleBlur = () => {
    if (value < minValue) {
      onChange(minValue);
    } else if (value > maxValue) {
      onChange(maxValue);
    }
    onChangeCommitted?.();
  };

  return (
    <div className="flex-col w-full">
      {!hideLabels &&
      <div className="flex justify-between ">
        <span className="">{sliderName}</span>
        <Input
          value={value}
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
      }
      <CustomSlider
        color="secondary"
        value={value}
        onChange={handleSliderChange}
        onChangeCommitted={onChangeCommitted}
        aria-label={sliderName}
        min={minValue}
        max={maxValue}
      />
    </div>
  );
};

export default PyTorchSlider;
