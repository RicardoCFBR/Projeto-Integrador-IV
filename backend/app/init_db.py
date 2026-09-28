"""Create the tables through the ORM. Prefer db/schema.sql for a reference PostgreSQL setup."""

import logging

import app.models  # noqa: F401
from app.database import Base, get_engine

logger = logging.getLogger(__name__)


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("tables created on %s", engine.url.render_as_string(hide_password=True))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
