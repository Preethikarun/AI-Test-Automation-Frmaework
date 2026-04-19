"""
utils/data_factory.py

DataFactory — deterministic test data for all screens.

Rules:
- One @staticmethod per screen (e.g. property_search, login, checkout)
- Values are taken VERBATIM from intake test case DATA blocks
- Callers can override any default by passing keyword arguments
- Never generate random data here — this file is the single source of truth

Usage:
    from utils.data_factory import DataFactory

    # default values from intake
    data = DataFactory.property_search()

    # override one field
    data = DataFactory.property_search(search_term="Auckland apartments")

    # override multiple fields
    data = DataFactory.property_search(
        search_term="Auckland",
        min_price="$600,000",
        max_price="$900,000",
    )

    # in step definitions:
    def step_search(context, term):
        data = DataFactory.property_search(search_term=term)
        TradeMeFacade(context.page, context.tc).search(data["search_term"])

Generated automatically by Agent 2 (BDDGeneratorAgent) when the pipeline runs.
Do NOT edit values manually — re-run the pipeline to update from intake files.
"""

from __future__ import annotations


class DataFactory:
    """
    Deterministic test data factory.

    Every method returns a dict whose keys match the DATA block keys
    in the intake test cases.  Values are the exact strings from the intake files.
    """

    # ── Trade Me — Property Search ────────────────────────────────────────────

    @staticmethod
    def property_search(
        url:           str = "https://www.trademe.co.nz/a/property/residential/sale",
        search_term:   str = "Wellington homes",
        min_price:     str = "$500,000",
        max_price:     str = "$800,000",
        suburb:        str = "Wellington Central",
        bedrooms:      str = "3",
        expected_page: int = 2,
        **overrides,
    ) -> dict:
        """
        Test data for the Trade Me property search screen.
        Values sourced from: intake/trademe_property_search.txt
        """
        base = {
            "url":           url,
            "search_term":   search_term,
            "min_price":     min_price,
            "max_price":     max_price,
            "suburb":        suburb,
            "bedrooms":      bedrooms,
            "expected_page": expected_page,
        }
        return {**base, **overrides}

    @staticmethod
    def property_search_api(
        endpoint:        str = "/v1/Search/Property/Residential.json",
        search_string:   str = "Wellington",
        expected_status: int = 200,
        expected_key:    str = "List",
        **overrides,
    ) -> dict:
        """
        Test data for the Trade Me property search API endpoint.
        Values sourced from: intake/trademe_property_search.txt
        """
        base = {
            "endpoint":        endpoint,
            "search_string":   search_string,
            "expected_status": expected_status,
            "expected_key":    expected_key,
        }
        return {**base, **overrides}

    # ── placeholder for future screens ────────────────────────────────────────
    # Agent 2 will add new @staticmethod methods here when new intake
    # files are processed through the pipeline.
