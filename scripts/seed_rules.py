#!/usr/bin/env python3
"""Upsert deterministic enrichment rules. Run with PYTHONPATH=src."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adapters.postgres.rule_seed import seed_rules
from config.logging import configure_logging
from config.settings import get_settings

logger = logging.getLogger("seed_rules")


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        count = await seed_rules(session)
        await session.commit()
    await engine.dispose()
    logger.info("rule seed upserted %s rows", count)


if __name__ == "__main__":
    asyncio.run(main())
