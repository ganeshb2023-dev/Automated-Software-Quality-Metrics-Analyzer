"""
Automated Software Quality Metrics Analyzer - Flask web application.

Routes
------
GET  /                      dashboard shell (single-page app)
GET  /api/sample            run the engine against the bundled sample_project
POST /api/analyze           run the engine against an uploaded .zip or .py files
POST /api/sonarqube/test    test connectivity to a configured SonarQube server
POST /api/sonarqube/fetch   pull measures from SonarQube and merge into a report
"""

import os
import shutil
import tempfile
import zipfile

from flask import Flask, jsonify, render_template, request

from analyzer import analyze_project
from sonarqube import SonarQubeClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_PROJECT_DIR = os.path.join(BASE_DIR, "sample_project")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB upload cap


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sample")
def api_sample():
    report = analyze_project(SAMPLE_PROJECT_DIR)
    report["meta"]["source"] = "bundled sample project"
    return jsonify(report)


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    tmp_dir = tempfile.mkdtemp(prefix="asqma_")
    try:
        if "zipfile" in request.files and request.files["zipfile"].filename:
            zf = request.files["zipfile"]
            zip_path = os.path.join(tmp_dir, "upload.zip")
            zf.save(zip_path)
            try:
                with zipfile.ZipFile(zip_path) as z:
                    # guard against path traversal in the archive
                    for member in z.namelist():
                        if member.startswith("/") or ".." in member:
                            return jsonify({"error": f"unsafe path in archive: {member}"}), 400
                    z.extractall(tmp_dir)
            except zipfile.BadZipFile:
                return jsonify({"error": "uploaded file is not a valid .zip archive"}), 400
            os.remove(zip_path)

        else:
            files = request.files.getlist("files")
            if not files:
                return jsonify({"error": "no files uploaded - choose a .zip or one or more .py files"}), 400
            for f in files:
                if not f.filename:
                    continue
                safe_name = f.filename.replace("..", "_").lstrip("/")
                dest = os.path.join(tmp_dir, safe_name)
                os.makedirs(os.path.dirname(dest) or tmp_dir, exist_ok=True)
                f.save(dest)

        report = analyze_project(tmp_dir)
        report["meta"]["source"] = "user upload"

        if report["meta"]["total_files_submitted"] == 0:
            return jsonify({"error": "no .py files were found in the upload"}), 400

        return jsonify(report)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.route("/api/sonarqube/test", methods=["POST"])
def api_sonarqube_test():
    cfg = request.get_json(force=True, silent=True) or {}
    required = ("base_url", "token", "project_key")
    if not all(cfg.get(k) for k in required):
        return jsonify({"ok": False, "error": "base_url, token and project_key are all required"}), 400

    client = SonarQubeClient(cfg["base_url"], cfg["token"], cfg["project_key"])
    result = client.test_connection()
    return jsonify(result)


@app.route("/api/sonarqube/fetch", methods=["POST"])
def api_sonarqube_fetch():
    cfg = request.get_json(force=True, silent=True) or {}
    required = ("base_url", "token", "project_key")
    if not all(cfg.get(k) for k in required):
        return jsonify({"ok": False, "error": "base_url, token and project_key are all required"}), 400

    client = SonarQubeClient(cfg["base_url"], cfg["token"], cfg["project_key"])
    measures = client.fetch_measures()
    if not measures.get("ok"):
        return jsonify(measures), 502

    mapped = client.to_report_format(measures["raw"])
    return jsonify({"ok": True, "raw": measures["raw"], "mapped": mapped})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
