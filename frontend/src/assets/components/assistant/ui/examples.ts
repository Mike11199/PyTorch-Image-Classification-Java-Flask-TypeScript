import type { AssistantPage } from "../types";

export function assistantExamples(page: AssistantPage | undefined, classes: string[]) {
  const category = classes.includes("car") ? "car" : classes[0];
  const standard = category ? [
    `Only show ${category}`,
    `Make ${category} purple`,
    ...(page === "boxes" ? [] : [
      `Make ${category} masks blue`,
      "Show masks only",
      "Show boxes only",
    ]),
    `How many ${category} detections are visible?`,
    page === "video" ? `Jump to the frame with the most ${category} detections`
      : `Highlight the leftmost ${category}`,
    "Hide detections below 80% confidence",
  ] : ["Hide detections below 80% confidence", "Show all categories"];

  const videoOrdered = page === "video" && category === "car" ? [
    "Make car purple and person red",
    ...standard.filter((example) => example !== "Only show car"),
    "Only show car",
  ] : standard;

  const ordered = page === "boxes" ? videoOrdered : [
    "Show masks only at full opacity",
    ...videoOrdered.filter((example) => example !== "Show masks only"),
  ];
  return page === "boxes" || page === "mask"
    ? ["Make cats red and dogs blue", ...ordered]
    : ordered;
}
