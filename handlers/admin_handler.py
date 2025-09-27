# handlers/admin_handler.py
from __future__ import annotations
import logging, asyncio
from typing import Dict, Optional, Callable, Awaitable
from handlers.jobs import daily_crystal_grant_job, force_grant_daily_crystals
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
)
from telegram.error import BadRequest
from config import ADMIN_ID

logger = logging.getLogger(__name__)
HTML = "HTML"

# =========================================================
# Utils básicos
# =========================================================
def _is_admin(update: Update) -> bool:
    return bool(update.effective_user and update.effective_user.id == ADMIN_ID)

# ---- teclado cacheado (evita recriar objetos) ----
_ADMIN_KB: Optional[InlineKeyboardMarkup] = None
def _admin_menu_kb() -> InlineKeyboardMarkup:
    global _ADMIN_KB
    if _ADMIN_KB is None:
        _ADMIN_KB = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 𓂀 𝔼𝕟𝕥𝕣𝕖𝕘𝕒𝕣 𝕀𝕥𝕖𝕟𝕤 (𝔸𝕕𝕞𝕚𝕟) 𓂀", callback_data="admin:diamond_grant")],
            [InlineKeyboardButton("🔁 𓂀 𝔽𝕠𝕣ç𝕒𝕣 𝕕𝕚á𝕣𝕚𝕠𝕤 (ℂ𝕣𝕚𝕤𝕥𝕒𝕚𝕤) 𓂀", callback_data="admin_force_daily")],
            [InlineKeyboardButton("👑 𓂀 ℙ𝕣𝕖𝕞𝕚𝕦𝕞 𓂀", callback_data="admin_premium")],
            [InlineKeyboardButton("📁 𓂀 𝔾𝕖𝕣𝕖𝕟𝕔𝕚𝕒𝕣 𝔽𝕚𝕝𝕖 𝕀𝔻𝕤 𓂀", callback_data="admin_file_ids")],
            [InlineKeyboardButton("🧹 𓂀 ℝ𝕖𝕤𝕖𝕥/ℝ𝕖𝕤𝕡𝕖𝕔 𓂀", callback_data="admin_reset_menu")],
            [InlineKeyboardButton("🔄 𝐑𝐞𝐬𝐞𝐭𝐚𝐫 𝐄𝐬𝐭𝐚𝐝𝐨 (/𝐫𝐞𝐬𝐞𝐭_𝐬𝐭𝐚𝐭𝐞)", callback_data="admin_reset_state_hint")],
        ])
    return _ADMIN_KB

async def _safe_answer(update: Update) -> None:
    q = update.callback_query
    if not q:
        return
    try:
        await q.answer()
    except BadRequest:
        pass
    except Exception:
        logger.debug("query.answer() ignorado", exc_info=True)

async def _safe_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str,
                          reply_markup: InlineKeyboardMarkup | None = None) -> None:
    q = update.callback_query
    try:
        if q and q.message:
            await q.edit_message_text(text, parse_mode=HTML, reply_markup=reply_markup)
            return
    except Exception:
        pass
    # fallback
    chat_id = (q.message.chat.id if q and q.message else update.effective_chat.id)
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=HTML, reply_markup=reply_markup)

# =========================================================
# /admin (abre painel)
# =========================================================
async def _send_admin_menu(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=chat_id,
        text="🎛️ <b>Painel do Admin</b>\nEscolha uma opção:",
        reply_markup=_admin_menu_kb(),
        parse_mode=HTML,
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        if update.effective_message:
            await update.effective_message.reply_text("Sem permissão.")
        return
    await _send_admin_menu(update.effective_chat.id, context)

admin_command_handler = CommandHandler("admin", admin_command, filters=filters.User(ADMIN_ID))

# =========================================================
# Submenus simples
# =========================================================


async def _handle_admin_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _safe_answer(update)
    await _safe_edit_text(update, context, "🎛️ <b>Painel do Admin</b>\nEscolha uma opção:", _admin_menu_kb())



async def _handle_admin_force_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _safe_answer(update)
    if not _is_admin(update):
        return
    
    # Edita a mensagem para dar um feedback de que está processando
    await _safe_edit_text(update, context, "⏳ Processando entrega de cristais diários...")
    
    # Executa o job e CAPTURA o resultado
    granted_count = await force_grant_daily_crystals(context)
    
    # Monta a nova mensagem com o resultado
    feedback_text = f"✅ Executado! <b>{granted_count}</b> jogadores receberam os cristais diários."
    
    await _safe_edit_text(
        update, context,
        feedback_text,
        InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ 𓂀 𝕍𝕠𝕝𝕥𝕒𝕣 𓂀", callback_data="admin_main")]])
    )

async def force_daily_crystals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        if update.effective_message:
            await update.effective_message.reply_text("Sem permissão.")
        return
    
    # Adiciona um feedback imediato para o admin saber que o comando foi recebido
    await update.effective_message.reply_text("⏳ Processando entrega forçada de cristais para todos os jogadores...")
    
    # Chama a NOVA função "superpoderosa" e captura a contagem de jogadores
    granted_count = await force_grant_daily_crystals(context)
    
    # Envia o feedback final com o resultado exato
    await update.effective_message.reply_text(
        f"✅ Executado! <b>{granted_count}</b> jogadores receberam os cristais diários.",
        parse_mode="HTML"
    )

# A linha abaixo não muda, mas a incluo para você substituir o bloco todo
force_daily_handler = CommandHandler("forcar_cristais", force_daily_crystals_cmd, filters=filters.User(ADMIN_ID))

# =========================================================
# Roteador do painel admin
# =========================================================
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not _is_admin(update):
        if query:
            await query.answer("Sem permissão.", show_alert=True)
        return

    data = (query.data or "") if query else ""

    # Esta seção ignora os cliques que serão tratados pelas nossas novas conversas
    # (Premium, File ID, e o novo Painel de Reset), deixando-os passar.
    if data.startswith("admin:") or data in ["admin_file_ids", "admin_reset_menu", "admin_premium"]:
        return

    # Ações que ainda são tratadas diretamente neste arquivo
    if data == "admin_force_daily":
        await _handle_admin_force_daily(update, context)
        return
    
    if data == "admin_main":
        await _handle_admin_main(update, context)
        return
    
    # Se o clique não corresponder a nada, apenas confirma o recebimento sem fazer nada
    await _safe_answer(update)

admin_callback_handler = CallbackQueryHandler(
    admin_callback,
    pattern=r"^admin_.*$|^admin:.*$"
)