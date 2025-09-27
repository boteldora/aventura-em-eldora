# update_players.py
# Migração segura do schema dos saves em players/*.json

import argparse
import os
import json
from datetime import datetime, timezone
from typing import Tuple, Dict, Any

from modules.player_manager import (
    iter_players,
    save_player_data,
    PLAYERS_DIR,
    add_unique_item,
)

def backup_file(path: str, backup_root: str) -> None:
    os.makedirs(backup_root, exist_ok=True)
    base = os.path.basename(path)
    dst = os.path.join(backup_root, base)
    # não sobrescreve backup existente
    if not os.path.exists(dst):
        with open(path, "rb") as src, open(dst, "wb") as out:
            out.write(src.read())

def _ensure_equipment_slots(equipment: Dict[str, Any]) -> Dict[str, Any]:
    # slots padrão do projeto
    defaults = {
        "arma": None, "elmo": None, "armadura": None, "calca": None,
        "luvas": None, "botas": None, "anel": None, "colar": None, "brinco": None
    }
    if not isinstance(equipment, dict):
        return defaults
    for k, v in defaults.items():
        equipment.setdefault(k, v)
    # remove lixo inesperado
    for k in list(equipment.keys()):
        if k not in defaults:
            equipment.pop(k, None)
    return equipment

def _coerce_stack_qty(x) -> int:
    try:
        v = int(x)
    except Exception:
        v = 0
    return max(0, v)

def _migrate_schema_safe(user_id: int, data: dict) -> Tuple[dict, bool, list]:
    """
    Retorna (novo_data, changed, warnings)
    NUNCA altera player_state existente.
    """
    changed = False
    warnings = []

    # Campos-base
    if 'inventory' not in data or not isinstance(data['inventory'], dict):
        data['inventory'] = {}
        changed = True

    if 'equipment' not in data or not isinstance(data['equipment'], dict):
        data['equipment'] = {}
        changed = True
    data['equipment'] = _ensure_equipment_slots(data['equipment'])

    if 'profession' not in data or not isinstance(data['profession'], dict):
        data['profession'] = {}
        changed = True

    if 'max_energy' not in data:
        data['max_energy'] = 20; changed = True
    if 'energy' not in data:
        data['energy'] = data.get('max_energy', 20); changed = True

    # Estado do jogador — só cria se faltar
    if 'player_state' not in data or not isinstance(data['player_state'], dict):
        data['player_state'] = {'action': 'idle'}
        changed = True

    # Premium legado -> novo
    if data.get('is_premium'):
        if not data.get('premium_tier'):
            data['premium_tier'] = 'premium'
            changed = True
        data.pop('is_premium', None)
        changed = True

    # premium_expires_at sem tz -> UTC
    exp = data.get('premium_expires_at')
    if exp:
        try:
            dt = datetime.fromisoformat(exp)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
                data['premium_expires_at'] = dt.isoformat()
                changed = True
        except Exception:
            warnings.append(f"{user_id}: premium_expires_at inválido, removendo")
            data['premium_expires_at'] = None
            data['premium_tier'] = None
            changed = True

    # Normaliza inventário empilhável
    inv = data.get('inventory', {})
    for key in list(inv.keys()):
        val = inv[key]
        if isinstance(val, dict):
            # item único — ok
            continue
        # empilhável → int >= 0; zera/lixo remove
        qty = _coerce_stack_qty(val)
        if qty <= 0:
            inv.pop(key, None)
            changed = True
        else:
            if qty != val:
                inv[key] = qty
                changed = True

    # Corrige slots que guardam objeto ao invés de unique_id
    # Se encontrar dict no slot, move para inventory como item único e coloca o uuid no slot
    for slot, ref in list(data['equipment'].items()):
        if isinstance(ref, dict) and ref:
            # mover este objeto pro inventário como único
            unique_id = add_unique_item(data, ref)
            data['equipment'][slot] = unique_id
            changed = True
        elif isinstance(ref, str):
            # se aponta para unique_id mas não existe no inventário, registra aviso
            if ref not in inv:
                warnings.append(f"{user_id}: slot '{slot}' aponta para '{ref}' inexistente no inventário")
        elif ref is None:
            pass
        else:
            # tipo inesperado — limpa slot
            data['equipment'][slot] = None
            changed = True

    return data, changed, warnings

def main():
    parser = argparse.ArgumentParser(description="Migra saves dos jogadores com segurança.")
    parser.add_argument("--players-dir", default=PLAYERS_DIR, help="Pasta dos saves (default: players)")
    parser.add_argument("--backup", action="store_true", default=True, help="Cria backup antes de escrever (default: on)")
    parser.add_argument("--no-backup", dest="backup", action="store_false", help="Não criar backup")
    parser.add_argument("--apply", action="store_true", help="Aplicar mudanças (por padrão é dry-run)")
    args = parser.parse_args()

    # Garante diretório
    os.makedirs(args.players_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(args.players_dir, f"_backup_{ts}")

    total = 0
    changed_n = 0
    warnings_all = []

    print(f"== Migração de jogadores ==")
    print(f"Diretório: {args.players_dir}")
    print(f"Backup: {'ON' if args.backup else 'OFF'}")
    print(f"Modo: {'APPLY' if args.apply else 'DRY-RUN'}\n")

    for user_id, pdata in iter_players():
        total += 1
        before = json.dumps(pdata, sort_keys=True, ensure_ascii=False)
        new_data, changed, warns = _migrate_schema_safe(user_id, pdata)
        after = json.dumps(new_data, sort_keys=True, ensure_ascii=False)

        if warns:
            warnings_all.extend(warns)

        if changed and before != after:
            changed_n += 1
            print(f"- {user_id}: mudanças detectadas.")
            if args.apply:
                # backup
                if args.backup:
                    backup_file(os.path.join(args.players_dir, f"{user_id}.json"), backup_root)
                # salvar atômico
                save_player_data(user_id, new_data)
        else:
            print(f"- {user_id}: ok (sem alterações).")

    print(f"\nConcluído. Processados: {total}, alterados: {changed_n}.")
    if warnings_all:
        print("\nAvisos:")
        for w in warnings_all:
            print(f"  • {w}")

if __name__ == "__main__":
    main()
