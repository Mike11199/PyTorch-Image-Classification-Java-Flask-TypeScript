import { useState } from "react";
import { cancelVideoJob, createVideoJob } from "../api/videoRequests";
import { uploadVideo } from "../api/videoUploads";
import { videoSubmissionOptions } from "../helpers/videoSource";
import type { VideoSubmission } from "../helpers/videoSource";
import type {
  CreatedVideoJob,
  VideoConfig,
  VideoJob,
} from "../types";

export const useVideoSubmission = (
  config: VideoConfig | null,
  onSelect: (job: VideoJob) => void
) => {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (submission: VideoSubmission) => {
    const { input, file } = submission;
    setError("");
    setBusy(true);
    let created: CreatedVideoJob | null = null;
    try {
      if (!config)
        throw new Error(
          "The video service is unavailable. Please try again shortly."
        );
      const options = videoSubmissionOptions({
        ...submission,
        examples: config.examples,
      });
      created = await createVideoJob(options);
      if (input === "upload" && file) await uploadVideo(created, file);
      onSelect(created);
    } catch (error) {
      setError((error as Error).message);
      if (created) await cancelVideoJob(created).catch(() => undefined);
    } finally {
      setBusy(false);
    }
  };

  return { busy, error, submit };
};
