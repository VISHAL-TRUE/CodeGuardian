import json
import urllib.request
import urllib.error
import urllib.parse
import re


DEPS_DEV_API = "https://api.deps.dev/v3alpha/systems/"
PYPI_API = "https://pypi.org/pypi/"
CRATES_API = "https://crates.io/api/v1/crates/"
NPM_API = "https://registry.npmjs.org/"
GO_PROXY_API = "https://proxy.golang.org/"


# =========================================================
# GENERAL HTTP REQUEST
# =========================================================

def get_json(url):

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "CodeGuardian/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            data = response.read().decode("utf-8")

            return json.loads(data)

    except Exception:
        return None


# =========================================================
# LICENSE NORMALIZATION
# =========================================================

def normalize_license(license_name):

    if not license_name:
        return None

    license_name = str(
        license_name
    ).strip()

    upper = license_name.upper()

    # Combined licenses
    if "MIT" in upper and "APACHE" in upper:
        return "MIT OR Apache-2.0"

    # MIT
    if upper in [
        "MIT",
        "MIT LICENSE"
    ]:
        return "MIT"

    # Apache
    if "APACHE" in upper:
        return "Apache-2.0"

    # BSD
    if "BSD-3" in upper:
        return "BSD-3-Clause"

    if "BSD-2" in upper:
        return "BSD-2-Clause"

    if upper == "BSD":
        return "BSD"

    if upper == "BSD LICENSE":
        return "BSD-3-Clause"

    # GPL
    if "AGPL-3" in upper:
        return "AGPL-3.0"

    if "GPL-3" in upper:
        return "GPL-3.0"

    if "GPL-2" in upper:
        return "GPL-2.0"

    # LGPL
    if "LGPL-3" in upper:
        return "LGPL-3.0"

    if "LGPL-2" in upper:
        return "LGPL-2.0"

    # Other common licenses
    if "MPL-2" in upper:
        return "MPL-2.0"

    if "ISC" in upper:
        return "ISC"

    if "UNLICENSE" in upper:
        return "Unlicense"

    if "CC0" in upper:
        return "CC0-1.0"

    if "EPL-2" in upper:
        return "EPL-2.0"

    return license_name


# =========================================================
# COMBINE LICENSES
# =========================================================

def combine_licenses(licenses):

    if not licenses:
        return None

    normalized = []

    for license_name in licenses:

        normalized_license = normalize_license(
            license_name
        )

        if (
            normalized_license
            and normalized_license not in normalized
        ):
            normalized.append(
                normalized_license
            )

    if not normalized:
        return None

    if len(normalized) == 1:
        return normalized[0]

    return " OR ".join(normalized)


# =========================================================
# LICENSE CLASSIFICATION
# =========================================================

def classify_license(license_name):

    if not license_name:
        return {
            "classification": "Other",
            "risk": "UNKNOWN"
        }

    upper = license_name.upper()

    # Strong copyleft must be checked before generic GPL
    if (
        "AGPL" in upper
        or "GPL" in upper
    ):
        return {
            "classification": "Strong Copyleft",
            "risk": "HIGH"
        }

    # Weak copyleft
    if (
        "LGPL" in upper
        or "MPL" in upper
        or "EPL" in upper
    ):
        return {
            "classification": "Weak Copyleft",
            "risk": "MEDIUM"
        }

    # Permissive
    if (
        "MIT" in upper
        or "APACHE" in upper
        or "BSD" in upper
        or "ISC" in upper
        or "UNLICENSE" in upper
        or "CC0" in upper
    ):
        return {
            "classification": "Permissive",
            "risk": "LOW"
        }

    return {
        "classification": "Other",
        "risk": "UNKNOWN"
    }


# =========================================================
# PYPI
# =========================================================

def get_license_from_pypi(
    package_name,
    version
):

    clean_version = str(
        version
    ).replace(
        "==",
        ""
    ).strip()

    url = (
        PYPI_API
        + package_name
        + "/"
        + clean_version
        + "/json"
    )

    data = get_json(url)

    if not data:
        return None

    info = data.get(
        "info",
        {}
    )

    license_name = info.get(
        "license"
    )

    if license_name:
        return normalize_license(
            license_name
        )

    classifiers = info.get(
        "classifiers",
        []
    )

    licenses = []

    for classifier in classifiers:

        if classifier.startswith(
            "License ::"
        ):

            parts = classifier.split(
                "::"
            )

            if len(parts) >= 3:

                licenses.append(
                    parts[-1].strip()
                )

    return combine_licenses(
        licenses
    )


# =========================================================
# CRATES.IO
# =========================================================

