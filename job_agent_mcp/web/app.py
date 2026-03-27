"""Flask web UI for job-agent-mcp configuration."""
from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from job_agent_mcp.config import (
    COMPANY_SIZE_LABELS,
    COMPANY_SIZES,
    JOB_CATEGORIES,
    JOB_CATEGORY_LABELS,
    extract_page_id,
    load_config,
    save_config,
)

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = os.urandom(24)


@app.route("/")
def index():
    cfg = load_config()
    return render_template(
        "index.html",
        cfg=cfg,
        job_category_labels=JOB_CATEGORY_LABELS,
        company_size_labels=COMPANY_SIZE_LABELS,
        company_sizes=COMPANY_SIZES,
    )


@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = load_config()
    return jsonify(
        {
            "notion_token": cfg.notion_token,
            "notion_cv_page_id": cfg.notion_cv_page_id,
            "job_category_indices": cfg.job_category_indices,
            "company_sizes": cfg.company_sizes,
            "device_uid": cfg.device_uid,
        }
    )


@app.route("/api/config", methods=["POST"])
def post_config():
    data = request.get_json(force=True)
    cfg = load_config()

    if "notion_token" in data:
        cfg.notion_token = data["notion_token"].strip()
    if "notion_cv_page_url" in data:
        raw = data["notion_cv_page_url"].strip()
        cfg.notion_cv_page_id = extract_page_id(raw) if raw else ""
    if "notion_cv_page_id" in data:
        cfg.notion_cv_page_id = data["notion_cv_page_id"].strip()
    if "job_category_indices" in data:
        indices = data["job_category_indices"]
        cfg.job_category_indices = [int(i) for i in indices if 0 <= int(i) < len(JOB_CATEGORY_LABELS)]
    if "company_sizes" in data:
        sizes = data["company_sizes"]
        cfg.company_sizes = [s for s in sizes if s in COMPANY_SIZES]

    save_config(cfg)
    return jsonify({"ok": True, "message": "설정이 저장되었습니다."})


def run_server(port: int = 5173, debug: bool = False):
    import logging
    from flask import cli

    # "* Serving Flask app" / "* Debug mode: off" are printed by
    # flask.cli.show_server_banner via click.echo. Replace it with a no-op.
    cli.show_server_banner = lambda *args, **kwargs: None

    # "* Running on ..." comes from werkzeug logging (INFO level).
    # Raise the level and cut propagation so it never reaches any stdout handler.
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    log.propagate = False

    app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=False)
