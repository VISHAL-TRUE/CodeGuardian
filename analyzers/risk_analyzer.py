# =========================================================

# CodeGuardian - Risk Calculation Engine

# =========================================================

# ---------------------------------------------------------

# RISK WEIGHTS

# ---------------------------------------------------------

VULNERABILITY_WEIGHTS = {

    "CRITICAL": 10,

    "HIGH": 7,

    "MEDIUM": 4,

    "LOW": 1,

    "UNKNOWN": 0

}

LICENSE_WEIGHTS = {

    "HIGH": 7,

    "MEDIUM": 4,

    "LOW": 1,

    "UNKNOWN": 0

}

# Percentage contribution

VULNERABILITY_WEIGHT = 0.70

LICENSE_WEIGHT = 0.30

# ---------------------------------------------------------

# CALCULATE VULNERABILITY SCORE

# ---------------------------------------------------------

def calculate_vulnerability_score(

    vulnerability_result

):

    vulnerabilities = vulnerability_result.get(

        "vulnerabilities",

        []

    )

    if not vulnerabilities:

        return {

            "score": 0,

            "highest_severity": "NONE",

            "known_vulnerabilities": 0,

            "unknown_vulnerabilities": 0

        }

    highest_score = 0

    highest_severity = "NONE"

    known_count = 0

    unknown_count = 0

    for vulnerability in vulnerabilities:

        severity = str(

            vulnerability.get(

                "severity",

                "UNKNOWN"

            )

        ).upper()

        score = VULNERABILITY_WEIGHTS.get(

            severity,

            0

        )

        if severity == "UNKNOWN":

            unknown_count += 1

        else:

            known_count += 1

        if score > highest_score:

            highest_score = score

            highest_severity = severity

    return {

        "score": highest_score,

        "highest_severity": highest_severity,

        "known_vulnerabilities": known_count,

        "unknown_vulnerabilities": unknown_count

    }

# ---------------------------------------------------------

# CALCULATE LICENSE SCORE

# ---------------------------------------------------------

def calculate_license_score(

    license_result

):

    license_risk = str(

        license_result.get(

            "risk",

            "UNKNOWN"

        )

    ).upper()

    score = LICENSE_WEIGHTS.get(

        license_risk,

        0

    )

    return {

        "score": score,

        "license_risk": license_risk

    }

# ---------------------------------------------------------

# CALCULATE INDIVIDUAL DEPENDENCY RISK

# ---------------------------------------------------------

