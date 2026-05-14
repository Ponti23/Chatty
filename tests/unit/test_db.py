import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_db_connection(db_session):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_sources_table_exists(db_session):
    result = await db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name = 'sources'")
    )
    assert result.scalar() == "sources"
