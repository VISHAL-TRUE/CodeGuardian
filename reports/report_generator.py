# =========================================================

# CodeGuardian - Report Generator

# =========================================================

import json

import os

from datetime import datetime

from reportlab.lib import colors

from reportlab.lib.enums import TA_CENTER

from reportlab.lib.pagesizes import A4, landscape

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.lib.units import inch

from reportlab.platypus import (

    SimpleDocTemplate,

    Paragraph,

    Spacer,

    Table,

    TableStyle,

    PageBreak

)

# =========================================================

# REPORT FOLDER

# =========================================================

REPORT_FOLDER = "reports/generated"

os.makedirs(

    REPORT_FOLDER,

    exist_ok=True

)

# =========================================================

# CREATE REPORT DATA

# =========================================================

def create_report_data(

    project_name,

    languages,

    dependency_files,

    dependencies,

    vulnerability_results,

    license_results,

    risk_results,

    project_risk,

    recommendations=None

):

    return {

        "report_information": {

            "tool": "CodeGuardian",

            "description":

                "Intelligent Software Dependency Risk Analyzer",

            "project":

                project_name,

            "generated_at":

                datetime.now().strftime(

                    "%Y-%m-%d %H:%M:%S"

                )

        },

        "project": {

            "name":

                project_name,

            "languages":

                languages,

            "dependency_files":

                dependency_files

        },

        "dependencies":

            dependencies,

        "vulnerabilities":

            vulnerability_results,

        "licenses":

            license_results,

        "risk_analysis": {

            "project":

                project_risk,

            "dependencies":

                risk_results

        },

        "recommendations":

            recommendations or []
    }

# =========================================================

# GENERATE JSON REPORT

# =========================================================

def generate_json_report(

    report_data,

    project_name

):

    safe_name = os.path.splitext(

        project_name

    )[0]

    filename = (

        safe_name

        + "_CodeGuardian_Report.json"

    )

    filepath = os.path.join(

        REPORT_FOLDER,

        filename

    )

    with open(

        filepath,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            report_data,

            file,

            indent=4,

            default=str

        )

    return filepath

# =========================================================

# ESCAPE HTML

# =========================================================

def escape_html(value):

    if value is None:

        return ""

    value = str(value)

    return (

        value

        .replace("&", "&amp;")

        .replace("<", "&lt;")

        .replace(">", "&gt;")

        .replace('"', "&quot;")

        .replace("'", "&#39;")

    )

def display_value(value, fallback="N/A"):
    if value is None or value == "":
        return fallback
    return str(value)
# =========================================================

# GENERATE HTML REPORT

# =========================================================

