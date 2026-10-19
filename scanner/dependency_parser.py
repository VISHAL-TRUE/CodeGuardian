import os
import json
import re
import xml.etree.ElementTree as ET


# ============================================================
# PYTHON - requirements.txt
# ============================================================

def parse_requirements(file_path):

    dependencies = []

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            # Ignore comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Ignore editable/local installs for now
            if line.startswith("-"):
                continue

            # Remove inline comments
            line = line.split("#")[0].strip()

            match = re.match(
                r"^([A-Za-z0-9_.-]+)\s*([<>=!~]+)?\s*([A-Za-z0-9.*+!\-]+)?",
                line
            )

            if match:

                name = match.group(1)

                operator = match.group(2) or ""

                version = match.group(3) or "unknown"

                dependencies.append({

                    "name": name,

                    "version": (
                        operator + version
                        if operator
                        else version
                    ),

                    "ecosystem": "Python",

                    "language": "Python",

                    "manifest_file": os.path.basename(
                        file_path
                    ),

                    "project_path": file_path
                })

    return dependencies


# ============================================================
# JAVASCRIPT / NODE.JS - package.json
# ============================================================

def parse_package_json(file_path):

    dependencies = []

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    sections = [
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies"
    ]

    for section in sections:

        packages = data.get(
            section,
            {}
        )

        for name, version in packages.items():

            dependencies.append({

                "name": name,

                "version": version,

                "ecosystem": "JavaScript/Node.js",

                "language": "JavaScript",

                "manifest_file": os.path.basename(
                    file_path
                ),

                "project_path": file_path
            })

    return dependencies


# ============================================================
# GO - go.mod
# ============================================================

def parse_go_mod(file_path):

    dependencies = []

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()

    inside_require_block = False

    for line in content.splitlines():

        line = line.strip()

        # Start require block
        if line.startswith("require ("):

            inside_require_block = True

            continue

        # End require block
        if inside_require_block and line == ")":

            inside_require_block = False

            continue

        # Dependency inside require block
        if inside_require_block:

            parts = line.split()

            if len(parts) >= 2:

                # Ignore comments
                if parts[0].startswith("//"):
                    continue

                dependencies.append({

                    "name": parts[0],

                    "version": parts[1],

                    "ecosystem": "Go",

                    "language": "Go",

                    "manifest_file": os.path.basename(
                        file_path
                    ),

                    "project_path": file_path
                })

        # Single-line require
        elif line.startswith("require "):

            parts = line.split()

            if len(parts) >= 3:

                dependencies.append({

                    "name": parts[1],

                    "version": parts[2],

                    "ecosystem": "Go",

                    "language": "Go",

                    "manifest_file": os.path.basename(
                        file_path
                    ),

                    "project_path": file_path
                })

    return dependencies


# ============================================================
# RUST - Cargo.toml
# ============================================================

def parse_cargo_toml(file_path):

    dependencies = []

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()

    in_dependencies = False

    for line in content.splitlines():

        line = line.strip()

        # Enter [dependencies]
        if line == "[dependencies]":

            in_dependencies = True

            continue

        # Leave [dependencies]
        if line.startswith("["):

            in_dependencies = False

        if in_dependencies and "=" in line:

            name, value = line.split(
                "=",
                1
            )

            name = name.strip()

            value = value.strip()

            # Example:
            # serde = "1.0"

            if value.startswith('"'):

                version = value.strip('"')

            # Example:
            # serde = { version = "1.0", features = ["derive"] }

            elif value.startswith("{"):

                version_match = re.search(
                    r'version\s*=\s*"([^"]+)"',
                    value
                )

                if version_match:

                    version = version_match.group(1)

                else:

                    version = "unknown"

            else:

                version = value

            dependencies.append({

                "name": name,

                "version": version,

                "ecosystem": "Rust",

                "language": "Rust",

                "manifest_file": os.path.basename(
                    file_path
                ),

                "project_path": file_path
            })

    return dependencies


# ============================================================
# JAVA - pom.xml
# ============================================================

def parse_pom_xml(file_path):

    dependencies = []

    try:

        tree = ET.parse(file_path)

        root = tree.getroot()

    except ET.ParseError:

        return dependencies

    # Maven XML can use namespaces
    namespace = ""

    if root.tag.startswith("{"):

        namespace = root.tag.split("}")[0] + "}"

    dependencies_element = root.find(
        f"{namespace}dependencies"
    )

    if dependencies_element is None:

        return dependencies

    for dependency in dependencies_element.findall(
        f"{namespace}dependency"
    ):

        group_id = dependency.find(
            f"{namespace}groupId"
        )

        artifact_id = dependency.find(
            f"{namespace}artifactId"
        )

        version = dependency.find(
            f"{namespace}version"
        )

        if artifact_id is None:

            continue

        group = (
            group_id.text.strip()
            if group_id is not None and group_id.text
            else "unknown"
        )

        artifact = (
            artifact_id.text.strip()
            if artifact_id.text
            else "unknown"
        )

        dependency_version = (
            version.text.strip()
            if version is not None and version.text
            else "unknown"
        )

        # Standard Maven coordinate
        dependency_name = (
            group + ":" + artifact
        )

        dependencies.append({

            "name": dependency_name,

            "version": dependency_version,

            "ecosystem": "Java/Maven",

            "language": "Java",

            "manifest_file": os.path.basename(
                file_path
            ),

            "project_path": file_path
        })

    return dependencies


# ============================================================
# SELECT PARSER
# ============================================================

def parse_dependency_file(dependency_file):

    file_name = dependency_file["file"]

    file_path = dependency_file["path"]

    # Python
    if file_name == "requirements.txt":

        return parse_requirements(
            file_path
        )

    # JavaScript / Node.js
    elif file_name == "package.json":

        return parse_package_json(
            file_path
        )

    # Go
    elif file_name == "go.mod":

        return parse_go_mod(
            file_path
        )

    # Rust
    elif file_name == "Cargo.toml":

        return parse_cargo_toml(
            file_path
        )

    # Java / Maven
    elif file_name == "pom.xml":

        return parse_pom_xml(
            file_path
        )

    return []


# ============================================================
# EXTRACT ALL DEPENDENCIES
# ============================================================

def extract_all_dependencies(
    dependency_files
):

    all_dependencies = []

    for dependency_file in dependency_files:

        dependencies = parse_dependency_file(
            dependency_file
        )

        all_dependencies.extend(
            dependencies
        )

    return all_dependencies