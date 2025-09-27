# handlers/admin/force_daily.py
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import logging

from handlers.jobs import daily_crystal_grant_job
from config import ADMIN_ID

logger = logging.getLogger(__name__)

async def force_daily_crystals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Apenas administradores podem usar este comando.")
        return

    await daily_crystal_grant_job(context)
    await update.message.reply_text("✅ Verificação forçada executada. Veja logs para detalhes.")

force_daily_handler = CommandHandler("forcar_cristais", force_daily_crystals)
