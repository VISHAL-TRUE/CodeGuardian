import os


# ============================================================
# PROGRAMMING LANGUAGE DETECTION
# ============================================================

LANGUAGE_EXTENSIONS = {
    ".py": "Python",

    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",

    ".ts": "TypeScript",
    ".tsx": "TypeScript",

    ".java": "Java",

    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",

    ".cs": "C#",

    ".go": "Go",

    ".rs": "Rust",

    ".php": "PHP",

    ".rb": "Ruby",

    ".kt": "Kotlin",
    ".kts": "Kotlin",

    ".swift": "Swift",

    ".dart": "Dart",

    ".scala": "Scala",

    ".lua": "Lua",

    ".r": "R",
}


# ============================================================
# DEPENDENCY MANIFEST / LOCK FILE DETECTION
# ============================================================

DEPENDENCY_FILES = {

    # Python
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "Pipfile": "Python",
    "Pipfile.lock": "Python",

    # JavaScript / Node.js
    "package.json": "JavaScript/Node.js",
    "package-lock.json": "JavaScript/Node.js",
    "yarn.lock": "JavaScript/Node.js",
    "pnpm-lock.yaml": "JavaScript/Node.js",

    # Java / Kotlin
    "pom.xml": "Java/Maven",
    "build.gradle": "Java/Gradle",
    "build.gradle.kts": "Kotlin/Gradle",

    # Rust
    "Cargo.toml": "Rust",
    "Cargo.lock": "Rust",

    # Go
    "go.mod": "Go",
    "go.sum": "Go",

    # PHP
    "composer.json": "PHP",

    # Ruby
    "Gemfile": "Ruby",
    "Gemfile.lock": "Ruby",

    # C#
    "packages.config": "C#",
}


# ============================================================
# MANIFEST → LANGUAGE MAPPING
# ============================================================

MANIFEST_LANGUAGES = {

    # Python
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "Pipfile": "Python",
    "Pipfile.lock": "Python",

    # JavaScript
    "package.json": "JavaScript",
    "package-lock.json": "JavaScript",
    "yarn.lock": "JavaScript",
    "pnpm-lock.yaml": "JavaScript",

    # Java
    "pom.xml": "Java",
    "build.gradle": "Java",

    # Kotlin
    "build.gradle.kts": "Kotlin",

    # Rust
    "Cargo.toml": "Rust",
    "Cargo.lock": "Rust",

    # Go
    "go.mod": "Go",
    "go.sum": "Go",

    # PHP
    "composer.json": "PHP",

    # Ruby
    "Gemfile": "Ruby",
    "Gemfile.lock": "Ruby",

    # C#
    "packages.config": "C#",
}


# ============================================================
# DIRECTORIES TO IGNORE
# ============================================================

IGNORED_DIRECTORIES = {
    ".git",
    ".svn",
    ".hg",

    "node_modules",

    "venv",
    ".venv",
    "env",
    ".env",

    "__pycache__",

    "target",
    "dist",
    "build",

    ".idea",
    ".vscode",

    "bin",
    "obj",

    "vendor",
}


# ============================================================
# PROJECT DETECTOR
# ============================================================

def detect_project(project_path):

    languages = set()

    dependency_files = []

    for root, directories, files in os.walk(project_path):

        # Ignore generated / unnecessary directories
        directories[:] = [
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES
        ]

        for file in files:

            # ------------------------------------------------
            # Detect programming language from file extension
            # ------------------------------------------------

            extension = os.path.splitext(file)[1].lower()

            if extension in LANGUAGE_EXTENSIONS:

                languages.add(
                    LANGUAGE_EXTENSIONS[extension]
                )

            # ------------------------------------------------
            # Detect dependency manifest
            # ------------------------------------------------

            if file in DEPENDENCY_FILES:

                dependency_files.append({

                    "file": file,

                    "ecosystem": DEPENDENCY_FILES[file],

                    "path": os.path.join(
                        root,
                        file
                    )
                })

                # ------------------------------------------------
                # Infer language from dependency manifest
                # ------------------------------------------------

                if file in MANIFEST_LANGUAGES:

                    languages.add(
                        MANIFEST_LANGUAGES[file]
                    )

    return {

        "languages": sorted(languages),

        "dependency_files": dependency_files
    }