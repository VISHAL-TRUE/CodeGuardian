import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from ai import recommendation_engine
from reports import report_generator
import app


class RecommendationEngineTests(unittest.TestCase):
    def setUp(self):
        self.vulnerabilities = [
            {
                "name": "risky-package",
                "version": "1.0.0",
                "ecosystem": "Python",
                "status": "scanned",
                "vulnerabilities": [
                    {
                        "id": "OSV-1",
                        "aliases": ["CVE-1"],
                        "severity": "HIGH",
                        "cvss_score": 7.5,
                        "summary": "A supplied vulnerability.",
                    },
                    {
                        "id": "OSV-2",
                        "severity": "MEDIUM",
                        "summary": "Another supplied vulnerability.",
                    },
                ],
            },
            {
                "name": "clean-package",
                "version": "2.0",
                "ecosystem": "Python",
                "status": "scanned",
                "vulnerabilities": [],
            },
            {
                "name": "range-package",
                "version": ">=1.0",
                "ecosystem": "Python",
                "status": "not_scanned",
                "reason": "Version is a range.",
                "vulnerabilities": [],
            },
        ]
        self.licenses = [
            {
                "name": "risky-package",
                "version": "1.0.0",
                "ecosystem": "Python",
                "license": "Unknown",
                "classification": "Other",
                "risk": "UNKNOWN",
            },
            {
                "name": "clean-package",
                "version": "2.0",
                "ecosystem": "Python",
                "license": "MIT",
                "classification": "Permissive",
                "risk": "LOW",
            },
            {
                "name": "range-package",
                "version": ">=1.0",
                "ecosystem": "Python",
                "license": "MIT",
                "classification": "Permissive",
                "risk": "LOW",
            },
        ]
        self.risks = [
            {
                "name": "risky-package",
                "version": "1.0.0",
                "ecosystem": "Python",
                "risk_level": "HIGH",
                "risk_score": 7.5,
                "license": "Unknown",
                "license_risk": "UNKNOWN",
                "known_vulnerabilities": 2,
                "highest_vulnerability_severity": "HIGH",
            },
            {
                "name": "clean-package",
                "version": "2.0",
                "ecosystem": "Python",
                "risk_level": "LOW",
                "risk_score": 0,
                "license": "MIT",
                "license_risk": "LOW",
            },
            {
                "name": "range-package",
                "version": ">=1.0",
                "ecosystem": "Python",
                "risk_level": "NOT ASSESSED",
                "risk_score": None,
                "license": "MIT",
                "license_risk": "LOW",
            },
        ]

    def test_only_actionable_findings_are_consolidated_without_api_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch.object(
            recommendation_engine, "get_gemini_client", return_value=None
        ) as get_client:
            recommendations = recommendation_engine.generate_recommendations(
                self.vulnerabilities,
                self.licenses,
                self.risks,
            )

        self.assertEqual(len(recommendations), 2)
        self.assertEqual(
            [item["dependency"] for item in recommendations],
            ["risky-package", "range-package"],
        )
        self.assertEqual(recommendations[0]["severity"], "HIGH")
        self.assertEqual(recommendations[0]["status"], "missing_api_key")
        self.assertIn("GEMINI_API_KEY", recommendations[0]["diagnostic"])
        self.assertIn("OSV-1", recommendations[0]["issue"])
        self.assertIn(
            "AI recommendation unavailable",
            recommendations[0]["recommendation"],
        )
        self.assertIn("Version not scanned", recommendations[1]["issue_type"])
        self.assertEqual(get_client.call_count, 0)

    def test_gemini_response_cannot_lower_detected_priority(self):
        response = {
            "problem": "Known supplied issue.",
            "why_it_matters": "It may affect users.",
            "recommendation": "Update after validating a supported release.",
            "developer_steps": ["Update the manifest."],
            "verification": "Rerun the scan.",
            "priority": "LOW",
        }
        models = unittest.mock.Mock()
        models.generate_content.return_value.text = json.dumps(response)
        client = unittest.mock.Mock(models=models)

        with patch.object(
            recommendation_engine, "get_gemini_client", return_value=client
        ), patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            result = recommendation_engine.generate_recommendation({
                "dependency": "risky-package",
                "version": "1.0.0",
                "ecosystem": "Python",
                "issue_types": ["Vulnerability"],
                "issue": "Vulnerability detected.",
                "severity": "CRITICAL",
                "findings": [{"id": "OSV-1"}],
            })

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["priority"], "CRITICAL")
        models.generate_content.assert_called_once()
        self.assertEqual(
            models.generate_content.call_args.kwargs["model"],
            recommendation_engine.GEMINI_MODEL,
        )
        self.assertEqual(
            models.generate_content.call_args.kwargs["config"][
                "response_mime_type"
            ],
            "application/json",
        )

    def test_temporary_model_error_uses_fallback_model(self):
        response = {
            "problem": "A supplied issue.",
            "why_it_matters": "It may affect security.",
            "recommendation": "Review and update the dependency.",
            "developer_steps": ["Update the manifest."],
            "verification": "Rerun the scan.",
            "priority": "HIGH",
        }
        unavailable_error = type(
            "UnavailableError",
            (Exception,),
            {"code": 503},
        )("temporarily unavailable")
        models = unittest.mock.Mock()
        models.generate_content.side_effect = [
            unavailable_error,
            unittest.mock.Mock(text=json.dumps(response)),
        ]
        client = unittest.mock.Mock(models=models)

        with patch.object(
            recommendation_engine, "get_gemini_client", return_value=client
        ), patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            result = recommendation_engine.generate_recommendation({
                "dependency": "risky-package",
                "version": "1.0.0",
                "ecosystem": "Python",
                "issue_types": ["Vulnerability"],
                "issue": "Vulnerability detected.",
                "severity": "HIGH",
                "findings": [{"id": "OSV-1"}],
            })

        self.assertEqual(result["status"], "success")
        self.assertEqual(models.generate_content.call_count, 2)
        self.assertEqual(
            models.generate_content.call_args_list[1].kwargs["model"],
            recommendation_engine.GEMINI_FALLBACK_MODELS[0],
        )

    def test_client_reads_key_from_process_environment(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-key"}), patch(
            "google.genai.Client"
        ) as client_factory:
            recommendation_engine.get_gemini_client()

        self.assertEqual(
            client_factory.call_args.kwargs["api_key"],
            "private-test-key",
        )
        self.assertEqual(
            client_factory.call_args.kwargs["http_options"]["timeout"],
            15000,
        )
        self.assertEqual(
            client_factory.call_args.kwargs["http_options"]["retry_options"][
                "attempts"
            ],
            1,
        )

    def test_api_error_diagnostic_does_not_expose_secret(self):
        unauthorized_error = type(
            "UnauthorizedError",
            (Exception,),
            {"code": 401},
        )("request failed")
        unauthorized_error.message = (
            "API key not valid. Provided key: private-test-key"
        )
        models = unittest.mock.Mock()
        models.generate_content.side_effect = unauthorized_error
        client = unittest.mock.Mock(models=models)

        with patch.object(
            recommendation_engine, "get_gemini_client", return_value=client
        ), patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-key"}):
            result = recommendation_engine.generate_recommendation({
                "dependency": "risky-package",
                "version": "1.0.0",
                "ecosystem": "Python",
                "issue_types": ["Vulnerability"],
                "issue": "Vulnerability detected.",
                "severity": "HIGH",
                "findings": [{"id": "OSV-1"}],
            })

        self.assertEqual(result["status"], "error")
        self.assertIn("rejected the credentials", result["diagnostic"])
        self.assertIn("API key not valid", result["diagnostic"])
        self.assertIn("[redacted]", result["diagnostic"])
        self.assertNotIn("private-test-key", result["diagnostic"])

    def test_scan_stops_repeating_calls_after_authentication_failure(self):
        unauthorized_error = type(
            "UnauthorizedError",
            (Exception,),
            {"code": 401, "message": "API key not valid"},
        )("request failed")
        client = unittest.mock.Mock()
        client.models.generate_content.side_effect = unauthorized_error

        with patch.object(
            recommendation_engine, "get_gemini_client", return_value=client
        ), patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            recommendations = recommendation_engine.generate_recommendations(
                [
                    {
                        "name": "first-package",
                        "version": "1.0",
                        "ecosystem": "Python",
                        "status": "not_scanned",
                        "vulnerabilities": [],
                    },
                    {
                        "name": "second-package",
                        "version": "2.0",
                        "ecosystem": "Python",
                        "status": "not_scanned",
                        "vulnerabilities": [],
                    },
                ],
                [],
                [],
            )

        self.assertEqual(client.models.generate_content.call_count, 1)
        self.assertEqual(len(recommendations), 2)
        self.assertEqual(
            [item["status"] for item in recommendations],
            ["error", "error"],
        )
        self.assertIn(
            "API key not valid",
            recommendations[1]["diagnostic"],
        )

    def test_upload_generates_recommendations_in_all_report_surfaces(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reports_dir = root / "reports"
            uploads_dir = root / "uploads"
            extracted_dir = root / "extracted"
            reports_dir.mkdir()
            uploads_dir.mkdir()
            extracted_dir.mkdir()

            project_result = {
                "languages": ["Python"],
                "dependency_files": [
                    {"file": "requirements.txt", "ecosystem": "Python"}
                ],
            }
            risk_result = {
                "dependencies": self.risks[:1],
                "project": {
                    "project_score": 7.5,
                    "project_risk": "HIGH",
                    "total_dependencies": 1,
                    "total_vulnerabilities": 2,
                },
            }
            with (
                patch.object(app, "REPORT_FOLDER", str(reports_dir)),
                patch.object(app, "UPLOAD_FOLDER", str(uploads_dir)),
                patch.object(app, "EXTRACT_FOLDER", str(extracted_dir)),
                patch.object(report_generator, "REPORT_FOLDER", str(reports_dir)),
                patch.object(app, "detect_project", return_value=project_result),
                patch.object(app, "extract_all_dependencies", return_value=[]),
                patch.object(
                    app, "analyze_dependencies", return_value=self.vulnerabilities[:1]
                ),
                patch.object(app, "analyze_licenses", return_value=self.licenses[:1]),
                patch.object(app, "analyze_risks", return_value=risk_result),
                patch.object(
                    recommendation_engine, "get_gemini_client", return_value=None
                ),
                patch.dict(os.environ, {"GEMINI_API_KEY": ""}),
                patch.dict(app.app.config, {"TESTING": True}),
            ):
                archive_bytes = io.BytesIO()
                with zipfile.ZipFile(archive_bytes, "w") as archive:
                    archive.writestr("requirements.txt", "risky-package==1.0.0")
                archive_bytes.seek(0)

                response = app.app.test_client().post(
                    "/upload",
                    data={"project": (archive_bytes, "validation-upload.zip")},
                    content_type="multipart/form-data",
                )

            self.assertEqual(response.status_code, 200)
            self.assertIn(b"AI-Powered Remediation Recommendations", response.data)
            self.assertIn(b"How to verify:", response.data)
            json_path = next(reports_dir.glob("*.json"))
            html_path = next(reports_dir.glob("*.html"))
            pdf_path = next(reports_dir.glob("*.pdf"))
            report_data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(len(report_data["recommendations"]), 1)
            self.assertEqual(
                report_data["recommendations"][0]["status"],
                "missing_api_key",
            )
            self.assertIn(
                "AI-Powered Remediation Recommendations",
                html_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "GEMINI_API_KEY is not set",
                html_path.read_text(encoding="utf-8"),
            )
            self.assertGreater(pdf_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
