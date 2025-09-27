# =========================
# main.py — Mundo de Eldora (prioridades organizadas)
# =========================

from __future__ import annotations
import logging
from datetime import datetime, timezone, time
from zoneinfo import ZoneInfo
from handlers.chat_handler import chat_interaction_handler
from handlers.job_handler import finish_collection_job, job_handler
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    filters,
    MessageHandler,
)
from modules import player_manager
from config import ADMIN_ID, TELEGRAM_TOKEN
from handlers.daily_jobs import daily_pvp_entry_reset_job

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ---------------------------------------------------------------------------
# Crafting: registra todas as receitas (T1/T2/etc.)
# ---------------------------------------------------------------------------
try:
    from modules.recipes import register_all as register_all_recipes
    register_all_recipes()
    logging.info("[RECIPES] Pacotes de receitas registrados com sucesso.")
except Exception as e:
    logging.info("[RECIPES] Registro de receitas não disponível: %s", e)

# ---------------------------------------------------------------------------
# Jobs/Timers principais
# ---------------------------------------------------------------------------
from handlers.jobs import regenerate_energy_job, daily_crystal_grant_job
from handlers.refining_handler import finish_dismantle_job

# Forja (opcional)
try:
    from handlers.forge_handler import (
        finish_craft_notification_job as finish_crafting_job,
        forge_handler,
    )
except Exception:
    finish_crafting_job = None  # type: ignore[assignment]
    forge_handler = None  # type: ignore[assignment]

# Refino (opcional)
try:
    from handlers.refining_handler import (
        finish_refine_job as finish_refining_job,
        ref_confirm_handler,
        ref_select_handler,
        refining_main_callback,
        refining_main_handler,
        dismantle_list_handler,      # <-- ADICIONE AQUI
        dismantle_preview_handler,   # <-- ADICIONE AQUI
        dismantle_confirm_handler    # <-- ADICIONE AQUI
    )
except Exception:
    finish_refining_job = None  # type: ignore[assignment]
    refining_main_handler = None  # type: ignore[assignment]
    ref_select_handler = None  # type: ignore[assignment]
    ref_confirm_handler = None  # type: ignore[assignment]
    refining_main_callback = None  # type: ignore[assignment]

# --- Calabouço (runtime) ---
try:
    
    from modules.dungeons.runtime import (
        dungeon_open_handler,
        dungeon_pick_handler,
    )
except Exception:
    dungeon_open_handler = None  # type: ignore[assignment]
    dungeon_pick_handler = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# HANDLERS essenciais
# ---------------------------------------------------------------------------
# Admin básico
from handlers.admin.item_grant_conv import item_grant_conversation_handler
from handlers.admin_handler import (
    admin_callback_handler,
    admin_command_handler,
)

# Conversas do Admin (DEVEM vir antes do admin_callback_handler)
from handlers.admin.file_id_conv import file_id_conv_handler
from handlers.admin.premium_panel import premium_panel_handler, premium_command_handler
from handlers.admin.reset_panel import reset_panel_conversation_handler
from handlers.admin.force_daily import force_daily_handler
from handlers.admin.premium_panel import premium_panel_handler, premium_command_handler
# Início / Criação
from handlers.start_handler import (
    character_creation_handler,
    start_command_handler,
    name_command_handler,
)

# Party (sem dungeons)
try:
    from handlers.events.party_handler import (
        invite_conversation_handler,
        party_callback_handler,
    )
except Exception:

    invite_conversation_handler = None  # type: ignore[assignment]
    party_callback_handler = None  # type: ignore[assignment]

# Menus / Navegação
from handlers.menu_handler import continue_after_action_handler, kingdom_menu_handler, travel_handler
# Região / Viagem / Kingdom menu
try:
    from handlers.menu.region import (
        region_handler as region_callback_handler,
        travel_handler as travel_callback_handler,
        restore_durability_menu_handler,
        restore_durability_fix_handler,
        collect_handler as collect_callback_handler,  # <--- agora importamos o handler de coleta
        finish_travel_job,
        open_region_handler,
       
    )
