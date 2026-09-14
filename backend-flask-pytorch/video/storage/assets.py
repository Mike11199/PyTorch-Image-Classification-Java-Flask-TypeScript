"""Video files and playback links, backed by S3 or the local data directory."""

import json
import shutil
import tempfile
import time
from pathlib import Path, PurePosixPath
from urllib.parse import quote


class VideoAssets:
    """Store input files, normalized videos, masks, and manifests."""

    def __init__(self, root, bucket):
        """Use S3 when a bucket is configured, otherwise the local directory."""
        self.root = root
        self.bucket = bucket
        if bucket:
            import boto3

            self.s3 = boto3.client("s3")

    def put_file(self, key, path, content_type):
        if self.bucket:
            self.s3.upload_file(
                str(path), self.bucket, key, ExtraArgs={"ContentType": content_type}
            )
        else:
            target = self.root / "objects" / key
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)

    def download(self, key, path):
        if self.bucket:
            self.s3.download_file(self.bucket, key, str(path))
        else:
            shutil.copyfile(self.root / "objects" / key, path)

    def size(self, key):
        if self.bucket:
            return self.s3.head_object(Bucket=self.bucket, Key=key)["ContentLength"]
        return (self.root / "objects" / key).stat().st_size

    def read_json(self, key):
        if self.bucket:
            return json.loads(
                self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read()
            )
        return json.loads((self.root / "objects" / key).read_text())

    def url(self, job, key):
        """Issue a fresh playback URL without changing retained object lifetime."""
        if self.bucket:
            now = int(time.time())
            expires_at = job.get("expiresAt") or now + 3600
            lifetime = max(1, min(3600, expires_at - now))
            return self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=lifetime,
            )
        relative = key.removeprefix(f"jobs/{job['id']}/")
        return f"/api-java-spring-boot/video-jobs/{job['id']}/assets/{quote(relative)}?token={job['token']}"

    def upload_destination(self, job):
        """Give the browser a local PUT endpoint or signed S3 POST fields."""
        key = f"jobs/{job['id']}/input"
        if self.bucket:
            return self.s3.generate_presigned_post(self.bucket, key, ExpiresIn=3600)
        return {
            "url": f"/api-java-spring-boot/video-jobs/{job['id']}/upload",
            "local": True,
        }

    def local_path(self, job, name):
        """Restrict local asset requests to the selected job's result directory."""
        if (
            self.bucket
            or ".." in PurePosixPath(name).parts
            or "\\" in name
            or name.startswith("/")
        ):
            raise PermissionError("Asset not found.")
        key = (
            name
            if name.startswith(("examples/", "videos/"))
            else f"jobs/{job['id']}/{name}"
        )
        manifest = job.get("manifest")
        preview = job.get("previewKey")
        if preview and key.startswith(str(PurePosixPath(preview).parent) + "/"):
            return self.root / "objects" / key
        if not manifest or not key.startswith(
            str(PurePosixPath(manifest).parent) + "/"
        ):
            raise PermissionError("Asset not found.")
        return self.root / "objects" / key

    def remove_temporary(self, job_id):
        """Remove temporary local files for an expired job."""
        shutil.rmtree(self.root / "objects" / "jobs" / job_id, ignore_errors=True)

    def save_upload(self, job_id, stream):
        """Spool local uploads to disk without buffering the entire file in memory."""
        with tempfile.TemporaryDirectory(dir=self.root) as work:
            path = Path(work) / "input"
            with path.open("wb") as output:
                shutil.copyfileobj(stream, output, length=65536)
            self.put_file(f"jobs/{job_id}/input", path, "application/octet-stream")
