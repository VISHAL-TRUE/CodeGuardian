# CodeGuardian – Intelligent Software Dependency Risk Analyzer

## 📌 Project Overview

**CodeGuardian** is a web-based software dependency risk analysis tool designed to analyze software projects and identify potential **security vulnerabilities, dependency risks, and software license risks**.

The system allows a user to upload a software project as a **ZIP file**. CodeGuardian extracts the project, detects the programming languages and dependency files, identifies project dependencies, performs vulnerability and license analysis, calculates dependency risk scores, and generates detailed reports.

The project is designed to support multiple programming ecosystems instead of being restricted to a single programming language.

---

## 🎯 Objectives

The main objectives of CodeGuardian are:

- To automatically detect programming languages used in a software project.
- To identify dependency and package management files.
- To extract dependencies and their versions.
- To detect known security vulnerabilities in dependencies.
- To analyze the licenses associated with dependencies.
- To calculate individual dependency risk scores.
- To calculate an overall project risk score.
- To identify dependencies that require attention.
- To generate detailed analysis reports.
- To provide the results in multiple report formats.

---

## ✨ Key Features

### 1. Project ZIP Upload

Users can upload their software project in ZIP format.

CodeGuardian extracts the uploaded project and analyzes its contents without requiring the user to manually enter dependencies.

### 2. Multi-Ecosystem Dependency Detection

The system can identify dependencies from different ecosystems, including:

- 🐍 Python
- 🟨 JavaScript / Node.js
- ☕ Java / Maven
- 🐹 Go
- 🦀 Rust

Example dependency files supported in the project include:

| Dependency File | Ecosystem |
|---|---|
| `requirements.txt` | Python |
| `package.json` | JavaScript / Node.js |
| `pom.xml` | Java / Maven |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

### 3. Dependency Extraction

CodeGuardian extracts dependency names and their specified versions from supported dependency files.

For example:

```text
flask       ==3.0.0
requests    ==2.31.0
express     4.18.2
react       18.2.0
tokio       1.35
```

### 4. Vulnerability Analysis

The system checks detected dependencies for known security vulnerabilities.

For identified vulnerabilities, CodeGuardian provides information such as:

- Vulnerability ID
- CVE / security aliases
- Severity
- CVSS score
- CVSS vector
- Vulnerability summary
- Publication information

### 5. License Analysis

CodeGuardian identifies the license associated with each dependency and classifies its license risk.

Examples of licenses detected include:

- MIT
- Apache-2.0
- BSD-3-Clause
- MIT OR Apache-2.0

The system classifies licenses according to their risk level.

### 6. Dependency Risk Analysis

CodeGuardian combines vulnerability and license information to calculate a risk score for each dependency.

The system also calculates an **overall project risk score**.

The result includes:

- Overall risk score
- Overall risk level
- Total dependencies
- Critical dependencies
- High-risk dependencies
- Medium-risk dependencies
- Low-risk dependencies
- Total vulnerabilities
- Individual dependency risk scores

### 7. Risk Classification

Dependencies are classified according to their calculated risk.

Possible classifications include:

```text
LOW
MEDIUM
HIGH
CRITICAL
NOT ASSESSED
```

### 8. Report Generation

CodeGuardian generates detailed reports containing the scan results.

Supported report formats include:

- JSON
- HTML
- PDF

The reports contain dependency information, vulnerability analysis, license analysis, and risk analysis.

---

## 🏗️ System Workflow

The overall workflow of CodeGuardian is:

```text
          User
            │
            ▼
     Upload ZIP Project
            │
            ▼
      ZIP Extraction
            │
            ▼
   Language Detection
            │
            ▼
 Dependency File Detection
            │
            ▼
   Dependency Extraction
            │
            ▼
 Vulnerability Analysis
            │
            ▼
     License Analysis
            │
            ▼
     Risk Calculation
            │
            ▼
    Report Generation
       │      │      │
       ▼      ▼      ▼
     JSON    HTML    PDF
```

---

## 🧩 Project Modules

### Upload Module

Responsible for receiving the uploaded ZIP project from the user.

### ZIP Extraction Module

Extracts the contents of the uploaded project into a temporary/project workspace for analysis.

### Language Detection Module

Identifies the programming languages present in the uploaded project.

### Dependency File Detector

Searches the extracted project for supported dependency management files.

### Dependency Extractor

Reads the detected dependency files and extracts package names and versions.

### Vulnerability Analyzer

Analyzes extracted dependencies for known security vulnerabilities and records their severity and CVSS information.

### License Analyzer

Identifies dependency licenses and evaluates their license risk.

### Risk Analyzer

Calculates dependency-level and project-level risk scores using the analysis results.

### Report Generator

Generates JSON, HTML, and PDF reports containing the complete analysis results.

### Web Interface

Provides the user interface through which users upload projects and view the generated analysis results.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and analysis logic |
| Flask | Web application framework |
| HTML | Web page structure |
| CSS | User interface styling |
| JavaScript | Client-side interaction |
| MySQL | Planned/future data persistence |
| JSON | Structured scan/report data |
| ReportLab | PDF report generation |
| Git | Version control |
| GitHub | Source code management |

---

## 📂 Project Structure

The project follows a modular structure similar to:

```text
CodeGuardian/
│
├── app.py
│
├── analyzers/
│   ├── dependency_detector.py
│   ├── vulnerability_analyzer.py
│   ├── license_analyzer.py
│   └── risk_analyzer.py
│
├── reports/
│   └── report_generator.py
│
├── templates/
│   └── scan_result.html
│
├──