except Exception:
    region_callback_handler = None  # type: ignore[assignment]
    travel_callback_handler = None  # type: ignore[assignment]
    restore_durability_menu_handler = None  # type: ignore[assignment]
    restore_durability_fix_handler = None  # type: ignore[assignment]
    collect_callback_handler = None  # type: ignore[assignment]

try:
    from handlers.menu.kingdom import show_kingdom_menu
except Exception as e:
    print(f"\n!!!! ERRO AO IMPORTAR: {e} !!!!\n")
    show_kingdom_menu = None  # type: ignore[assignment]

# Perfil / Status
from handlers.profile_handler import profile_handler
from handlers.status_handler import (
    close_status_handler,
    status_callback_handler,
    status_command_handler,
    status_open_handler,
)

# _______pvp_______
from pvp.pvp_handler import pvp_handlers

# Inventário / Ações gerais
from handlers.inventory_handler import inventory_handler, noop_inventory_handler
from handlers.hunt_handler import hunt_handler
from handlers.combat_handler import (
    combat_handler,
    continue_after_action_handler,
)
from handlers.class_selection_handler import class_selection_handler

# Equipamentos
from handlers.equipment_handler import (
    equip_pick_handler,
    equip_slot_handler,
    equip_unequip_handler,
    equipment_menu_handler,
)

# Crafting UI
from handlers.crafting_handler import craft_open_handler

# Enhance / Aprimoramento
from handlers.enhance_handler import (
    enhance_action_handler,
    enhance_menu_handler,
    enhance_select_handler,
)

# Profissões
from handlers.profession_handler import job_menu_handler, job_pick_handler

# Mercado
from handlers.market_handler import (
    kingdom_qty_minus_handler,
    kingdom_qty_plus_handler,
    kingdom_set_item_handler,
    market_adventurer_handler,
    market_buy_handler,
    market_cancel_handler,
    market_cancel_new_handler,
    market_kingdom_buy_handler,
    market_kingdom_buy_legacy_handler,
    market_kingdom_handler,
    market_list_handler,
    market_my_handler,
    market_open_handler,
    market_pick_stack_handler,
    market_pick_unique_handler,
    market_price_confirm_handler,
    market_price_spin_handler,
    market_qty_handler,
    market_sell_handler,
)

# Loja de Gemas
from handlers.gem_shop import (
    gem_shop_open_handler,
    gem_pick_handler,
    gem_qty_minus_handler,
    gem_qty_plus_handler,
    gem_buy_handler,
    gem_shop_command_handler,
)
# Guilda - Clans
from handlers.guild_handler import clan_logo_conv_handler
from handlers.guild_handler import clan_creation_conv_handler
from handlers.guild_handler import (
    guild_menu_handler,
    clan_menu_handler,
    clan_upgrade_menu_handler,
    clan_creation_conv_handler, # Conversa de Criar Clã
    clan_search_conv_handler,   # Conversa de Procurar Clã
    clan_apply_handler,         # O handler que está a dar erro
    clan_manage_apps_handler,
    clan_app_accept_handler,
    clan_app_decline_handler,
    noop_handler,
    clan_upgrade_confirm_handler,
    clan_leave_confirm_handler,
    clan_leave_do_handler,
    clan_manage_menu_handler,
    clan_kick_menu_handler,
    clan_kick_confirm_handler,
    clan_kick_do_handler,
    clan_transfer_leader_conv_handler,
    missions_menu_handler,
    mission_claim_handler,
    mission_reroll_handler,
    clan_mission_start_handler, clan_mission_confirm_handler,
    clan_bank_menu_handler,
    clan_deposit_conv_handler,
    clan_withdraw_conv_handler,
    clan_board_purchase_handler,
    clan_guild_mission_details_handler,
)
# Evolução de classe (menu e execução)
from handlers.class_evolution_handler import (
    evolution_command_handler,
    evolution_callback_handler,
    evolution_do_handler,
    evolution_cancel_handler,
    status_evolution_open_handler,  # botão do status abre evolução
)

# Mercado (validação opcional)
try:
    from modules.game_data.market import validate_market_items
