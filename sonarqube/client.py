"""
SonarQube Web API client.

This module is the bridge described in the course report: it lets the
analyzer pull the eight standard metrics from a real, running
SonarQube / SonarCloud instance instead of (or alongside) the local
AST-based engine, while the two project-specific custom metrics
(Metric Coverage Ratio, Automated Quality Gate Pass Rate) are always
computed locally, since SonarQube has no native equivalent for them.

Requires a reachable SonarQube server (see docker-compose.yml) and a
user token with 'Browse' permission on the target project. Network
access is required at run time - this client makes no calls on
import.
"""

import requests

DEFAULT_METRIC_KEYS = [
    "ncloc",                     # -> Lines of Code
    "complexity",                # -> Cyclomatic Complexity (project total)
    "cognitive_complexity",
    "duplicated_lines_density",  # -> Code Duplication %
    "sqale_index",                # technical debt minutes -> Maintainability proxy
    "sqale_rating",               # maintainability rating (A-E)
    "coverage",
    "bugs",
    "vulnerabilities",
    "code_smells",
]

# Maps SonarQube measure keys to this project's own standard-metric names,
# so SonarQube data can be merged into the same report shape the local
# engine produces.
SONAR_TO_LOCAL_METRIC_MAP = {
    "ncloc": "logical_loc_sonar",
    "complexity": "cyclomatic_complexity_sonar",
    "duplicated_lines_density": "duplication_pct_sonar",
    "sqale_rating": "maintainability_rating_sonar",
}


class SonarQubeClient:
    def __init__(self, base_url: str, token: str, project_key: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.project_key = project_key
        self.timeout = timeout

    def _auth(self):
        # SonarQube token auth: token as HTTP Basic username, blank password.
        return (self.token, "")

    def test_connection(self) -> dict:
        try:
            resp = requests.get(
                f"{self.base_url}/api/system/status", timeout=self.timeout
            )
            resp.raise_for_status()
            return {"ok": True, "status": resp.json()}
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc)}

    def fetch_measures(self, metric_keys=None) -> dict:
        metric_keys = metric_keys or DEFAULT_METRIC_KEYS
        params = {
            "component": self.project_key,
            "metricKeys": ",".join(metric_keys),
        }
        try:
            resp = requests.get(
                f"{self.base_url}/api/measures/component",
                params=params,
                auth=self._auth(),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc)}

        measures = {
            m["metric"]: m.get("value")
            for m in data.get("component", {}).get("measures", [])
        }
        return {"ok": True, "raw": measures}

    def to_report_format(self, raw_measures: dict) -> dict:
        """Translate raw SonarQube measure keys into this project's
        standard-metric naming so they can be merged into the same
        dashboard rendered for the local engine's output."""
        mapped = {}
        for sonar_key, local_key in SONAR_TO_LOCAL_METRIC_MAP.items():
            if sonar_key in raw_measures:
                value = raw_measures[sonar_key]
                try:
                    mapped[local_key] = float(value)
                except (TypeError, ValueError):
                    mapped[local_key] = value
        return mapped
