"""One-off script to generate a valuation report for a single property."""

import logging
import sys
from typing import NoReturn

from bot import MLSCompBot
from report_generator import ReportGenerator

ADDRESS = "3644 E CONSTITUTION DR"
CITY = "GILBERT"
STATE = "AZ"
ZIP_CODE = "85296"
MAX_COMPS = 5

logger = logging.getLogger(__name__)


def main() -> NoReturn:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    bot = MLSCompBot()
    if not bot.connect():
        logger.error("ATTOM connection failed. Check credentials/config.")
        sys.exit(1)

    try:
        comp_result = bot.find_comps_for_property(
            address=ADDRESS,
            city=CITY,
            state=STATE,
            zip_code=ZIP_CODE,
            max_comps=MAX_COMPS,
        )
    except Exception as exc:  # pragma: no cover - operational script
        logger.error(f"Failed to fetch comps: {exc}", exc_info=True)
        sys.exit(1)

    if not comp_result:
        logger.error("No comps returned.")
        sys.exit(1)

    rg = ReportGenerator()
    try:
        html_path = rg.save_report(comp_result, format="html")
        md_path = rg.save_report(comp_result, format="markdown")
    except Exception as exc:  # pragma: no cover - operational script
        logger.error(f"Failed to save report: {exc}", exc_info=True)
        sys.exit(1)

    logger.info("Report generation complete.")
    print(f"HTML report: {html_path}")
    print(f"Markdown report: {md_path}")


if __name__ == "__main__":
    main()