def get_license_from_crates(
    package_name,
    version
):

    clean_version = str(
        version
    ).strip()

    # Resolve shorthand such as 1.0
    if re.match(
        r"^\d+\.\d+$",
        clean_version
    ):

        crate_data = get_json(
            CRATES_API
            + package_name
        )

        if crate_data:

            versions = crate_data.get(
                "versions",
                []
            )

            for item in versions:

                crate_version = item.get(
                    "num",
                    ""
                )

                if crate_version.startswith(
                    clean_version + "."
                ):

                    clean_version = (
                        crate_version
                    )

                    break

    url = (
        CRATES_API
        + package_name
        + "/"
        + clean_version
    )

    data = get_json(url)

    if not data:
        return None

    version_data = data.get(
        "version",
        {}
    )

    license_name = version_data.get(
        "license"
    )

    if license_name:
        return normalize_license(
            license_name
        )

    return None


# =========================================================
# NPM
# =========================================================

def get_license_from_npm(
    package_name,
    version
):

    clean_version = str(
        version
    ).strip()

    url = (
        NPM_API
        + package_name
        + "/"
        + clean_version
    )

    data = get_json(url)

    if not data:
        return None

    license_name = data.get(
        "license"
    )

    if isinstance(
        license_name,
        dict
    ):

        license_name = license_name.get(
            "type"
        )

    if isinstance(
        license_name,
        str
    ):

        return normalize_license(
            license_name
        )

    return None


# =========================================================
# GO LICENSE LOOKUP
# =========================================================

def get_license_from_go(
    package_name,
    version
):

    clean_version = str(
        version
    ).strip()

    if clean_version.startswith("v"):
        clean_version = clean_version[1:]

    # -----------------------------------------------------
    # First try deps.dev
    # -----------------------------------------------------

    encoded_package = urllib.parse.quote(
        package_name,
        safe=""
    )

    deps_url = (
        DEPS_DEV_API
        + "GO/"
        + encoded_package
        + "/versions/"
        + clean_version
    )

    data = get_json(
        deps_url
    )

    if data:

        version_data = data.get(
            "version",
            {}
        )

        licenses = version_data.get(
            "licenses",
            []
        )

        detected_licenses = []

        if isinstance(
            licenses,
            list
        ):

            for item in licenses:

                if isinstance(
                    item,
                    str
                ):

                    detected_licenses.append(
                        item
                    )

                elif isinstance(
                    item,
                    dict
                ):

                    name = item.get(
                        "name"
                    )

                    if name:
                        detected_licenses.append(
                            name
                        )

                    types = item.get(
                        "types",
                        []
                    )

                    if isinstance(
                        types,
                        list
                    ):

                        for license_type in types:

                            if isinstance(
                                license_type,
                                str
                            ):

                                detected_licenses.append(
                                    license_type
                                )

        result = combine_licenses(
            detected_licenses
        )

        if result:
            return result

    # -----------------------------------------------------
    # Second approach:
    # Go module ZIP/source metadata through
    # proxy.golang.org
    # -----------------------------------------------------

    module_path = package_name

    # Escape module path for Go proxy
    escaped_module = module_path.replace(
        "!",
        "! "
    ).replace(
        " ",
        ""
    )

    info_url = (
        GO_PROXY_API
        + escaped_module
        + "/@v/v"
        + clean_version
        + ".info"
    )

    info_data = get_json(
        info_url
    )

    # The Go proxy itself does not directly provide
    # a license field. Therefore, this is intentionally
    # not treated as a license result.
    #
    # We continue to a GitHub-based lookup for the
    # common GitHub Go modules.

    # -----------------------------------------------------
    # GitHub source lookup
    # -----------------------------------------------------

    if package_name.startswith(
        "github.com/"
    ):

        parts = package_name.split("/")

        if len(parts) >= 3:

            owner = parts[1]
            repository = parts[2]

            license_url = (
                "https://api.github.com/repos/"
                + owner
                + "/"
                + repository
                + "/license"
            )

            github_data = get_json(
                license_url
            )

            if github_data:

                license_info = github_data.get(
                    "license"
                )

                if isinstance(
                    license_info,
                    dict
                ):

                    spdx_id = license_info.get(
                        "spdx_id"
                    )

                    if spdx_id:
                        return normalize_license(
                            spdx_id
                        )

                    license_name = license_info.get(
                        "name"
                    )

                    if license_name:
                        return normalize_license(
                            license_name
                        )

    return None


# =========================================================
# MAVEN
# =========================================================

def get_license_from_maven(
    package_name,
    version
):

    if ":" not in package_name:
        return None

    group_id, artifact_id = (
        package_name.split(
            ":",
            1
        )
    )

    encoded_package = urllib.parse.quote(
        group_id + ":" + artifact_id,
        safe=""
    )

    url = (
        DEPS_DEV_API
        + "MAVEN/"
        + encoded_package
        + "/versions/"
        + version
    )

    data = get_json(url)

    if not data:
        return None

    version_data = data.get(
        "version",
        {}
    )

    licenses = version_data.get(
        "licenses",
        []
    )

    detected_licenses = []

    if isinstance(
        licenses,
        list
    ):

        for item in licenses:

            if isinstance(
                item,
                str
            ):

                detected_licenses.append(
                    item
                )

            elif isinstance(
                item,
                dict
            ):

                name = item.get(
                    "name"
                )

                if name:
                    detected_licenses.append(
                        name
                    )

    return combine_licenses(
        detected_licenses
    )


