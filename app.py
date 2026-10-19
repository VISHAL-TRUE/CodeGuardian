from flask import (
    Flask,
    render_template,
    request,
    send_from_directory
)

import os
import zipfile

from werkzeug.utils import secure_filename

from scanner.project_detector import (
    detect_project
)

from scanner.dependency_parser import (
    extract_all_dependencies
)

from analyzers.vulnerability_analyzer import (
    analyze_dependencies
)

from analyzers.license_analyzer import (
    analyze_licenses
)

from analyzers.risk_analyzer import (
    analyze_risks
)

from reports.report_generator import (
    create_report_data,
    generate_json_report,
    generate_html_report,
    generate_pdf_report
)


app = Flask(__name__)


# =========================================================
# FOLDERS
# =========================================================

UPLOAD_FOLDER = "uploads"

EXTRACT_FOLDER = "extracted_projects"

REPORT_FOLDER = "reports/generated"


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    EXTRACT_FOLDER,
    exist_ok=True
)

os.makedirs(
    REPORT_FOLDER,
    exist_ok=True
)


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# DOWNLOAD REPORT
# =========================================================

@app.route(
    "/reports/<path:filename>"
)
def download_report(filename):

    return send_from_directory(
        REPORT_FOLDER,
        filename,
        as_attachment=True
    )


# =========================================================
# UPLOAD PROJECT
# =========================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_project():

    if "project" not in request.files:

        return "No file selected."


    file = request.files["project"]


    if file.filename == "":

        return "No file selected."


    if not file.filename.lower().endswith(
        ".zip"
    ):

        return "Please upload a ZIP file."


    filename = secure_filename(
        file.filename
    )


    zip_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    file.save(
        zip_path
    )


    project_name = os.path.splitext(
        filename
    )[0]


    extract_path = os.path.join(
        EXTRACT_FOLDER,
        project_name
    )


    os.makedirs(
        extract_path,
        exist_ok=True
    )


    # =====================================================
    # SAFE ZIP EXTRACTION
    # =====================================================

    try:

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zip_ref:

            for member in zip_ref.infolist():

                member_path = (
                    os.path.abspath(
                        os.path.join(
                            extract_path,
                            member.filename
                        )
                    )
                )


                safe_path = (
                    os.path.abspath(
                        extract_path
                    )
                    + os.sep
                )


                if not member_path.startswith(
                    safe_path
                ):

                    return (
                        "Unsafe ZIP file detected."
                    )


            zip_ref.extractall(
                extract_path
            )


    except zipfile.BadZipFile:

        return "Invalid ZIP file."


    # =====================================================
    # PROJECT DETECTION
    # =====================================================

    result = detect_project(
        extract_path
    )


    # =====================================================
    # DEPENDENCY EXTRACTION
    # =====================================================

    dependencies = (
        extract_all_dependencies(
            result[
                "dependency_files"
            ]
        )
    )


    # =====================================================
    # VULNERABILITY ANALYSIS
    # =====================================================

    vulnerability_results = (
        analyze_dependencies(
            dependencies
        )
    )


    # =====================================================
    # LICENSE ANALYSIS
    # =====================================================

    license_results = (
        analyze_licenses(
            dependencies
        )
    )


    # =====================================================
    # RISK ANALYSIS
    # =====================================================

    risk_results = analyze_risks(
        vulnerability_results,
        license_results
    )


    # =====================================================
    # CREATE REPORT DATA
    # =====================================================

    report_data = create_report_data(

        project_name=filename,

        languages=result[
            "languages"
        ],

        dependency_files=result[
            "dependency_files"
        ],

        dependencies=dependencies,

        vulnerability_results=(
            vulnerability_results
        ),

        license_results=(
            license_results
        ),

        risk_results=(
            risk_results[
                "dependencies"
            ]
        ),

        project_risk=(
            risk_results[
                "project"
            ]
        )
    )


    # =====================================================
    # GENERATE REPORTS
    # =====================================================

    json_report_path = (
        generate_json_report(
            report_data,
            filename
        )
    )


    html_report_path = (
        generate_html_report(
            report_data,
            filename
        )
    )


    pdf_report_path = (
        generate_pdf_report(
            report_data,
            filename
        )
    )


    # =====================================================
    # REPORT FILENAMES
    # =====================================================

    json_report_filename = os.path.basename(
        json_report_path
    )

    html_report_filename = os.path.basename(
        html_report_path
    )

    pdf_report_filename = os.path.basename(
        pdf_report_path
    )


    # =====================================================
    # RENDER RESULTS
    # =====================================================

    return render_template(

        "scan_result.html",

        project_name=filename,

        languages=result[
            "languages"
        ],

        dependency_files=result[
            "dependency_files"
        ],

        dependencies=dependencies,

        vulnerability_results=(
            vulnerability_results
        ),

        license_results=(
            license_results
        ),

        risk_results=(
            risk_results[
                "dependencies"
            ]
        ),

        project_risk=(
            risk_results[
                "project"
            ]
        ),

        json_report_filename=(
            json_report_filename
        ),

        html_report_filename=(
            html_report_filename
        ),

        pdf_report_filename=(
            pdf_report_filename
        )
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )