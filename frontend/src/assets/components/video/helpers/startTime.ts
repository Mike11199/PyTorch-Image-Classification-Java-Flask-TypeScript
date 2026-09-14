const INVALID_TIME = "Use seconds, mm:ss, or hh:mm:ss for the start time.";

const parseSeconds = (text: string) => {
  if (!/^\d+(?:\.\d+)?$/.test(text)) throw new Error(INVALID_TIME);
  return Number(text);
};

const parseClockTime = (text: string) => {
  if (!/^\d+(?::\d{1,2}){1,2}(?:\.\d+)?$/.test(text)) {
    throw new Error(INVALID_TIME);
  }
  const parts = text.split(":").map(Number);
  if (parts.slice(1).some((part) => part >= 60)) throw new Error(INVALID_TIME);
  return parts.reduce((total, part) => total * 60 + part, 0);
};

const parseYoutubeTime = (text: string) => {
  const match = /^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?$/.exec(text);
  if (!match) throw new Error(INVALID_TIME);
  const hours = Number(match[1] || 0);
  const minutes = Number(match[2] || 0);
  const seconds = Number(match[3] || 0);
  return hours * 3600 + minutes * 60 + seconds;
};

const validateSeconds = (seconds: number) => {
  if (!Number.isFinite(seconds)) throw new Error("Enter a finite start time.");
  return Math.round(seconds * 1000) / 1000;
};

/** Convert a supported timestamp; an empty field starts at zero. */
export const parseStartTime = (value: string): number => {
  const text = value.trim();
  if (!text) return 0;
  if (text.includes(":")) return validateSeconds(parseClockTime(text));
  if (/[hms]$/.test(text)) return validateSeconds(parseYoutubeTime(text));
  return validateSeconds(parseSeconds(text));
};

export const formatStartTime = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const [whole, fraction] = (seconds % 60).toFixed(3).split(".");
  const decimals = fraction.replace(/0+$/, "");
  const remainder = whole.padStart(2, "0") + (decimals ? `.${decimals}` : "");
  if (hours) return `${hours}:${String(minutes).padStart(2, "0")}:${remainder}`;
  return `${minutes}:${remainder}`;
};

export const youtubeStartTime = (value: string): string => {
  try {
    const url = new URL(value);
    const hosts = ["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"];
    if (!hosts.includes(url.hostname)) return "";
    const fragment = new URLSearchParams(url.hash.slice(1));
    const timestamp =
      url.searchParams.get("t") ||
      url.searchParams.get("start") ||
      fragment.get("t");
    return timestamp ? formatStartTime(parseStartTime(timestamp)) : "";
  } catch {
    return "";
  }
};