def calculate_dependency_risk(

    vulnerability_result,

    license_result

):

    scan_status = str(

        vulnerability_result.get("status", "scanned")

    ).lower()

    if scan_status != "scanned":

        return {

            "name": vulnerability_result.get(

                "name", "Unknown"

            ),

            "version": vulnerability_result.get(

                "version", "Unknown"

            ),

            "ecosystem": vulnerability_result.get(

                "ecosystem", "Unknown"

            ),

            "vulnerability_score": None,

            "license_score": None,

            "risk_score": None,

            "risk_level": "NOT ASSESSED",

            "highest_vulnerability_severity": "UNKNOWN",

            "known_vulnerabilities": 0,

            "unknown_vulnerabilities": 0,

            "license": license_result.get(

                "license", "Unknown"

            ),

            "license_risk": license_result.get(

                "risk", "UNKNOWN"

            ),

            "scan_status": scan_status,

            "scan_reason": vulnerability_result.get(

                "reason",

                vulnerability_result.get(

                    "message",

                    "Vulnerability scan was not completed."

                )

            )

        }

    vulnerability_data = (

        calculate_vulnerability_score(

            vulnerability_result

        )

    )

    license_data = (

        calculate_license_score(

            license_result

        )

    )

    vulnerability_score = (

        vulnerability_data["score"]

    )

    license_score = (

        license_data["score"]

    )

    # -----------------------------------------------------

    # Weighted risk calculation

    #

    # Vulnerability = 70%

    # License = 30%

    # -----------------------------------------------------

    raw_score = (

        (

            vulnerability_score

            * VULNERABILITY_WEIGHT

        )

        +

        (

            license_score

            * LICENSE_WEIGHT

        )

    )

    # Maximum possible raw score:

    #

    # Vulnerability = 10

    # License = 7

    #

    # Maximum = 10(0.70) + 7(0.30)

    #         = 9.1

    #

    # Normalize to 0 - 10.

    maximum_possible_score = (

        (

            10

            * VULNERABILITY_WEIGHT

        )

        +

        (

            7

            * LICENSE_WEIGHT

        )

    )

    if maximum_possible_score > 0:

        normalized_score = (

            raw_score

            / maximum_possible_score

        ) * 10

    else:

        normalized_score = 0

    normalized_score = round(

        normalized_score,

        2

    )

    risk_level = determine_risk_level(

        normalized_score

    )

    return {

        "name":

            vulnerability_result.get(

                "name",

                license_result.get(

                    "name",

                    "Unknown"

                )

            ),

        "version":

            vulnerability_result.get(

                "version",

                license_result.get(

                    "version",

                    "Unknown"

                )

            ),

        "ecosystem":

            vulnerability_result.get(

                "ecosystem",

                license_result.get(

                    "ecosystem",

                    "Unknown"

                )

            ),

        "vulnerability_score":

            vulnerability_score,

        "license_score":

            license_score,

        "risk_score":

            normalized_score,

        "risk_level":

            risk_level,

        "highest_vulnerability_severity":

            vulnerability_data[

                "highest_severity"

            ],

        "known_vulnerabilities":

            vulnerability_data[

                "known_vulnerabilities"

            ],

        "unknown_vulnerabilities":

            vulnerability_data[

                "unknown_vulnerabilities"

            ],

        "license":

            license_result.get(

                "license",

                "Unknown"

            ),

        "license_risk":

            license_data[

                "license_risk"

            ]

    }

# ---------------------------------------------------------

# DETERMINE INDIVIDUAL RISK LEVEL

# ---------------------------------------------------------

def determine_risk_level(

    score

):

    if score >= 8:

        return "CRITICAL"

    elif score >= 6:

        return "HIGH"

    elif score >= 3:

        return "MEDIUM"

    else:

        return "LOW"

# ---------------------------------------------------------

# CALCULATE PROJECT RISK

# ---------------------------------------------------------

