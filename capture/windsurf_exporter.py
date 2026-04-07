"""
capture/windsurf_exporter.py

Formats MCPAnalysis output for Windsurf to consume.

Windsurf reads windsurf_input.json and, combined with:
  - CLAUDE.md   (framework conventions)
  - skills/PAGE_OBJECT_SKILL.md
  - skills/TEST_CLASS_SKILL.md
  - skills/BDD_SKILL.md

generates:
  - pages/{screen}_page.py       with role-based locators
  - locators/{screen}_locators.py
  - tests/{feature}_test.py      using pytest + POM
  - Auth session fixture shortcut (from auth_apis)
  - API + UI optimised from the same trace

Semi-automated workflow:
    Step 1: playwright codegen --save-trace reports/traces/feature.zip URL
    Step 2: python -m capture.mcp_analyser --trace reports/traces/feature.zip
    Step 3: python -m capture.windsurf_exporter --analysis output/analysis.json
    Step 4: Windsurf reads windsurf_input.json → generates files
    Step 5: Review → APPROVE → git commit

Usage:
    exporter = WindsurfExporter()
    exporter.export(analysis, output_dir="output")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from capture.mcp_analyser import MCPAnalysis


class WindsurfExporter:
    """
    Serialises MCPAnalysis into windsurf_input.json.

    The JSON tells Windsurf:
      - what intent was detected
      - which role-based locators to use
      - which auth APIs to shortcut in fixtures
      - which framework conventions to follow
      - which skill files to read before generating
    """

    SKILLS_DIR     = Path("skills")
    OUTPUT_DEFAULT = Path("output")

    def export(
        self,
        analysis:   MCPAnalysis,
        output_dir: str = "output",
    ) -> Path:
        """
        Write windsurf_input.json to output_dir.

        Args:
            analysis:   MCPAnalysis from MCPAnalyser.analyse()
            output_dir: where to write the file

        Returns:
            Path to the written file
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        payload = self._build_payload(analysis)
        output_path = out / "windsurf_input.json"
        output_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        print(f"WindsurfExporter: written → {output_path}")
        return output_path

    def _build_payload(self, analysis: MCPAnalysis) -> dict:
        """
        Build the full Windsurf input payload.
        Every key maps to something Windsurf acts on.
        """
        return {
            # ── what was captured ─────────────────────────────────
            "generated_at":   datetime.now(timezone.utc).isoformat(),
            "trace_path":     analysis.trace_path,
            "intent":         analysis.intent,
            "flaky_risk":     analysis.flaky_risk,

            # ── HOW to automate ───────────────────────────────────
            "role_locators":  analysis.role_map,
            "causality":      analysis.causality,

            # ── auth shortcut ─────────────────────────────────────
            # Windsurf generates a session fixture using these APIs
            # so tests skip the UI login flow entirely
            "auth_setup": {
                "apis":        analysis.auth_apis,
                "fixture_name": f"{analysis.intent}_session",
            },

            # ── framework conventions ─────────────────────────────
            # Windsurf reads CLAUDE.md and skills/ to generate code
            # that matches existing patterns exactly
            "framework_style": "pytest_pom_behave_bdd",
            "conventions_ref": "CLAUDE.md",
            "skill_files": [
                str(self.SKILLS_DIR / "PAGE_OBJECT_SKILL.md"),
                str(self.SKILLS_DIR / "TEST_CLASS_SKILL.md"),
                str(self.SKILLS_DIR / "BDD_SKILL.md"),
            ],

            # ── generation instructions ───────────────────────────
            "generate": {
                "locators_file": f"locators/{analysis.intent}_locators.py",
                "page_file":     f"pages/{analysis.intent}_page.py",
                "test_file":     f"tests/test_{analysis.intent}.py",
                "steps_file":    f"steps/{analysis.intent}_steps.py",
                "feature_file":  f"features/{analysis.intent}.feature",
            },

            # ── locator strategy ──────────────────────────────────
            "locator_preference": [
                "aria-label",
                "data-testid",
                "role",
                "name",
                "placeholder",
                "css class (last resort)",
            ],

            # ── optimisation hint ─────────────────────────────────
            # same trace generates both API test and UI test
            "api_ui_optimisation": True,
        }

    # ── CLI entry point ───────────────────────────────────────────

    @classmethod
    def from_analysis_file(cls, analysis_json: str, output_dir: str) -> Path:
        """
        Load MCPAnalysis from a saved JSON file and export.

        CLI usage:
            python -m capture.windsurf_exporter \
                --analysis output/analysis.json \
                --output output
        """
        data     = json.loads(Path(analysis_json).read_text())
        analysis = MCPAnalysis(**data)
        return cls().export(analysis, output_dir)


# ── CLI runner ────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Export MCP analysis to Windsurf input format"
    )
    parser.add_argument("--analysis", required=True,
                        help="Path to MCPAnalysis JSON file")
    parser.add_argument("--output", default="output",
                        help="Output directory (default: output/)")
    args = parser.parse_args()

    output_path = WindsurfExporter.from_analysis_file(
        args.analysis, args.output
    )
    print(f"Done: {output_path}")
