export interface PyTorchImageResponseType {
  scores: number[];
  classes: string[];
  boxes: number[][];
  labels: number[];
  masks_array?: number[][][];
}

