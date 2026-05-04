"""FSM Storage на aiosqlite (свой, без внешних пакетов)"""
import aiosqlite
import json
from pathlib import Path
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

DB_PATH = Path(__file__).parent.parent / "data" / "fsm.db"

class SQLiteStorage(BaseStorage):
    async def _get_conn(self):
        return await aiosqlite.connect(str(DB_PATH))
    
    async def set_state(self, key: StorageKey, state: StateType = None):
        async with await self._get_conn() as conn:
            await conn.execute("CREATE TABLE IF NOT EXISTS fsm_state (chat_id INT, user_id INT, state TEXT)")
            await conn.execute("DELETE FROM fsm_state WHERE chat_id=? AND user_id=?", (key.chat_id, key.user_id))
            if state is not None:
                await conn.execute("INSERT INTO fsm_state VALUES (?,?,?)", (key.chat_id, key.user_id, state.state if state else None))
            await conn.commit()
    
    async def get_state(self, key: StorageKey) -> str | None:
        async with await self._get_conn() as conn:
            cursor = await conn.execute("SELECT state FROM fsm_state WHERE chat_id=? AND user_id=?", (key.chat_id, key.user_id))
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def set_data(self, key: StorageKey, data: dict):
        async with await self._get_conn() as conn:
            await conn.execute("CREATE TABLE IF NOT EXISTS fsm_data (chat_id INT, user_id INT, data TEXT)")
            await conn.execute("DELETE FROM fsm_data WHERE chat_id=? AND user_id=?", (key.chat_id, key.user_id))
            await conn.execute("INSERT INTO fsm_data VALUES (?,?,?)", (key.chat_id, key.user_id, json.dumps(data)))
            await conn.commit()
    
    async def get_data(self, key: StorageKey) -> dict:
        async with await self._get_conn() as conn:
            cursor = await conn.execute("SELECT data FROM fsm_data WHERE chat_id=? AND user_id=?", (key.chat_id, key.user_id))
            row = await cursor.fetchone()
            return json.loads(row[0]) if row and row[0] else {}
    
    async def close(self):
        pass