def generate_html_report(

    report_data,

    project_name

):

    safe_name = os.path.splitext(

        project_name

    )[0]

    filename = (

        safe_name

        + "_CodeGuardian_Report.html"

    )

    filepath = os.path.join(

        REPORT_FOLDER,

        filename

    )

    project = report_data["project"]

    project_risk = (

        report_data[

            "risk_analysis"

        ]["project"]

    )

    vulnerabilities = (

        report_data["vulnerabilities"]

    )

    licenses = (

        report_data["licenses"]

    )

    risk_results = (

        report_data[

            "risk_analysis"

        ]["dependencies"]

    )

    risk_level = (

        project_risk.get(

            "project_risk",

            "LOW"

        )

    )

    total_vulnerabilities = (

        project_risk.get(

            "total_vulnerabilities",

            0

        )

    )

    vulnerability_rows = ""

    for result in vulnerabilities:

        dependency_name = escape_html(

            result.get(

                "name",

                "Unknown"

            )

        )

        version = escape_html(

            result.get(

                "version",

                "Unknown"

            )

        )

        vulnerability_list = result.get(

            "vulnerabilities",

            []

        )

        scan_status = str(result.get("status", "scanned")).lower()
        scan_reason = escape_html(
            result.get("reason") or result.get("message") or ""
        )

        if not vulnerability_list:
            if scan_status == "not_scanned":
                status_message = "Not assessed"
            elif scan_status in ("error", "failed", "scan_error"):
                status_message = "Scan error"
            else:
                status_message = "No known vulnerabilities"

            if scan_reason and status_message != "No known vulnerabilities":
                status_message += ": " + scan_reason

            vulnerability_rows += f"""
            <tr>
                <td>{dependency_name}</td>
                <td>{version}</td>
                <td colspan="4">{status_message}</td>
            </tr>
            """
            continue

        for vulnerability in vulnerability_list:

            vulnerability_id = escape_html(

                vulnerability.get(

                    "id",

                    "Unknown"

                )

            )

            severity = escape_html(

                vulnerability.get(

                    "severity",

                    "UNKNOWN"

                )

            )

            cvss_score = vulnerability.get(

                "cvss_score"

            )

            if cvss_score is None:

                cvss_score = "N/A"

            summary = escape_html(

                vulnerability.get(

                    "summary",

                    "No summary available."

                )

            )

            vulnerability_rows += f"""

            <tr>

                <td>{dependency_name}</td>

                <td>{version}</td>

                <td>{vulnerability_id}</td>

                <td>{severity}</td>

                <td>{cvss_score}</td>

                <td>{summary}</td>

            </tr>

            """

    license_rows = ""

    for license_result in licenses:

        name = escape_html(

            license_result.get(

                "name",

                "Unknown"

            )

        )

        version = escape_html(

            license_result.get(

                "version",

                "Unknown"

            )

        )

        license_name = escape_html(

            license_result.get(

                "license",

                "Unknown"

            )

        )

        license_risk = escape_html(

            license_result.get(

                "risk",

                "UNKNOWN"

            )

        )

        license_rows += f"""

        <tr>

            <td>{name}</td>

            <td>{version}</td>

            <td>{license_name}</td>

            <td>{license_risk}</td>

        </tr>

        """

    risk_rows = ""

    for risk in risk_results:

        name = escape_html(
        str(
            risk.get(
                "name",
                "Unknown"
            )
        )
    )

    version = escape_html(
        str(
            risk.get(
                "version",
                "Unknown"
            )
        )
    )

    risk_score = risk.get("risk_score")

    vulnerability_score = risk.get(
        "vulnerability_score"
    )

    license_score = risk.get(
        "license_score"
    )

    risk_level = str(
        risk.get(
            "risk_level",
            "LOW"
        )
    )

    # Display missing values as N/A
    if risk_score is None:
        risk_score_display = "N/A"
    else:
        risk_score_display = (
            str(risk_score) + " / 10"
        )

    if vulnerability_score is None:
        vulnerability_score_display = "N/A"
    else:
        vulnerability_score_display = str(
            vulnerability_score
        )

    if license_score is None:
        license_score_display = "N/A"
    else:
        license_score_display = str(
            license_score
        )

    # Display NOT ASSESSED clearly
    if risk_level.upper() == "NOT ASSESSED":
        risk_level_display = "NOT ASSESSED"
    else:
        risk_level_display = escape_html(
            risk_level
        )

    risk_rows += f"""
    <tr>
        <td>{name}</td>

        <td>{version}</td>

        <td>{risk_score_display}</td>

        <td>{risk_level_display}</td>

        <td>{vulnerability_score_display}</td>

        <td>{license_score_display}</td>
    </tr>
    """

    recommendation_rows = ""
    recommendations = report_data.get("recommendations", [])
    for recommendation in recommendations:
        recommendation_rows += f"""
        <tr>
            <td>{escape_html(recommendation.get("dependency", "Unknown"))}
                {escape_html(recommendation.get("version", ""))}</td>
            <td>{escape_html(recommendation.get("issue", "Dependency issue"))}</td>
            <td>{escape_html(recommendation.get("severity", recommendation.get("risk_level", "UNKNOWN")))}</td>
            <td>{escape_html(recommendation.get("why_it_matters", ""))}</td>
            <td>{escape_html(recommendation.get("recommendation", ""))}</td>
            <td>{escape_html(recommendation.get("suggested_action", ""))}</td>
            <td>{escape_html(recommendation.get("priority", "UNKNOWN"))}</td>
            <td>{escape_html(recommendation.get("status", "unknown"))}
                {escape_html(recommendation.get("diagnostic", ""))}</td>
        </tr>
        """

    if not recommendation_rows:
        recommendation_rows = """
        <tr><td colspan="8">No actionable dependency issues requiring remediation.</td></tr>
        """

    language_list = ""


    for language in project.get(

        "languages",

        []

    ):

        language_list += (

            "<li>"

            + escape_html(language)

            + "</li>"

        )

    dependency_file_list = ""

    for dependency_file in project.get(

        "dependency_files",

        []

    ):

        dependency_file_list += (

            "<li>"

            + escape_html(

                dependency_file.get(

                    "file",

                    "Unknown"

                )

            )

            + "</li>"

        )

    html = f"""

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"

      content="width=device-width, initial-scale=1.0">

<title>

CodeGuardian Security Report

</title>

<style>

body {{

    font-family: Arial, sans-serif;

    margin: 0;

    padding: 0;

    background: #f4f6f8;

    color: #222;

}}

.container {{

    width: 90%;

    max-width: 1200px;

    margin: 30px auto;

}}

.header {{

    background: #17202a;

    color: white;

    padding: 30px;

    border-radius: 10px;

}}

.header h1 {{

    margin: 0;

}}

.section {{

    background: white;

    margin-top: 25px;

    padding: 25px;

    border-radius: 10px;

    box-shadow: 0 2px 10px rgba(0,0,0,0.08);

}}

.summary-grid {{

    display: grid;

    grid-template-columns:

        repeat(auto-fit, minmax(180px, 1fr));

    gap: 15px;

}}

.summary-card {{

    padding: 20px;

    border-radius: 8px;

    background: #f8f9fa;

    text-align: center;

}}

.summary-card h3 {{

    margin-top: 0;

}}

.risk {{

    font-weight: bold;

}}

table {{

    width: 100%;

    border-collapse: collapse;

    margin-top: 15px;

}}

th,

td {{

    border: 1px solid #ddd;

    padding: 10px;

    text-align: left;

    vertical-align: top;

}}

th {{

    background: #17202a;

    color: white;

}}

ul {{

    line-height: 1.8;

}}

.footer {{

    margin-top: 30px;

    text-align: center;

    color: #666;

    padding: 20px;

}}

</style>

</head>

<body>

<div class="container">

<div class="header">

<h1>

CodeGuardian

</h1>

<p>

Intelligent Software Dependency Risk Analyzer

</p>

<p>

<strong>Project:</strong>

{escape_html(project.get("name", "Unknown"))}

</p>

<p>

<strong>Generated:</strong>

{escape_html(

    report_data[

        "report_information"

    ]["generated_at"]

)}

</p>

</div>

<div class="section">

<h2>

Project Risk Summary

</h2>

<div class="summary-grid">

<div class="summary-card">

<h3>Risk Score</h3>

<p>

{project_risk.get("project_score", 0)}

/ 10

</p>

</div>

<div class="summary-card">

<h3>Risk Level</h3>

<p class="risk">

{escape_html(risk_level)}

</p>

</div>

<div class="summary-card">

<h3>Dependencies</h3>

<p>

{project_risk.get(

    "total_dependencies",

    0

)}

</p>

</div>

<div class="summary-card">

<h3>Vulnerabilities</h3>

<p>

{total_vulnerabilities}

</p>

</div>

<div class="summary-card">

<h3>Critical</h3>

<p>

{project_risk.get(

    "critical_dependencies",

    0

)}

</p>

</div>

<div class="summary-card">

<h3>High Risk</h3>

<p>

{project_risk.get(

    "high_dependencies",

    0

)}

</p>

</div>

<div class="summary-card">

<h3>Medium Risk</h3>

<p>

{project_risk.get(

    "medium_dependencies",

    0

)}

</p>

</div>

<div class="summary-card">

<h3>Low Risk</h3>

<p>

{project_risk.get(

    "low_dependencies",

    0

)}

</p>

</div>

</div>

</div>

<div class="section">

<h2>

Project Information

</h2>

<h3>

Detected Languages

</h3>

<ul>

{language_list}

</ul>

<h3>

Dependency Files

</h3>

<ul>

{dependency_file_list}

</ul>

</div>

<div class="section">

<h2>

Vulnerability Analysis

</h2>

<table>

<thead>

<tr>

<th>Dependency</th>

<th>Version</th>

<th>Vulnerability ID</th>

<th>Severity</th>

<th>CVSS</th>

<th>Summary</th>

</tr>

</thead>


<tbody>

{vulnerability_rows}

</tbody>

</table>

</div>

<div class="section">

<h2>

License Analysis

</h2>

<table>

<thead>

<tr>

<th>Dependency</th>

<th>Version</th>

<th>License</th>

<th>License Risk</th>

</tr>

</thead>

<tbody>

{license_rows}

</tbody>

</table>

</div>

<div class="section">

<h2>

Dependency Risk Analysis

</h2>

<table>

<thead>

<tr>

<th>Dependency</th>

<th>Version</th>

<th>Risk Score</th>

<th>Risk Level</th>

<th>Vulnerability Score</th>

<th>License Score</th>

</tr>

</thead>

<tbody>

{risk_rows}

</tbody>

</table>

</div>

<div class="section">

<h2>AI-Powered Remediation Recommendations</h2>

<table>
<thead>
<tr>
<th>Dependency</th>
<th>Issue</th>
<th>Severity / Risk</th>
<th>Why It Matters</th>
<th>Recommendation</th>
<th>Suggested Action</th>
<th>Priority</th>
<th>AI Status / Diagnostic</th>
</tr>
</thead>
<tbody>
{recommendation_rows}
</tbody>
</table>

</div>

<div class="footer">

<p>

Generated by CodeGuardian

</p>

<p>

Intelligent Software Dependency Risk Analyzer

</p>

</div>

</div>

</body>

</html>

"""

    with open(

        filepath,

        "w",

        encoding="utf-8"

    ) as file:

        file.write(html)

    return filepath

