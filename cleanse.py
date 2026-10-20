"""Run the cleansing rules in sql/cleanse/ (sorted by file name) against a DuckDB connection holding the raw tables."""

from pathlib import Path

RULES = Path(__file__).parent / "sql" / "cleanse"


def run(con) -> None:
    for rule in sorted(RULES.glob("*.sql")):
        con.execute(rule.read_text())
