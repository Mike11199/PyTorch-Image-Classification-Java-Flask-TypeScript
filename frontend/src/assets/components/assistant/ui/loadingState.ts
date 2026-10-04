export function elapsedSeconds(startedAt: number, now = Date.now()) {
  return Math.max(0, Math.floor((now - startedAt) / 1000));
}

export function loadingDetails(seconds: number) {
  return {
    title: "Running local Qwen through LangGraph… (this can take up to 30 seconds)",
    detail: "Generating and validating viewer tool calls.",
    elapsed: seconds < 1 ? "" : `${seconds} second${seconds === 1 ? "" : "s"} elapsed`,
  };
}