# =========================================================
# DEPS.DEV COMMON LOOKUP
# =========================================================

def get_license_from_deps_dev(
    ecosystem,
    package_name,
    version
):

    ecosystem_mapping = {

        "Python":
            "PYPI",

        "JavaScript/Node.js":
            "NPM",

        "Rust":
            "CARGO",

        "Go":
            "GO",

        "Java/Maven":
            "MAVEN",

        "Ruby":
            "RUBYGEMS",

        "C#":
            "NUGET",

        "PHP":
            "PACKAGIST"
    }

    system = ecosystem_mapping.get(
        ecosystem
    )

    if not system:
        return None

    encoded_package = urllib.parse.quote(
        package_name,
        safe=""
    )

    url = (
        DEPS_DEV_API
        + system
        + "/"
        + encoded_package
        + "/versions/"
        + version
    )

    data = get_json(url)

    if not data:
        return None

    version_data = data.get(
        "version",
        {}
    )

    licenses = version_data.get(
        "licenses",
        []
    )

    detected_licenses = []

    if isinstance(
        licenses,
        list
    ):

        for item in licenses:

            if isinstance(
                item,
                str
            ):

                detected_licenses.append(
                    item
                )

            elif isinstance(
                item,
                dict
            ):

                name = item.get(
                    "name"
                )

                if name:
                    detected_licenses.append(
                        name
                    )

                types = item.get(
                    "types",
                    []
                )

                if isinstance(
                    types,
                    list
                ):

                    for license_type in types:

                        if isinstance(
                            license_type,
                            str
                        ):

                            detected_licenses.append(
                                license_type
                            )

    return combine_licenses(
        detected_licenses
    )


# =========================================================
# MAIN LICENSE LOOKUP
# =========================================================

def get_license(
    dependency
):

    name = dependency.get(
        "name"
    )

    version = dependency.get(
        "version"
    )

    ecosystem = dependency.get(
        "ecosystem"
    )

    if not name or not version:
        return None

    clean_version = str(
        version
    ).strip()

    clean_version = clean_version.replace(
        "==",
        ""
    )

    # -----------------------------------------------------
    # Python
    # -----------------------------------------------------

    if ecosystem == "Python":

        result = get_license_from_pypi(
            name,
            clean_version
        )

        if result:
            return result

    # -----------------------------------------------------
    # JavaScript
    # -----------------------------------------------------

    elif ecosystem == "JavaScript/Node.js":

        result = get_license_from_npm(
            name,
            clean_version
        )

        if result:
            return result

    # -----------------------------------------------------
    # Rust
    # -----------------------------------------------------

    elif ecosystem == "Rust":

        result = get_license_from_crates(
            name,
            clean_version
        )

        if result:
            return result

    # -----------------------------------------------------
    # Go
    # -----------------------------------------------------

    elif ecosystem == "Go":

        result = get_license_from_go(
            name,
            clean_version
        )

        if result:
            return result

    # -----------------------------------------------------
    # Java / Maven
    # -----------------------------------------------------

    elif ecosystem == "Java/Maven":

        result = get_license_from_maven(
            name,
            clean_version
        )

        if result:
            return result

    # -----------------------------------------------------
    # Common fallback
    # -----------------------------------------------------

    result = get_license_from_deps_dev(
        ecosystem,
        name,
        clean_version
    )

    if result:
        return result

    return None


# =========================================================
# ANALYZE ONE DEPENDENCY
# =========================================================

def analyze_license(
    dependency
):

    license_name = get_license(
        dependency
    )

    classification = classify_license(
        license_name
    )

    return {

        "name":
            dependency.get(
                "name",
                "Unknown"
            ),

        "version":
            dependency.get(
                "version",
                "Unknown"
            ),

        "ecosystem":
            dependency.get(
                "ecosystem",
                "Unknown"
            ),

        "manifest_file":
            dependency.get(
                "manifest_file",
                "Unknown"
            ),

        "license":
            license_name
            if license_name
            else "Unknown",

        "classification":
            classification[
                "classification"
            ],

        "risk":
            classification[
                "risk"
            ]
    }


# =========================================================
# ANALYZE ALL DEPENDENCIES
# =========================================================

def analyze_licenses(
    dependencies
):

    results = []

    for dependency in dependencies:

        result = analyze_license(
            dependency
        )

        results.append(
            result
        )

    return results