except Exception:
    validate_market_items = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Error Handler
# ---------------------------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Exceção ao processar um update: %s", context.error)

# ---------------------------------------------------------------------------
# Premium: verificação de expiração
# ---------------------------------------------------------------------------
from modules.player_manager import (
    is_player_premium,
    iter_players,
    save_player_data,
)

async def check_premium_expirations(context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("[SCHEDULER] Verificando expiração de premium...")
    for user_id, player_data in iter_players():
        try:
            if player_data.get("premium_expires_at") and not is_player_premium(player_data):
                logging.info("Premium do jogador %s expirou. Limpando...", user_id)
                player_data["premium_tier"] = None
                player_data["premium_expires_at"] = None
                save_player_data(user_id, player_data)
                try:
                    await context.bot.send_message(chat_id=user_id, text="Sua assinatura premium expirou!")
                except Exception as e:
                    logging.warning("Falha ao notificar %s: %s", user_id, e)
        except Exception as e:
            logging.warning("[PREMIUM] Erro com jogador %s: %s", user_id, e)

# ---------------------------------------------------------------------------
# Startup Notice
# ---------------------------------------------------------------------------
async def send_startup_message(application) -> None:
    if not ADMIN_ID:
        return
    try:
        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text="✅ O bot *Mundo de Eldora* foi iniciado com sucesso!",
            parse_mode="Markdown",
            disable_notification=True,
        )
        logging.info("Mensagem de inicialização enviada para ADMIN_ID %s", ADMIN_ID)
    except Exception as e:
        logging.warning("Não foi possível enviar mensagem de inicialização: %s", e)

# ---------------------------------------------------------------------------
def _get_action_restorers():
    restorers = {}
    
    # Restauração da COLETA
    if finish_collection_job:
        restorers["collecting"] = {
            "fn": finish_collection_job,
            "data_builder": lambda st: {
                "resource_id": (st.get("details") or {}).get("resource_id"),
                "item_id_yielded": (st.get("details") or {}).get("item_id_yielded"),
                "energy_cost": (st.get("details") or {}).get("energy_cost", 1),
                "speed_mult": (st.get("details") or {}).get("speed_mult", 1.0),
                "charged": True,
            },
        }
        
    # Restauração da VIAGEM
    if finish_travel_job: # Supondo que finish_travel_job foi importado
        restorers["travel"] = {
            "fn": finish_travel_job,
            "data_builder": lambda st: {
                "dest": st.get("travel_dest"), # A viagem guarda o destino fora dos 'details'
            },
        }

    # Restauração do REFINO
    if finish_refining_job:
        restorers["refining"] = {
            "fn": finish_refining_job,
            "data_builder": lambda st: {
                "recipe_id": (st.get("details") or {}).get("recipe_id")
            },
        }

    # Restauração da FORJA (Crafting)
    if finish_crafting_job:
        restorers["crafting"] = {
            "fn": finish_crafting_job,
            "data_builder": lambda st: {
                "recipe_id": (st.get("details") or {}).get("recipe_id")
            },
        }
        
    return restorers

async def restore_scheduled_jobs(app) -> None:
    job_queue = app.job_queue
    now = datetime.now(timezone.utc)
    restored = 0

    # O dicionário de finalizadores agora é construído aqui dentro
    ACTION_RESTORERS = {
        "collecting": {"fn": finish_collection_job, "data_builder": lambda st: (st.get("details") or {})},
        "crafting": {"fn": finish_crafting_job, "data_builder": lambda st: (st.get("details") or {})},
        "refining": {"fn": finish_refining_job, "data_builder": lambda st: (st.get("details") or {})},
        # CORRIGIDO: Agora lê o destino do sítio certo
        "travel": {"fn": finish_travel_job, "data_builder": lambda st: {"dest": (st.get("details") or {}).get("destination")}},
        "dismantling": {"fn": finish_dismantle_job, "data_builder": lambda st: (st.get("details") or {})},
        # Adicione 'dismantling' aqui quando o criar
    }

    for user_id, pdata in player_manager.iter_players():
        st = pdata.get("player_state") or {}
        action = st.get("action")
        finish_iso = st.get("finish_time")
        if not (action and finish_iso and action in ACTION_RESTORERS):
            continue

        try:
            ft = datetime.fromisoformat(finish_iso)
            if ft.tzinfo is None: ft = ft.replace(tzinfo=timezone.utc)
        except Exception:
            pdata["player_state"] = {"action": "idle"}
            player_manager.save_player_data(user_id, pdata)
            continue
        
        delay = max(0, (ft - now).total_seconds())
        
        restorer = ACTION_RESTORERS[action]
        job_data = restorer["data_builder"](st) if restorer.get("data_builder") else {}
        chat_id = pdata.get("last_chat_id", user_id)
        
        job_queue.run_once(restorer["fn"], when=delay, chat_id=chat_id, user_id=user_id, data=job_data, name=f"{action}:{user_id}")
        restored += 1

    logging.info("[RESTORE] Jobs re-agendados: %s", restored)

