"""HTTP endpoints for video jobs. Model work runs in the background worker."""

from flask import Blueprint, jsonify, request, send_file

from .jobs import (
    authorize_job,
    cancel_job,
    create_job,
    start_job,
)
from .responses import job_status, playback_result
from ..config import video_config


def request_token():
    return request.headers.get("Authorization", "").removeprefix(
        "Bearer "
    ) or request.args.get("token", "")


def create_blueprint(store):
    api = Blueprint("video", __name__, url_prefix="/api-pytorch/video-jobs")

    def authorized(job_id):
        return authorize_job(store, job_id, request_token())

    @api.errorhandler(ValueError)
    def bad_request(error):
        return jsonify(error=str(error)), 400

    @api.errorhandler(PermissionError)
    def forbidden(error):
        return jsonify(error=str(error)), 404

    @api.get("/config")
    def config():
        return jsonify(video_config())

    @api.post("")
    def create():
        """Accept small JSON options and return a private job handle."""
        if request.content_length and request.content_length > 4096:
            raise ValueError("Job options are too large.")
        job = create_job(store, request.get_json(silent=True) or {})
        result = {
            "id": job["id"],
            "token": job["token"],
            "state": job["state"],
            "cached": job.get("cached", False),
        }
        if job["source"] == "upload":
            result["upload"] = store.assets.upload_destination(job)
        return jsonify(result), 201

    @api.put("/<job_id>/upload")
    def upload(job_id):
        """Stream a local upload to its reserved job."""
        job = authorized(job_id)
        if store.bucket or job["state"] != "uploading":
            raise ValueError("This upload is not available.")
        if request.content_length == 0:
            raise ValueError("Please select a non-empty video file.")
        store.assets.save_upload(job_id, request.stream)
        return jsonify(ok=True)

    @api.post("/<job_id>/start")
    def start(job_id):
        state, started = start_job(store, authorized(job_id))
        return jsonify(state=state), 202 if started else 200

    @api.get("/<job_id>")
    def status(job_id):
        return jsonify(job_status(store, authorized(job_id)))

    @api.get("/<job_id>/result")
    def result(job_id):
        return jsonify(playback_result(store, authorized(job_id)))

    @api.delete("/<job_id>")
    def cancel(job_id):
        state = cancel_job(store, job_id, request_token())
        if state is None:
            return jsonify(error="Job changed; please retry cancellation."), 409
        return jsonify(state=state)

    @api.get("/<job_id>/assets/<path:name>")
    def asset(job_id, name):
        """Serve an authorized local asset with byte-range support."""
        path = store.assets.local_path(authorized(job_id), name)
        return send_file(path, conditional=True)

    return api
