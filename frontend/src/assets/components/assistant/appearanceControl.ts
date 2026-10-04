export interface MaskOpacityControl {
  value: number;
  set: (value: number) => void;
  defaultValue: number;
}

export function applyMaskOpacity(control: MaskOpacityControl | undefined, value?: number) {
  if (value !== undefined) control?.set(value);
}

export function resetMaskOpacity(control?: MaskOpacityControl) {
  if (control) control.set(control.defaultValue);
}
