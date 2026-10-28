"""Logging setup. The logs ARE the main output of the prototype (see README)."""
import logging


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)-9s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )
    # keep uvicorn's per-request access log out of the way
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
