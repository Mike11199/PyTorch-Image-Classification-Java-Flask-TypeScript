import * as React from "react";
import { styled } from "@mui/material/styles";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
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
    color: "#ba0000",
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
    <Box sx={{ width: 200 }}>
      <div className="flex gap-5 justify-between">
        <Typography
          id="input-slider"
          style={{
            color: "#dfdede",
            textAlign: "right",
          }}
        >
          {sliderName}
        </Typography>
        <Input
          style={{
            color: "#dfdede",
            width: "55px",
          }}
          value={setterValue}
          size="small"
          onChange={handleInputChange}
          onBlur={handleBlur}
          inputProps={{
            style: { textAlign: "right" },
            step: 1,
            min: minValue,
            max: maxValue,
            type: "number",
            "aria-labelledby": "input-slider",
          }}
        />
      </div>
      <Grid
        container
        spacing={2}
        alignItems="center"
        style={{ color: "white", borderBottomColor: "white" }}
      >
        <Grid item xs>
          <CustomSlider
            color="secondary"
            value={setterValue}
            onChange={handleSliderChange}
            aria-labelledby="input-slider"
            min={minValue}
            max={maxValue}
          />
        </Grid>
        <Grid
          item
          style={{ color: "white", borderBottomColor: "white" }}
        ></Grid>
      </Grid>
    </Box>
  );
};

export default PyTorchSlider;
