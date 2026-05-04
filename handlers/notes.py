"""
handlers/notes.py — 📝 Заметки
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo
from keyboards.reply import MAIN_KB
from db.connection import get_db

router = Router()

@router.message(Command("note"))
async def cmd_note(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return

    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        async with get_db() as conn:
            cursor = await conn.execute(
                "SELECT * FROM notes WHERE user_id=? ORDER BY done, created_at DESC LIMIT 10",
                (user["id"],)
            )
            notes = await cursor.fetchall()
        
        if not notes:
            await message.answer(
                "📝 *Заметки пусты*\n\n"
                "Добавь: `/note позвонить маме`\n"
                "Отметь: `/done 1` (номер заметки)\n"
                "Удали: `/delnote 1`",
                parse_mode="Markdown",
                reply_markup=MAIN_KB
            )
            return
        
        text = "📝 *Твои заметки:*\n\n"
        for note in notes:
            marker = "✅" if note["done"] else "☐"
            text += f"{marker} *{note['id']}.* {note['text']}\n"
        
        await message.answer(text, parse_mode="Markdown", reply_markup=MAIN_KB)
        return
    
    note_text = parts[1].strip()
    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO notes (user_id, text) VALUES (?, ?)",
            (user["id"], note_text)
        )
        await conn.commit()
    
    await message.answer(f"📝 *Добавлено:* {note_text}", parse_mode="Markdown", reply_markup=MAIN_KB)


@router.message(Command("done"))
async def cmd_done(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Укажи номер: `/done 1`", parse_mode="Markdown")
        return
    
    note_id = int(parts[1])
    async with get_db() as conn:
        await conn.execute(
            "UPDATE notes SET done=1 WHERE id=? AND user_id=?",
            (note_id, user["id"])
        )
        await conn.commit()
    
    await message.answer(f"✅ Заметка #{note_id} выполнена!", reply_markup=MAIN_KB)


@router.message(Command("delnote"))
async def cmd_delnote(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Укажи номер: `/delnote 1`", parse_mode="Markdown")
        return
    
    note_id = int(parts[1])
    async with get_db() as conn:
        await conn.execute(
            "DELETE FROM notes WHERE id=? AND user_id=?",
            (note_id, user["id"])
        )
        await conn.commit()
    
    await message.answer(f"🗑 Заметка #{note_id} удалена", reply_markup=MAIN_KB)
