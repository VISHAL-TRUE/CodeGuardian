from project_detector import detect_project


project_path = "extracted_projects"

result = detect_project(project_path)

print("\nDetected Languages:")
for language in result["languages"]:
    print("-", language)


print("\nDetected Dependency Files:")

for dependency in result["dependency_files"]:
    print(
        "-",
        dependency["file"],
        "|",
        dependency["ecosystem"]
    )