def calculate_project_risk(

    risk_results

):

    if not risk_results:

        return {

            "project_score": 0,

            "project_risk": "LOW",

            "total_dependencies": 0,

            "assessed_dependencies": 0,

            "unassessed_dependencies": 0,

            "critical_dependencies": 0,

            "high_dependencies": 0,

            "medium_dependencies": 0,

            "low_dependencies": 0,

            "total_vulnerabilities": 0,

            "unknown_vulnerabilities": 0,

            "highest_dependency_score": 0,

            "highest_dependency": "None"

        }

    # -----------------------------------------------------

    # Dependency counters

    # -----------------------------------------------------

    critical_count = 0

    high_count = 0

    medium_count = 0

    low_count = 0

    total_vulnerabilities = 0

    unknown_vulnerabilities = 0

    # -----------------------------------------------------

    # Find highest-risk dependency

    # -----------------------------------------------------

    highest_dependency_score = 0

    highest_dependency = "None"

    for result in risk_results:

        risk_score = result.get("risk_score")

        risk_level = result.get("risk_level", "LOW")

        # Count vulnerabilities for every dependency.

        total_vulnerabilities += result.get(

            "known_vulnerabilities", 0

        )

        total_vulnerabilities += result.get(

            "unknown_vulnerabilities", 0

        )

        unknown_vulnerabilities += result.get(

            "unknown_vulnerabilities", 0

        )

        # Do not treat unassessed dependencies as LOW risk.

        if risk_score is None or risk_level == "NOT ASSESSED":

            continue

        if risk_level == "CRITICAL":

            critical_count += 1

        elif risk_level == "HIGH":

            high_count += 1

        elif risk_level == "MEDIUM":

            medium_count += 1

        elif risk_level == "LOW":

            low_count += 1

        if risk_score > highest_dependency_score:

            highest_dependency_score = risk_score

            highest_dependency = result.get(

                "name", "Unknown"

            )

    # -----------------------------------------------------

    # Project Risk Strategy

    # -----------------------------------------------------

    #

    # The project risk is based on the highest-risk

    # dependency rather than a simple average.

    #

    # This prevents safe dependencies from hiding

    # serious vulnerabilities.

    #

    # Example:

    #

    # Dependency 1 = LOW

    # Dependency 2 = LOW

    # Dependency 3 = HIGH

    #

    # Project risk = HIGH

    #

    # -----------------------------------------------------

    project_score = round(

        highest_dependency_score,

        2

    )

    project_risk = determine_risk_level(

        project_score

    )

    # -----------------------------------------------------

    # Total dependency count

    # -----------------------------------------------------

    total_dependencies = len(

        risk_results

    )

    # -----------------------------------------------------

    # Return complete project result

    # -----------------------------------------------------

    return {

        "project_score":

            project_score,

        "project_risk":

            project_risk,

        "total_dependencies":

            total_dependencies,

        "assessed_dependencies": sum(
            1 for item in risk_results
            if item.get("risk_score") is not None
            and item.get("risk_level") != "NOT ASSESSED"
        ),

        "unassessed_dependencies": sum(
            1 for item in risk_results
            if item.get("risk_score") is None
            or item.get("risk_level") == "NOT ASSESSED"
        ),

        "critical_dependencies":

            critical_count,

        "high_dependencies":

            high_count,

        "medium_dependencies":

            medium_count,

        "low_dependencies":

            low_count,

        "total_vulnerabilities":

            total_vulnerabilities,

        "unknown_vulnerabilities":

            unknown_vulnerabilities,

        "highest_dependency_score":

            highest_dependency_score,

        "highest_dependency":

            highest_dependency

    }

# ---------------------------------------------------------

# MAIN RISK ANALYSIS FUNCTION

# ---------------------------------------------------------

def analyze_risks(

    vulnerability_results,

    license_results

):

    risk_results = []

    # -----------------------------------------------------

    # Create license lookup

    # -----------------------------------------------------

    license_lookup = {}

    for license_result in license_results:

        key = (

            license_result.get(

                "name",

                ""

            ),

            license_result.get(

                "version",

                ""

            )

        )

        license_lookup[key] = (

            license_result

        )

    # -----------------------------------------------------

    # Calculate risk for every dependency

    # -----------------------------------------------------

    for vulnerability_result in (

        vulnerability_results

    ):

        key = (

            vulnerability_result.get(

                "name",

                ""

            ),

            vulnerability_result.get(

                "version",

                ""

            )

        )

        # Find corresponding license result

        license_result = (

            license_lookup.get(

                key,

                {

                    "name":

                        vulnerability_result.get(

                            "name",

                            "Unknown"

                        ),

                    "version":

                        vulnerability_result.get(

                            "version",

                            "Unknown"

                        ),

                    "ecosystem":

                        vulnerability_result.get(

                            "ecosystem",

                            "Unknown"

                        ),

                    "license":

                        "Unknown",

                    "risk":

                        "UNKNOWN"

                }

            )

        )

        # Calculate dependency risk

        risk_result = (

            calculate_dependency_risk(

                vulnerability_result,

                license_result

            )

        )

        risk_results.append(

            risk_result

        )

    # -----------------------------------------------------

    # Calculate overall project risk

    # -----------------------------------------------------

    project_result = (

        calculate_project_risk(

            risk_results

        )

    )

    return {

        "dependencies":

            risk_results,

        "project":

            project_result

    }
