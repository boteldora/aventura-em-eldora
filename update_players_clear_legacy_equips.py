# update_players_clear_legacy_equips.py
import os
import json
import shutil
from datetime import datetime

# === Ajuste se necessário ===
PLAYERS_DIR = "players"  # pasta onde ficam os .json dos jogadores

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def backup_players(src_dir: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_dir = f"{src_dir}_backup_{ts}"
    shutil.copytree(src_dir, dst_dir)
    return dst_dir

def is_unique_item_reference(value, inventory: dict) -> bool:
    """
    Um slot de equipamento válido aponta para uma chave (UUID string)
    cujo valor no inventário é um dict (instância única do item).
    """
    return isinstance(value, str) and isinstance(inventory.get(value), dict)

def main():
    if not os.path.isdir(PLAYERS_DIR):
        print(f"❌ Pasta '{PLAYERS_DIR}' não encontrada.")
        return

    # Backup automático
    backup_dir = backup_players(PLAYERS_DIR)
    print(f"📦 Backup criado em: {backup_dir}\n")

    total = 0
    changed = 0
    errors = 0

    for fn in os.listdir(PLAYERS_DIR):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(PLAYERS_DIR, fn)
        total += 1

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            errors += 1
            print(f"⚠️  Erro lendo {fn}: {e}")
            continue

        inv = data.get("inventory", {}) or {}
        eq = data.get("equipment", {}) or {}
        changed_this = False

        # Normaliza formato do 'equipment' se vier fora do padrão
        if not isinstance(eq, dict):
            eq = {}
            changed_this = True

        # Zera qualquer slot que não aponte para um item único válido
        for slot, val in list(eq.items()):
            if val and not is_unique_item_reference(val, inv):
                eq[slot] = None
                changed_this = True

        if changed_this:
            data["equipment"] = eq
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                changed += 1
                print(f"🧹 Corrigido: {fn}")
            except Exception as e:
                errors += 1
                print(f"❌ Erro salvando {fn}: {e}")

    print("\n== Resumo ==")
    print(f"Processados: {total}")
    print(f"Alterados:   {changed}")
    print(f"Com erro:    {errors}")
    print("✅ Concluído.")

if __name__ == "__main__":
    main()
