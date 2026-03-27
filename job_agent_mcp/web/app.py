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
    import sys

    import click

    # Flask/Werkzeug startup messages pollute MCP's stdout-based JSON transport.
    # 1) Silence via logging: set ERROR level and disable propagation so messages
    #    never reach the root logger (which may have a stdout StreamHandler).
    null_handler = logging.NullHandler()
    for name in ("werkzeug", "werkzeug.serving", "flask.app", "flask"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        logger.handlers = [h for h in logger.handlers if getattr(h, "stream", None) is not sys.stdout]
        if not logger.handlers:
            logger.addHandler(null_handler)

    # 2) Werkzeug also uses click.echo for some banner lines (e.g. "* Running on …").
    #    Redirect those to stderr so they never touch stdout.
    _orig_echo = click.echo

    def _echo_to_stderr(message=None, file=None, nl=True, err=False, color=None):
        _orig_echo(message, file=file if file is not None else sys.stderr, nl=nl, err=err, color=color)

    click.echo = _echo_to_stderr

    app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=False)
