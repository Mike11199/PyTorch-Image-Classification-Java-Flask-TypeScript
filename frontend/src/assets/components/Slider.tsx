import * as React from "react";
import { styled } from "@mui/material/styles";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import Slider from "@mui/material/Slider";
import MuiInput from "@mui/material/Input";

const Input = styled(MuiInput)`
  width: 42px;
  color: white !important; // Text color with !important
  &::before,
  &::after {
    // Underline color
    border-bottom: 0px solid white !important;
  }

  &:hover {
    color: white !important; // Text color on hover
    &::before,
    &::after {
      border-bottom: 0px solid white !important; // Underline color on hover
    }
  }
`;

interface PyTorchSliderProps {
  sliderName: string;
  setterValue: number;
  setterFunction: React.Dispatch<React.SetStateAction<number>>;
}

const PyTorchSlider = ({ sliderName, setterValue, setterFunction  }: PyTorchSliderProps) => {


  const handleSliderChange = (event: Event, newValue: number | number[]) => {
    setterFunction(newValue as number);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setterFunction(event.target.value === "" ? 0 : Number(event.target.value));
  };

  const handleBlur = () => {
    if (setterValue < 0) {
      setterFunction(0);
    } else if (setterValue > 100) {
      setterFunction(100);
    }
  };

  return (
    <Box sx={{ width: 250 }}>
      <Typography
        id="input-slider"
        gutterBottom
        style={{ color: "white", borderBottomColor: "white" }}
      >
        {sliderName}
      </Typography>
      <Grid
        container
        spacing={2}
        alignItems="center"
        style={{ color: "white", borderBottomColor: "white" }}
      >
        <Grid item></Grid>
        <Grid item xs>
          <Slider
            color="secondary"
            value={typeof setterValue === "number" ? setterValue : 0}
            onChange={handleSliderChange}
            aria-labelledby="input-slider"
          />
        </Grid>
        <Grid item style={{ color: "white", borderBottomColor: "white" }}>
          <Input
            style={{ color: "white", borderBottomColor: "white" }}
            value={setterValue}
            size="small"
            onChange={handleInputChange}
            onBlur={handleBlur}
            inputProps={{
              step: 1,
              min: -20,
              max: 20,
              type: "number",
              "aria-labelledby": "input-slider",
            }}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default PyTorchSlider;