# ---------------------------------------------------------------------------
# Watchdog de ações cronometradas
# ---------------------------------------------------------------------------
async def timed_actions_watchdog(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        now = datetime.now(timezone.utc)
        jq = context.job_queue
        action_restorers = _get_action_restorers()

        fixed = 0
        for user_id, pdata in iter_players():
            st = pdata.get("player_state") or {}
            action = st.get("action")
            finish_iso = st.get("finish_time")
            if not action or not finish_iso:
                continue

            if action not in action_restorers:
                try:
                    ft = datetime.fromisoformat(finish_iso)
                except Exception:
                    ft = None
                if ft is None or ((ft.tzinfo or timezone.utc) and ft <= now):
                    pdata["player_state"] = {"action": "idle"}
                    save_player_data(user_id, pdata)
                    fixed += 1
                continue

            try:
                ft = datetime.fromisoformat(finish_iso)
                if ft.tzinfo is None:
                    ft = ft.replace(tzinfo=timezone.utc)
            except Exception:
                pdata["player_state"] = {"action": "idle"}
                save_player_data(user_id, pdata)
                fixed += 1
                continue

            if ft <= now:
                rest = action_restorers[action]
                data = rest["data_builder"](st) if rest.get("data_builder") else None
                chat_id = pdata.get("last_chat_id", user_id)
                jq.run_once(
                    rest["fn"],
                    when=0,
                    chat_id=chat_id,
                    user_id=user_id,
                    data=data,
                    name=f"{action}:{user_id}",
                )
                fixed += 1

        if fixed:
            logging.info("[WATCHDOG] Ações vencidas reparadas/disparadas: %s", fixed)
    except Exception as e:
        logging.warning("[WATCHDOG] Erro: %s", e)

# ---------------------------------------------------------------------------
# Runtime Tweaks
# ---------------------------------------------------------------------------
def _patch_runtime_rules() -> None:
    try:
        from modules import game_data as _game_data
        if not hasattr(_game_data, "TRAVEL_DEFAULT_SECONDS") or int(getattr(_game_data, "TRAVEL_DEFAULT_SECONDS")) <= 0:
            _game_data.TRAVEL_DEFAULT_SECONDS = 600
            logging.info("[TRAVEL] TRAVEL_DEFAULT_SECONDS definido para 600s (10 min).")
    except Exception:
        pass

    try:
        from modules.game_data import premium as _premium_mod
        tiers = getattr(_premium_mod, "PREMIUM_TIERS", {})
        if isinstance(tiers, dict):
            changed = False
            for tk in ("premium", "vip", "lenda"):
                td = tiers.get(tk) or {}
                perks = dict(td.get("perks", {}))
                if "travel_time_multiplier" not in perks or perks.get("travel_time_multiplier") != 0:
                    perks["travel_time_multiplier"] = 0
                    td["perks"] = perks
                    tiers[tk] = td
                    changed = True
            if changed:
                _premium_mod.PREMIUM_TIERS = tiers
                logging.info("[PREMIUM] travel_time_multiplier=0 aplicado aos tiers pagos.")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Post init
# ---------------------------------------------------------------------------
# Em main.py

async def _post_init(app) -> None:
    _patch_runtime_rules()
    await send_startup_message(app)
    try:
        from modules.game_data.market import validate_market_items  # late-import
        validate_market_items()
    except Exception:
        pass
    await restore_scheduled_jobs(app)
# ---------------------------------------------------------------------------
# GROUP PRIORITIES
# ---------------------------------------------------------------------------
G0_CONVERSATIONS   = 0   # conversas críticas (block=True)
G1_ADMIN_ROUTER    = 1   # roteadores/callbacks admin
G2_CALLBACKS_PRIM  = 2   # callbacks principais dos menus
G3_COMMANDS        = 3   # comandos gerais
G5_SECONDARY       = 5   # handlers secundários
G9_PARTY           = 9   # party callback
G10_BACKGROUND     = 10  # “fundo” / menos prioritário
G15_CHAT_LISTENER  = 15 
def add_if(app, handler, group):
    if handler:
        app.add_handler(handler, group=group)

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(_post_init).build()
    application.add_error_handler(error_handler)

    # Jobs
    jq = application.job_queue
    jq.run_repeating(regenerate_energy_job, interval=300, first=10)
    jq.run_repeating(check_premium_expirations, interval=21600, first=60)
    jq.run_repeating(timed_actions_watchdog, interval=120, first=45)
    jq.run_daily(
        daily_crystal_grant_job,
        time=time(hour=0, minute=5, tzinfo=ZoneInfo("America/Fortaleza")),
        name="daily_crystal_grant_job",
    )

    jq.run_daily(
    daily_pvp_entry_reset_job,
    time=time(hour=0, minute=6, tzinfo=ZoneInfo("America/Fortaleza")), # 1 minuto depois dos cristais
    name="daily_pvp_entry_reset_job",
    )

    # =======================
    # PRIORIDADES
    # =======================

    # G0 — CONVERSAS CRÍTICAS (file_id_conv primeiro!)
    add_if(application, file_id_conv_handler,        G0_CONVERSATIONS)   # <<< prioridade máxima
    add_if(application, premium_panel_handler,       G0_CONVERSATIONS)
    add_if(application, invite_conversation_handler, G0_CONVERSATIONS)   # party conversation
    add_if(application, reset_panel_conversation_handler, G0_CONVERSATIONS)
    add_if(application, item_grant_conversation_handler, G0_CONVERSATIONS)
    add_if(application, clan_creation_conv_handler, G0_CONVERSATIONS)
    add_if(application, clan_transfer_leader_conv_handler, G0_CONVERSATIONS)
    add_if(application, clan_logo_conv_handler, G0_CONVERSATIONS)
    
    # G1 — ROTEADORES ADMIN (depois das conversas)
    add_if(application, admin_command_handler,       G1_ADMIN_ROUTER)
    add_if(application, admin_callback_handler,      G1_ADMIN_ROUTER)
    add_if(application, premium_command_handler,     G1_ADMIN_ROUTER)
    add_if(application, force_daily_handler,         G1_ADMIN_ROUTER)  # /force_daily

    # 🚀 Loja de Diamantes — SUBIDA PARA G1 (evita colisões de callback)
    add_if(application, gem_shop_open_handler,       G1_ADMIN_ROUTER)
    add_if(application, gem_pick_handler,            G1_ADMIN_ROUTER)
    add_if(application, gem_qty_minus_handler,       G1_ADMIN_ROUTER)
    add_if(application, gem_qty_plus_handler,        G1_ADMIN_ROUTER)
    add_if(application, gem_buy_handler,             G1_ADMIN_ROUTER)

    # disponibiliza ADMIN_ID para guards internos (ex.: itemgen)
    application.bot_data["ADMIN_ID"] = int(ADMIN_ID) if ADMIN_ID else None
    add_if(application, continue_after_action_handler, G2_CALLBACKS_PRIM) # <-- AQUI
    add_if(application, kingdom_menu_handler,          G2_CALLBACKS_PRIM) # <-- E AQUI
    add_if(application, travel_handler,                G2_CALLBACKS_PRIM) # <-- O de viajar também fica bem aqui
    # G2 — CALLBACKS PRINCIPAIS (menus/fluxos)
    add_if(application, profile_handler,               G2_CALLBACKS_PRIM)
    add_if(application, status_open_handler,           G2_CALLBACKS_PRIM)
    add_if(application, status_command_handler,        G2_CALLBACKS_PRIM)
    add_if(application, status_callback_handler,       G2_CALLBACKS_PRIM)
    add_if(application, close_status_handler,          G2_CALLBACKS_PRIM)
    add_if(application, status_evolution_open_handler, G2_CALLBACKS_PRIM)
    
    add_if(application, open_region_handler,           G2_CALLBACKS_PRIM)
    add_if(application, dismantle_list_handler,      G2_CALLBACKS_PRIM)
    add_if(application, dismantle_preview_handler,   G2_CALLBACKS_PRIM)
    add_if(application, dismantle_confirm_handler,   G2_CALLBACKS_PRIM)
    add_if(application, equipment_menu_handler,        G2_CALLBACKS_PRIM)
    add_if(application, equip_slot_handler,            G2_CALLBACKS_PRIM)
    add_if(application, equip_pick_handler,            G2_CALLBACKS_PRIM)
    add_if(application, equip_unequip_handler,         G2_CALLBACKS_PRIM)

    add_if(application, inventory_handler,             G2_CALLBACKS_PRIM)
    add_if(application, noop_inventory_handler,        G2_CALLBACKS_PRIM)
    add_if(application, hunt_handler,                  G2_CALLBACKS_PRIM)
    add_if(application, combat_handler,                G2_CALLBACKS_PRIM)
   
    #add_if(application, continue_after_action_handler, G2_CALLBACKS_PRIM)
    add_if(application, class_selection_handler,       G2_CALLBACKS_PRIM)
    
    # ---- PVP ----
    application.add_handlers(pvp_handlers(), group=G2_CALLBACKS_PRIM)

    # --- INÍCIO DA ADIÇÃO DOS HANDLERS DE GUILDA/CLÃ ---
    add_if(application, guild_menu_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_menu_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_upgrade_menu_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_apply_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_manage_apps_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_app_accept_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_app_decline_handler, G2_CALLBACKS_PRIM)
    add_if(application, noop_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_search_conv_handler,   G0_CONVERSATIONS)
    add_if(application, clan_upgrade_confirm_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_leave_confirm_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_leave_do_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_manage_menu_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_kick_menu_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_kick_confirm_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_kick_do_handler, G2_CALLBACKS_PRIM)
    add_if(application, missions_menu_handler, G2_CALLBACKS_PRIM)
    add_if(application, mission_claim_handler, G2_CALLBACKS_PRIM)
    add_if(application, mission_reroll_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_bank_menu_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_deposit_conv_handler, G0_CONVERSATIONS)
    add_if(application, clan_withdraw_conv_handler, G0_CONVERSATIONS)
    add_if(application, clan_board_purchase_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_mission_start_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_mission_confirm_handler, G2_CALLBACKS_PRIM)
    add_if(application, clan_guild_mission_details_handler, G2_CALLBACKS_PRIM)
    
    # ✅ Forja e Coleta
    add_if(application, forge_handler,                 G2_CALLBACKS_PRIM)
    add_if(application, job_handler,                   G2_CALLBACKS_PRIM)

    add_if(application, craft_open_handler,            G2_CALLBACKS_PRIM)
    add_if(application, enhance_menu_handler,          G2_CALLBACKS_PRIM)
    add_if(application, enhance_select_handler,        G2_CALLBACKS_PRIM)
    add_if(application, enhance_action_handler,        G2_CALLBACKS_PRIM)

    add_if(application, job_menu_handler,              G2_CALLBACKS_PRIM)
    add_if(application, job_pick_handler,              G2_CALLBACKS_PRIM)

    add_if(application, market_open_handler,           G2_CALLBACKS_PRIM)
    add_if(application, market_adventurer_handler,     G2_CALLBACKS_PRIM)
    add_if(application, market_kingdom_handler,        G2_CALLBACKS_PRIM)
    add_if(application, kingdom_set_item_handler,      G2_CALLBACKS_PRIM)
    add_if(application, kingdom_qty_minus_handler,     G2_CALLBACKS_PRIM)
    add_if(application, kingdom_qty_plus_handler,      G2_CALLBACKS_PRIM)
    add_if(application, market_kingdom_buy_handler,    G2_CALLBACKS_PRIM)
    add_if(application, market_kingdom_buy_legacy_handler, G2_CALLBACKS_PRIM)
    add_if(application, market_list_handler,           G2_CALLBACKS_PRIM)
    add_if(application, market_my_handler,             G2_CALLBACKS_PRIM)
    add_if(application, market_sell_handler,           G2_CALLBACKS_PRIM)
    add_if(application, market_buy_handler,            G2_CALLBACKS_PRIM)
    add_if(application, market_cancel_handler,         G2_CALLBACKS_PRIM)
    add_if(application, market_pick_unique_handler,    G2_CALLBACKS_PRIM)
    add_if(application, market_pick_stack_handler,     G2_CALLBACKS_PRIM)
    add_if(application, market_qty_handler,            G2_CALLBACKS_PRIM)
    add_if(application, market_price_spin_handler,     G2_CALLBACKS_PRIM)
    add_if(application, market_price_confirm_handler,  G2_CALLBACKS_PRIM)
    add_if(application, market_cancel_new_handler,     G2_CALLBACKS_PRIM)

    # Região / Viagem / Durabilidade
    add_if(application, region_callback_handler,       G2_CALLBACKS_PRIM)
    #add_if(application, travel_callback_handler,       G2_CALLBACKS_PRIM)
    add_if(application, restore_durability_menu_handler, G2_CALLBACKS_PRIM)
    add_if(application, restore_durability_fix_handler,  G2_CALLBACKS_PRIM)
    # registra o handler de coleta (callback collect_<region>)
    add_if(application, collect_callback_handler,      G2_CALLBACKS_PRIM)
    add_if(application, continue_after_action_handler, G2_CALLBACKS_PRIM) # <-- NOVO
    add_if(application, kingdom_menu_handler, G2_CALLBACKS_PRIM)          # <-- NOVO
# ...
    # Refino
    add_if(application, refining_main_handler,         G2_CALLBACKS_PRIM)
    add_if(application, ref_select_handler,            G2_CALLBACKS_PRIM)
    add_if(application, ref_confirm_handler,           G2_CALLBACKS_PRIM)
    if refining_main_callback:
        application.add_handler(
            CallbackQueryHandler(
                refining_main_callback,
                pattern=r"^(ref_menu|refining_main|menu_refino|refino_main|open_refino)$",
            ),
            G2_CALLBACKS_PRIM,
        )

    # 🏰 Calabouço (runtime)
    add_if(application, dungeon_open_handler,          G2_CALLBACKS_PRIM)
    add_if(application, dungeon_pick_handler,          G2_CALLBACKS_PRIM)

    # G3 — COMANDOS
    if show_kingdom_menu:
        application.add_handler(CommandHandler("menu", show_kingdom_menu), G3_COMMANDS)
    if show_kingdom_menu:
        application.add_handler(CommandHandler("menu", show_kingdom_menu), G3_COMMANDS)

    # /start como comando explícito (não intercepta textos do nome)
    add_if(application, start_command_handler, G3_COMMANDS)
    
    # comando /gemas
    add_if(application, gem_shop_command_handler, G3_COMMANDS)

    # G5 — HANDLERS SECUNDÁRIOS (criação de personagem fica atrás)
    add_if(application, character_creation_handler,    G5_SECONDARY)
    add_if(application, name_command_handler,          G5_SECONDARY)

    
    # Party callbacks (baixíssima prioridade comparada às conversas)
    add_if(application, party_callback_handler,        G9_PARTY)
    add_if(application, chat_interaction_handler,      G15_CHAT_LISTENER)
    logging.info("Iniciando bot…")
    application.run_polling()


if __name__ == "__main__":
    main()
