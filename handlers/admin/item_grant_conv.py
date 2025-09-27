# Em handlers/admin/item_grant_conv.py (VERSÃO FINAL E CORRIGIDA)

from __future__ import annotations
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CommandHandler,
)

from config import ADMIN_ID
from modules import player_manager

logger = logging.getLogger(__name__)

# --- Estados da Conversa (Nomes Corrigidos) ---
ASKING_PLAYER, ASKING_GEMS, ASKING_CRYSTALS, ASKING_SIGILS, CONFIRM = range(5)

# --- IDs e Nomes dos Itens ---
GEMS_ID = "gems"
CRYSTAL_ID = "cristal_de_abertura"
SIGIL_ID = "sigilo_protecao"

# --- Funções da Conversa ---

# Ponto de Entrada
async def _entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop('grant_data', None)
    text = "🎁 **Entrega de Itens (Admin)**\n\nPara quem você quer enviar os itens? (Envie o ID, @username ou nome do personagem)"
    keyboard = [[InlineKeyboardButton("⬅️ Voltar ao Menu Admin", callback_data="admin_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return ASKING_PLAYER

# Recebe o jogador e pede a quantidade de Diamantes
async def _receive_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    target_id, pdata = player_manager.find_player_by_name_norm(update.message.text) or (None, None)
    if not target_id:
        await update.message.reply_text("❌ Jogador não encontrado. Tente novamente ou use /cancelar.")
        return ASKING_PLAYER
    context.user_data['grant_data'] = {'target_id': target_id, 'target_name': pdata.get("character_name", "N/A")}
    await update.message.reply_text("💎 Quantos **Diamantes** (gems) você quer enviar? (Digite um número)")
    return ASKING_GEMS

# Recebe os Diamantes e pede os Cristais
async def _receive_gems(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text)
        context.user_data['grant_data'][GEMS_ID] = qty
        await update.message.reply_text("✨ Quantos **Cristais de Abertura** você quer enviar? (Digite um número)")
        return ASKING_CRYSTALS
    except (ValueError, TypeError):
        await update.message.reply_text("Por favor, envie um número válido.")
        return ASKING_GEMS

# Recebe os Cristais e pede os Sigilos
async def _receive_crystals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text)
        context.user_data['grant_data'][CRYSTAL_ID] = qty
        await update.message.reply_text("✨ Quantos **Sigilos de Proteção** você quer enviar? (Digite um número)")
        return ASKING_SIGILS
    except (ValueError, TypeError):
        await update.message.reply_text("Por favor, envie um número válido.")
        return ASKING_CRYSTALS

# Recebe os Sigilos e mostra a confirmação final
async def _receive_sigils(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text)
        context.user_data['grant_data'][SIGIL_ID] = qty
        data = context.user_data['grant_data']
        text = (
            "📝 **Confirmação de Envio**\n\n"
            f"Você está prestes a enviar para **{data['target_name']}**:\n"
            f"  •  `{data.get(GEMS_ID, 0)}` 💎 Diamantes\n"
            f"  •  `{data.get(CRYSTAL_ID, 0)}` ✨ Cristais de Abertura\n"
            f"  •  `{data.get(SIGIL_ID, 0)}` ✨ Sigilos de Proteção\n\n"
            "Você confirma a operação?"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Sim, enviar agora", callback_data="grant_confirm")],
            [InlineKeyboardButton("❌ Não, cancelar", callback_data="grant_cancel")]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return CONFIRM
    except (ValueError, TypeError):
        await update.message.reply_text("Por favor, envie um número válido.")
        return ASKING_SIGILS

# Executa a entrega dos itens
async def _execute_grant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = context.user_data.get('grant_data')
    if not data:
        await query.edit_message_text("❌ Erro: Dados da operação perdidos. Comece de novo.")
        return ConversationHandler.END
    target_id = data['target_id']
    pdata = player_manager.get_player_data(target_id)
    gems_qty, crystal_qty, sigil_qty = data.get(GEMS_ID, 0), data.get(CRYSTAL_ID, 0), data.get(SIGIL_ID, 0)
    if gems_qty > 0: player_manager.add_item_to_inventory(pdata, GEMS_ID, gems_qty)
    if crystal_qty > 0: player_manager.add_item_to_inventory(pdata, CRYSTAL_ID, crystal_qty)
    if sigil_qty > 0: player_manager.add_item_to_inventory(pdata, SIGIL_ID, sigil_qty)
    player_manager.save_player_data(target_id, pdata)
    await query.edit_message_text(f"✅ Itens enviados com sucesso para **{data['target_name']}**!")
    context.user_data.pop('grant_data', None)
    return ConversationHandler.END

# Cancela a operação
async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.callback_query.message if update.callback_query else update.message
    await message.reply_text("Operação de entrega cancelada.")
    context.user_data.pop('grant_data', None)
    return ConversationHandler.END

# --- Montagem do ConversationHandler ---
item_grant_conversation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(_entry, pattern=r'^admin:diamond_grant$')
    ],
    states={
        ASKING_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, _receive_player)],
        ASKING_GEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, _receive_gems)],
        ASKING_CRYSTALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, _receive_crystals)],
        ASKING_SIGILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, _receive_sigils)],
        CONFIRM: [
            CallbackQueryHandler(_execute_grant, pattern=r'^grant_confirm$'),
            CallbackQueryHandler(_cancel, pattern=r'^grant_cancel$'),
        ]
    },
    fallbacks=[CommandHandler("cancelar", _cancel)],
    name="item_grant_conv",
    persistent=False
)