# =========================================================

# GENERATE PDF REPORT

# =========================================================

def generate_pdf_report(

    report_data,

    project_name

):

    safe_name = os.path.splitext(

        project_name

    )[0]

    filename = (

        safe_name

        + "_CodeGuardian_Report.pdf"

    )

    filepath = os.path.join(

        REPORT_FOLDER,

        filename

    )

    document = SimpleDocTemplate(

        filepath,

        pagesize=landscape(A4),

        rightMargin=35,

        leftMargin=35,

        topMargin=35,

        bottomMargin=35

    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(

        "ReportTitle",

        parent=styles["Title"],

        alignment=TA_CENTER,

        fontSize=22,

        spaceAfter=10

    )

    subtitle_style = ParagraphStyle(

        "Subtitle",

        parent=styles["Normal"],

        alignment=TA_CENTER,

        fontSize=11,

        spaceAfter=20

    )

    heading_style = ParagraphStyle(

        "Heading",

        parent=styles["Heading2"],

        fontSize=15,

        spaceBefore=15,

        spaceAfter=10

    )

    normal_style = ParagraphStyle(

        "NormalText",

        parent=styles["Normal"],

        fontSize=9,

        leading=13

    )

    small_style = ParagraphStyle(

        "SmallText",

        parent=styles["Normal"],

        fontSize=7,

        leading=9

    )

    story = []

    # =====================================================

    # TITLE

    # =====================================================

    story.append(

        Paragraph(

            "CodeGuardian",

            title_style

        )

    )

    story.append(

        Paragraph(

            "Intelligent Software Dependency Risk Analyzer",

            subtitle_style

        )

    )

    report_info = report_data[

        "report_information"

    ]

    story.append(

        Paragraph(

            "<b>Project:</b> "

            + escape_html(

                report_info.get(

                    "project",

                    "Unknown"

                )

            ),

            normal_style

        )

    )

    story.append(

        Paragraph(

            "<b>Generated:</b> "

            + escape_html(

                report_info.get(

                    "generated_at",

                    "Unknown"

                )

            ),

            normal_style

        )

    )

    story.append(

        Spacer(

            1,

            20

        )

    )

    # =====================================================

    # PROJECT RISK SUMMARY

    # =====================================================

    story.append(

        Paragraph(

            "Project Risk Summary",

            heading_style

        )

    )

    project_risk = (

        report_data[

            "risk_analysis"

        ]["project"]

    )

    summary_data = [

        [

            "Risk Score",

            "Risk Level",

            "Dependencies",

            "Vulnerabilities"

        ],

        [

            str(

                project_risk.get(

                    "project_score",

                    0

                )

            ) + " / 10",

            str(

                project_risk.get(

                    "project_risk",

                    "LOW"

                )

            ),

            str(

                project_risk.get(

                    "total_dependencies",

                    0

                )

            ),

            str(

                project_risk.get(

                    "total_vulnerabilities",

                    0

                )

            )

        ]

    ]

    summary_table = Table(

        summary_data,

        colWidths=[

            1.5 * inch,

            1.5 * inch,

            1.5 * inch,

            1.5 * inch

        ]

    )

    summary_table.setStyle(

        TableStyle([

            (

                "BACKGROUND",

                (0, 0),

                (-1, 0),

                colors.HexColor(

                    "#17202a"

                )

            ),

            (

                "TEXTCOLOR",

                (0, 0),

                (-1, 0),

                colors.white

            ),

            (

                "FONTNAME",

                (0, 0),

                (-1, 0),

                "Helvetica-Bold"

            ),

            (

                "ALIGN",

                (0, 0),

                (-1, -1),

                "CENTER"

            ),

            (

                "GRID",

                (0, 0),

                (-1, -1),

                0.5,

                colors.grey

            ),

            (

                "PADDING",

                (0, 0),

                (-1, -1),

                8

            )

        ])

    )

    story.append(

        summary_table

    )

    story.append(

        Spacer(

            1,

            15

        )

    )

    # =====================================================

    # PROJECT INFORMATION

    # =====================================================

    story.append(

        Paragraph(

            "Project Information",

            heading_style

        )

    )

    project = report_data[

        "project"

    ]

    languages = project.get(

        "languages",

        []

    )

    language_text = ", ".join(

        str(language)

        for language in languages

    )

    story.append(

        Paragraph(

            "<b>Detected Languages:</b> "

            + escape_html(

                language_text

            ),

            normal_style

        )

    )

    dependency_files = project.get(

        "dependency_files",

        []

    )

    dependency_file_names = []

    for dependency_file in dependency_files:

        dependency_file_names.append(

            dependency_file.get(

                "file",

                "Unknown"

            )

        )

    story.append(

        Paragraph(

            "<b>Dependency Files:</b> "

            + escape_html(

                ", ".join(

                    dependency_file_names

                )

            ),

            normal_style

        )

    )

    # =====================================================

    # VULNERABILITY ANALYSIS

    # =====================================================

    story.append(

        Paragraph(

            "Vulnerability Analysis",

            heading_style

        )

    )

    vulnerability_data = [

        [

            "Dependency",

            "Version",

            "ID",

            "Severity",

            "CVSS"

        ]

    ]

    for result in report_data[

        "vulnerabilities"

    ]:

        dependency_name = result.get(

            "name",

            "Unknown"

        )

        version = result.get(

            "version",

            "Unknown"

        )

        vulnerability_list = result.get(

            "vulnerabilities",

            []

        )

        if not vulnerability_list:
            scan_status = str(result.get("status", "scanned")).lower()
            if scan_status == "not_scanned":
                status_text = "Not assessed"
            elif scan_status in ("error", "failed", "scan_error"):
                status_text = "Scan error"
            else:
                status_text = "No known vulnerabilities"

            reason = result.get("reason") or result.get("message")
            if reason and status_text != "No known vulnerabilities":
                status_text += ": " + str(reason)

            vulnerability_data.append(
                [
                    str(dependency_name),
                    str(version),
                    status_text,
                    "N/A",
                    "N/A"
                ]
            )
            continue

        for vulnerability in vulnerability_list:

            cvss_score = vulnerability.get(

                "cvss_score"

            )

            if cvss_score is None:

                cvss_score = "N/A"

            vulnerability_data.append(

                [

                    str(

                        dependency_name

                    ),

                    str(

                        version

                    ),

                    str(

                        vulnerability.get(

                            "id",

                            "Unknown"

                        )

                    ),

                    str(

                        vulnerability.get(

                            "severity",

                            "UNKNOWN"

                        )

                    ),

                    str(

                        cvss_score

                    )

                ]

            )

    vulnerability_table = Table(

        vulnerability_data,

        repeatRows=1,

        colWidths=[

            1.25 * inch,

            0.85 * inch,

            1.35 * inch,

            0.75 * inch,

            0.55 * inch

        ]

    )

    vulnerability_table.setStyle(

        TableStyle([

            (

                "BACKGROUND",

                (0, 0),

                (-1, 0),

                colors.HexColor(

                    "#17202a"

                )

            ),

            (

                "TEXTCOLOR",

                (0, 0),

                (-1, 0),

                colors.white

            ),

            (

                "FONTNAME",

                (0, 0),

                (-1, 0),

                "Helvetica-Bold"

            ),

            (

                "FONTSIZE",

                (0, 0),

                (-1, -1),

                7

            ),

            (

                "GRID",

                (0, 0),

                (-1, -1),

                0.4,

                colors.grey

            ),

            (

                "VALIGN",

                (0, 0),

                (-1, -1),

                "TOP"

            ),

            (

                "PADDING",

                (0, 0),

                (-1, -1),

                5

            )

        ])

    )

    story.append(

        vulnerability_table

    )

    # =====================================================

    # LICENSE ANALYSIS

    # =====================================================

    story.append(

        PageBreak()

    )

    story.append(

        Paragraph(

            "License Analysis",

            heading_style

        )

    )

    license_data = [

        [

            "Dependency",

            "Version",

            "License",

            "Risk"

        ]

    ]

    for license_result in report_data[

        "licenses"

    ]:

        license_data.append(

            [

                str(

                    license_result.get(

                        "name",

                        "Unknown"

                    )

                ),

                str(

                    license_result.get(

                        "version",

                        "Unknown"

                    )

                ),

                str(

                    license_result.get(

                        "license",

                        "Unknown"

                    )

                ),

                str(

                    license_result.get(

                        "risk",

                        "UNKNOWN"

                    )

                )

            ]

        )

    license_table = Table(

        license_data,

        repeatRows=1,

        colWidths=[

            1.8 * inch,

            1.1 * inch,

            2.0 * inch,

            1.0 * inch

        ]

    )

    license_table.setStyle(

        TableStyle([

            (

                "BACKGROUND",

                (0, 0),

                (-1, 0),

                colors.HexColor(

                    "#17202a"

                )

            ),

            (

                "TEXTCOLOR",

                (0, 0),

                (-1, 0),

                colors.white

            ),

            (

                "FONTNAME",

                (0, 0),

                (-1, 0),

                "Helvetica-Bold"

            ),

            (

                "FONTSIZE",

                (0, 0),

                (-1, -1),

                8

            ),

            (

                "GRID",

                (0, 0),

                (-1, -1),

                0.4,

                colors.grey

            ),

            (

                "PADDING",

                (0, 0),

                (-1, -1),

                6

            )

        ])

    )

    story.append(

        license_table

    )

    # =====================================================

    # DEPENDENCY RISK ANALYSIS

    # =====================================================

    story.append(

        Paragraph(

            "Dependency Risk Analysis",

            heading_style

        )

    )

    risk_data = [

        [

            "Dependency",

            "Version",

            "Score",

            "Level",

            "Vuln.",

            "License"

        ]

    ]

    
    for risk in report_data["risk_analysis"]["dependencies"]:

        name = str(
            risk.get(
                "name",
                "Unknown"
            )
        )

        version = str(
            risk.get(
                "version",
                "Unknown"
            )
        )

        risk_score = risk.get("risk_score")

        vulnerability_score = risk.get(
            "vulnerability_score"
        )

        license_score = risk.get(
            "license_score"
        )

        risk_level = str(
            risk.get(
                "risk_level",
                "LOW"
            )
        )
    

        # Display missing values as N/A
        if risk_score is None:
            risk_score_display = "N/A"
        else:
            risk_score_display = (
                str(risk_score) + " / 10"
            )

        if vulnerability_score is None:
            vulnerability_score_display = "N/A"
        else:
            vulnerability_score_display = str(
                vulnerability_score
            )

        if license_score is None:
            license_score_display = "N/A"
        else:
            license_score_display = str(
                license_score
            )

        # Keep the scan failure reason visible for unassessed dependencies.
        risk_level_display = risk_level
        scan_reason = risk.get("scan_reason")
        if risk_level.upper() == "NOT ASSESSED" and scan_reason:
            risk_level_display += ": " + str(scan_reason)

        risk_data.append(
            [
                name,
                version,
                risk_score_display,
                risk_level_display,
                vulnerability_score_display,
                license_score_display
            ]
        )
    


    risk_table = Table(
        risk_data,
        repeatRows=1,
        colWidths=[
            1.75 * inch,
            0.90 * inch,
            0.90 * inch,
            1.00 * inch,
            0.70 * inch,
            0.70 * inch
        ]
    )

    risk_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#1b2128"
                    )
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, 0),
                    8
                ),

                (
                    "FONTSIZE",
                    (0, 1),
                    (-1, -1),
                    7
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "CENTER"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )

    story.append(
        risk_table
    )

    # =====================================================
    # AI-POWERED REMEDIATION RECOMMENDATIONS
    # =====================================================

    story.append(
        Paragraph(
            "AI-Powered Remediation Recommendations",
            heading_style
        )
    )

    recommendations = report_data.get("recommendations", [])
    if not recommendations:
        story.append(
            Paragraph(
                "No actionable dependency issues requiring remediation.",
                normal_style
            )
        )

    for recommendation in recommendations:
        story.append(
            Paragraph(
                "<b>Dependency:</b> "
                + escape_html(recommendation.get("dependency", "Unknown"))
                + " "
                + escape_html(recommendation.get("version", "")),
                normal_style
            )
        )
        for label, key, fallback in (
            ("Issue", "issue", "Dependency issue"),
            ("Severity / Risk", "severity", "UNKNOWN"),
            ("Why it matters", "why_it_matters", ""),
            ("Recommendation", "recommendation", ""),
            ("Suggested action", "suggested_action", ""),
            ("Priority", "priority", "UNKNOWN"),
            ("AI status", "status", "unknown"),
        ):
            story.append(
                Paragraph(
                    "<b>"
                    + label
                    + ":</b> "
                    + escape_html(recommendation.get(key, fallback)),
                    normal_style
                )
            )
        diagnostic = recommendation.get("diagnostic")
        if diagnostic:
            story.append(
                Paragraph(
                    "<b>AI diagnostic:</b> " + escape_html(diagnostic),
                    normal_style
                )
            )
        story.append(Spacer(1, 8))

    # =====================================================

    # BUILD PDF

    # =====================================================

    document.build(

        story

    )

    return filepath