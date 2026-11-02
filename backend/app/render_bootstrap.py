"""Initialize a new cloud demo database without wiping existing data.

Render's free Postgres database begins empty. This sets up the ORM schema and
seeds the same experimental risk policy used by db/schema.sql. It never
deletes telemetry, predictions, or an existing active policy.
"""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.database import Base, get_engine
from app.models import RiskPolicy

logger = logging.getLogger(__name__)


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        active = session.scalar(select(RiskPolicy).where(RiskPolicy.is_active.is_(True)))
        if active is None:
            policy = session.scalar(
                select(RiskPolicy).where(RiskPolicy.name == "experimental-v2")
            )
            if policy is None:
                policy = RiskPolicy(
                    name="experimental-v2",
                    high_below_cycles=Decimal("776"),
                    medium_below_cycles=Decimal("983"),
                    source="experimental",
                    is_active=True,
                    notes="Limiares experimentais derivados da frota sintetica; nao validados com operacao.",
                )
                session.add(policy)
            else:
                policy.is_active = True
            session.commit()
            logger.info("risk policy experimental-v2 activated")
    logger.info("demo schema ready")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
