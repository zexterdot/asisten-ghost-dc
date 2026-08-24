"""
game_data.py — Semua data game (classes, monsters, items, pets, trivia)
Ghost Assistant RPG System
"""

import random

# ==================== CLASSES ====================

CLASSES = {
    "warrior": {
        "name": "Warrior",
        "emoji": "⚔️",
        "description": "Tank tangguh dengan HP dan DEF tinggi. Cocok untuk pemula.",
        "base_hp": 150,
        "base_atk": 12,
        "base_def": 15,
        "base_spd": 8,
        "base_crit": 0.05,
        "level_bonus": {"hp": 8, "atk": 1, "def": 2, "spd": 0, "crit": 0.0},
    },
    "mage": {
        "name": "Mage",
        "emoji": "🔮",
        "description": "Glass cannon dengan damage besar tapi pertahanan lemah.",
        "base_hp": 90,
        "base_atk": 18,
        "base_def": 7,
        "base_spd": 12,
        "base_crit": 0.10,
        "level_bonus": {"hp": 4, "atk": 3, "def": 0, "spd": 1, "crit": 0.005},
    },
    "assassin": {
        "name": "Assassin",
        "emoji": "🗡️",
        "description": "Cepat dan mematikan. Fokus critical hit untuk burst damage.",
        "base_hp": 100,
        "base_atk": 15,
        "base_def": 8,
        "base_spd": 18,
        "base_crit": 0.20,
        "level_bonus": {"hp": 5, "atk": 2, "def": 0, "spd": 2, "crit": 0.005},
    },
    "archer": {
        "name": "Archer",
        "emoji": "🏹",
        "description": "Balanced fighter dengan damage konsisten dan mobilitas baik.",
        "base_hp": 110,
        "base_atk": 14,
        "base_def": 10,
        "base_spd": 14,
        "base_crit": 0.12,
        "level_bonus": {"hp": 6, "atk": 2, "def": 1, "spd": 1, "crit": 0.003},
    },
}


# ==================== MONSTERS ====================

# Monsters organized by floor ranges
MONSTERS = {
    # Floor 1-5: Hutan Pemula
    (1, 5): [
        {
            "id": "serigala", "name": "Serigala Liar", "emoji": "🐺",
            "hp": 40, "atk": 8, "def": 3, "spd": 7,
            "coins": (5, 10), "xp": (10, 15),
            "loot": [("leather_scrap", 0.4), ("potion_hp", 0.15)],
        },
        {
            "id": "laba_laba", "name": "Laba-laba Raksasa", "emoji": "🕷️",
            "hp": 35, "atk": 10, "def": 2, "spd": 9,
            "coins": (5, 10), "xp": (10, 15),
            "loot": [("spider_silk", 0.4), ("potion_hp", 0.15)],
        },
        {
            "id": "babi_hutan", "name": "Babi Hutan", "emoji": "🐗",
            "hp": 55, "atk": 7, "def": 5, "spd": 5,
            "coins": (8, 12), "xp": (12, 18),
            "loot": [("raw_meat", 0.5), ("leather_scrap", 0.2)],
        },
        {
            "id": "skeleton_lemah", "name": "Skeleton Lemah", "emoji": "💀",
            "hp": 45, "atk": 9, "def": 4, "spd": 6,
            "coins": (8, 12), "xp": (12, 18),
            "loot": [("bone_fragment", 0.4), ("sword_wood", 0.05)],
        },
    ],
    # Floor 6-10: Gua Gelap
    (6, 10): [
        {
            "id": "kelelawar", "name": "Kelelawar Vampir", "emoji": "🦇",
            "hp": 50, "atk": 12, "def": 4, "spd": 14,
            "coins": (10, 15), "xp": (15, 20),
            "loot": [("bat_wing", 0.4), ("potion_hp", 0.2)],
        },
        {
            "id": "ular", "name": "Ular Beracun", "emoji": "🐍",
            "hp": 45, "atk": 14, "def": 3, "spd": 12,
            "coins": (10, 15), "xp": (15, 20),
            "loot": [("venom_sac", 0.4), ("ring_speed", 0.03)],
        },
        {
            "id": "zombie", "name": "Zombie", "emoji": "🧟",
            "hp": 70, "atk": 11, "def": 6, "spd": 4,
            "coins": (12, 18), "xp": (18, 25),
            "loot": [("rotten_cloth", 0.4), ("armor_leather", 0.05)],
        },
        {
            "id": "hantu", "name": "Hantu Penasaran", "emoji": "👻",
            "hp": 40, "atk": 16, "def": 2, "spd": 16,
            "coins": (15, 20), "xp": (20, 28),
            "loot": [("ectoplasm", 0.4), ("amulet_crit", 0.02)],
        },
    ],
    # Floor 11-20: Kastil Tua
    (11, 20): [
        {
            "id": "dark_knight", "name": "Dark Knight", "emoji": "🧟‍♂️",
            "hp": 90, "atk": 18, "def": 10, "spd": 8,
            "coins": (15, 25), "xp": (25, 35),
            "loot": [("dark_shard", 0.3), ("sword_iron", 0.08), ("armor_iron", 0.05)],
        },
        {
            "id": "evil_mage", "name": "Evil Mage", "emoji": "🧙‍♂️",
            "hp": 60, "atk": 24, "def": 5, "spd": 13,
            "coins": (18, 28), "xp": (28, 38),
            "loot": [("magic_dust", 0.3), ("potion_atk", 0.08)],
        },
        {
            "id": "scorpion", "name": "Scorpion King", "emoji": "🦂",
            "hp": 80, "atk": 20, "def": 12, "spd": 10,
            "coins": (18, 28), "xp": (28, 38),
            "loot": [("scorpion_tail", 0.3), ("armor_dark", 0.03)],
        },
        {
            "id": "golem", "name": "Stone Golem", "emoji": "🗿",
            "hp": 120, "atk": 16, "def": 18, "spd": 3,
            "coins": (20, 30), "xp": (30, 40),
            "loot": [("stone_core", 0.3), ("ring_def", 0.05)],
        },
    ],
    # Floor 21-35: Gurun Terkutuk
    (21, 35): [
        {
            "id": "sand_worm", "name": "Cacing Pasir", "emoji": "🪱",
            "hp": 130, "atk": 25, "def": 14, "spd": 11,
            "coins": (25, 40), "xp": (35, 50),
            "loot": [("sand_crystal", 0.25), ("sword_fire", 0.04)],
        },
        {
            "id": "mummy", "name": "Mummy Kuno", "emoji": "🧟",
            "hp": 110, "atk": 28, "def": 10, "spd": 7,
            "coins": (25, 40), "xp": (35, 50),
            "loot": [("ancient_bandage", 0.25), ("amulet_hp", 0.05)],
        },
        {
            "id": "djinn", "name": "Djinn Api", "emoji": "🧞",
            "hp": 95, "atk": 32, "def": 8, "spd": 18,
            "coins": (30, 45), "xp": (40, 55),
            "loot": [("fire_essence", 0.2), ("sword_fire", 0.06)],
        },
    ],
    # Floor 36-50: Neraka
    (36, 50): [
        {
            "id": "demon_soldier", "name": "Prajurit Iblis", "emoji": "👹",
            "hp": 180, "atk": 35, "def": 20, "spd": 14,
            "coins": (40, 60), "xp": (50, 70),
            "loot": [("demon_horn", 0.2), ("armor_dragon", 0.03)],
        },
        {
            "id": "hell_hound", "name": "Anjing Neraka", "emoji": "🔥",
            "hp": 150, "atk": 40, "def": 15, "spd": 22,
            "coins": (40, 60), "xp": (50, 70),
            "loot": [("hellfire_fang", 0.2), ("ring_crit", 0.04)],
        },
        {
            "id": "fallen_angel", "name": "Malaikat Jatuh", "emoji": "😈",
            "hp": 160, "atk": 38, "def": 18, "spd": 20,
            "coins": (45, 70), "xp": (55, 80),
            "loot": [("fallen_feather", 0.15), ("sword_dragon", 0.02)],
        },
    ],
}

# Boss monsters (every 5 floors)
BOSSES = {
    5: {
        "id": "boss_bear", "name": "Beruang Alpha", "emoji": "🐻",
        "hp": 150, "atk": 15, "def": 8, "spd": 6,
        "coins": (30, 50), "xp": (50, 80),
        "loot": [("bear_claw", 1.0), ("armor_leather", 0.3), ("potion_hp_big", 0.5)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_bear.png",
    },
    10: {
        "id": "boss_dragon_young", "name": "Naga Muda", "emoji": "🐉",
        "hp": 250, "atk": 22, "def": 12, "spd": 10,
        "coins": (60, 100), "xp": (100, 150),
        "loot": [("dragon_scale", 1.0), ("sword_fire", 0.3), ("potion_atk", 0.4)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_dragon_young.png",
    },
    15: {
        "id": "boss_lich", "name": "Lich King", "emoji": "💀",
        "hp": 350, "atk": 28, "def": 15, "spd": 12,
        "coins": (90, 150), "xp": (150, 220),
        "loot": [("lich_crown", 1.0), ("armor_dark", 0.3), ("amulet_crit", 0.2)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_lich.png",
    },
    20: {
        "id": "boss_demon", "name": "Demon Lord", "emoji": "👹",
        "hp": 400, "atk": 30, "def": 18, "spd": 14,
        "coins": (120, 200), "xp": (200, 300),
        "loot": [("demon_core", 1.0), ("sword_dragon", 0.15), ("armor_dragon", 0.1)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_demon.png",
    },
    25: {
        "id": "boss_sphinx", "name": "Sphinx Agung", "emoji": "🦁",
        "hp": 500, "atk": 35, "def": 22, "spd": 16,
        "coins": (150, 250), "xp": (250, 380),
        "loot": [("sphinx_riddle", 1.0), ("ring_legend", 0.1)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_sphinx.png",
    },
    30: {
        "id": "boss_hydra", "name": "Hydra", "emoji": "🐍",
        "hp": 650, "atk": 38, "def": 25, "spd": 12,
        "coins": (180, 300), "xp": (300, 450),
        "loot": [("hydra_fang", 1.0), ("armor_legend", 0.08)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_hydra.png",
    },
    35: {
        "id": "boss_phoenix", "name": "Phoenix Abadi", "emoji": "🔥",
        "hp": 550, "atk": 42, "def": 20, "spd": 25,
        "coins": (200, 350), "xp": (350, 520),
        "loot": [("phoenix_feather", 1.0), ("sword_legend", 0.06)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_phoenix.png",
    },
    40: {
        "id": "boss_titan", "name": "Titan Batu", "emoji": "🗿",
        "hp": 900, "atk": 45, "def": 35, "spd": 5,
        "coins": (250, 400), "xp": (400, 600),
        "loot": [("titan_heart", 1.0), ("armor_legend", 0.1)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_titan.png",
    },
    45: {
        "id": "boss_shadow", "name": "Shadow Emperor", "emoji": "👤",
        "hp": 800, "atk": 50, "def": 28, "spd": 22,
        "coins": (300, 500), "xp": (500, 750),
        "loot": [("shadow_essence", 1.0), ("sword_legend", 0.1), ("ring_legend", 0.08)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_shadow.png",
    },
    50: {
        "id": "boss_dragon_ancient", "name": "Naga Purba", "emoji": "🐲",
        "hp": 1200, "atk": 55, "def": 35, "spd": 18,
        "coins": (500, 800), "xp": (800, 1200),
        "loot": [("dragon_heart", 1.0), ("sword_legend", 0.2), ("armor_legend", 0.15), ("ring_legend", 0.15)],
        "image": "https://raw.githubusercontent.com/zexterdot/asisten-ghost-dc/main/images/boss_dragon_ancient.png",
    },
}

# Zone names for flavor text
ZONE_NAMES = {
    (1, 5): "🌲 Hutan Pemula",
    (6, 10): "🕳️ Gua Gelap",
    (11, 20): "🏰 Kastil Tua",
    (21, 35): "🏜️ Gurun Terkutuk",
    (36, 50): "🔥 Neraka",
}


def get_zone_name(floor: int) -> str:
    """Get the zone name for a given floor."""
    for (low, high), name in ZONE_NAMES.items():
        if low <= floor <= high:
            return name
    return "❓ Zona Tidak Dikenal"


def get_random_monster(floor: int) -> dict:
    """Get a random monster for the given floor with scaled stats."""
    # Find the appropriate monster pool
    monster_pool = None
    for (low, high), monsters in MONSTERS.items():
        if low <= floor <= high:
            monster_pool = monsters
            break

    if not monster_pool:
        # Use the highest floor monsters for floors > 50
        monster_pool = MONSTERS[(36, 50)]

    base_monster = random.choice(monster_pool).copy()

    # Scale stats based on floor (10% increase per floor above base)
    for (low, _), _ in MONSTERS.items():
        if low <= floor:
            base_floor = low
    scale = 1 + (floor - base_floor) * 0.08

    base_monster["hp"] = int(base_monster["hp"] * scale)
    base_monster["atk"] = int(base_monster["atk"] * scale)
    base_monster["def"] = int(base_monster["def"] * scale)

    return base_monster


def get_boss(floor: int) -> dict | None:
    """Get boss for the given floor. Returns None if no boss at this floor."""
    return BOSSES.get(floor)


# ==================== ITEMS & EQUIPMENT ====================

# Item types: weapon, armor, accessory, consumable, material
ITEMS = {
    # --- Materials (drop dari monster, bisa dijual) ---
    "leather_scrap": {
        "name": "Leather Scrap", "emoji": "🧶", "type": "material",
        "rarity": "common", "sell_price": 3,
        "description": "Potongan kulit dari monster.",
    },
    "spider_silk": {
        "name": "Spider Silk", "emoji": "🕸️", "type": "material",
        "rarity": "common", "sell_price": 3,
        "description": "Sutra laba-laba yang kuat.",
    },
    "raw_meat": {
        "name": "Raw Meat", "emoji": "🥩", "type": "material",
        "rarity": "common", "sell_price": 2,
        "description": "Daging mentah. Bisa dijual.",
    },
    "bone_fragment": {
        "name": "Bone Fragment", "emoji": "🦴", "type": "material",
        "rarity": "common", "sell_price": 3,
        "description": "Pecahan tulang monster.",
    },
    "bat_wing": {
        "name": "Bat Wing", "emoji": "🦇", "type": "material",
        "rarity": "common", "sell_price": 5,
        "description": "Sayap kelelawar.",
    },
    "venom_sac": {
        "name": "Venom Sac", "emoji": "☠️", "type": "material",
        "rarity": "uncommon", "sell_price": 8,
        "description": "Kantung racun ular.",
    },
    "rotten_cloth": {
        "name": "Rotten Cloth", "emoji": "🧣", "type": "material",
        "rarity": "common", "sell_price": 4,
        "description": "Kain lapuk dari zombie.",
    },
    "ectoplasm": {
        "name": "Ectoplasm", "emoji": "💧", "type": "material",
        "rarity": "uncommon", "sell_price": 10,
        "description": "Substansi spiritual dari hantu.",
    },
    "dark_shard": {
        "name": "Dark Shard", "emoji": "🖤", "type": "material",
        "rarity": "uncommon", "sell_price": 12,
        "description": "Pecahan kegelapan.",
    },
    "magic_dust": {
        "name": "Magic Dust", "emoji": "✨", "type": "material",
        "rarity": "uncommon", "sell_price": 15,
        "description": "Debu sihir yang berkilau.",
    },
    "scorpion_tail": {
        "name": "Scorpion Tail", "emoji": "🦂", "type": "material",
        "rarity": "uncommon", "sell_price": 12,
        "description": "Ekor kalajengking beracun.",
    },
    "stone_core": {
        "name": "Stone Core", "emoji": "💎", "type": "material",
        "rarity": "rare", "sell_price": 20,
        "description": "Inti batu golem.",
    },
    "sand_crystal": {
        "name": "Sand Crystal", "emoji": "🔶", "type": "material",
        "rarity": "rare", "sell_price": 25,
        "description": "Kristal pasir langka.",
    },
    "ancient_bandage": {
        "name": "Ancient Bandage", "emoji": "🩹", "type": "material",
        "rarity": "rare", "sell_price": 22,
        "description": "Perban kuno dari mummy.",
    },
    "fire_essence": {
        "name": "Fire Essence", "emoji": "🔥", "type": "material",
        "rarity": "rare", "sell_price": 30,
        "description": "Esensi api murni.",
    },
    "demon_horn": {
        "name": "Demon Horn", "emoji": "👹", "type": "material",
        "rarity": "epic", "sell_price": 50,
        "description": "Tanduk iblis yang kuat.",
    },
    "hellfire_fang": {
        "name": "Hellfire Fang", "emoji": "🔥", "type": "material",
        "rarity": "epic", "sell_price": 55,
        "description": "Taring api neraka.",
    },
    "fallen_feather": {
        "name": "Fallen Feather", "emoji": "🪶", "type": "material",
        "rarity": "epic", "sell_price": 60,
        "description": "Bulu malaikat yang jatuh.",
    },
    # Boss materials
    "bear_claw": {
        "name": "Bear Claw", "emoji": "🐻", "type": "material",
        "rarity": "rare", "sell_price": 30,
        "description": "Cakar beruang alpha.",
    },
    "dragon_scale": {
        "name": "Dragon Scale", "emoji": "🐉", "type": "material",
        "rarity": "epic", "sell_price": 80,
        "description": "Sisik naga yang sangat kuat.",
    },
    "lich_crown": {
        "name": "Lich Crown", "emoji": "👑", "type": "material",
        "rarity": "epic", "sell_price": 100,
        "description": "Mahkota Lich King.",
    },
    "demon_core": {
        "name": "Demon Core", "emoji": "💜", "type": "material",
        "rarity": "epic", "sell_price": 120,
        "description": "Inti kekuatan Demon Lord.",
    },
    "sphinx_riddle": {
        "name": "Sphinx Riddle", "emoji": "📜", "type": "material",
        "rarity": "legendary", "sell_price": 150,
        "description": "Teka-teki Sphinx yang terpecahkan.",
    },
    "hydra_fang": {
        "name": "Hydra Fang", "emoji": "🐍", "type": "material",
        "rarity": "legendary", "sell_price": 180,
        "description": "Taring Hydra berkepala banyak.",
    },
    "phoenix_feather": {
        "name": "Phoenix Feather", "emoji": "🔥", "type": "material",
        "rarity": "legendary", "sell_price": 200,
        "description": "Bulu Phoenix yang tak pernah padam.",
    },
    "titan_heart": {
        "name": "Titan Heart", "emoji": "❤️‍🔥", "type": "material",
        "rarity": "legendary", "sell_price": 250,
        "description": "Jantung Titan yang membatu.",
    },
    "shadow_essence": {
        "name": "Shadow Essence", "emoji": "🌑", "type": "material",
        "rarity": "legendary", "sell_price": 300,
        "description": "Esensi bayangan murni.",
    },
    "dragon_heart": {
        "name": "Dragon Heart", "emoji": "🐲", "type": "material",
        "rarity": "legendary", "sell_price": 500,
        "description": "Jantung Naga Purba. Item terlangka.",
    },

    # --- Consumables ---
    "potion_hp": {
        "name": "Health Potion", "emoji": "❤️", "type": "consumable",
        "rarity": "common", "buy_price": 25, "sell_price": 10,
        "description": "Memulihkan 50 HP.",
        "effect": {"heal": 50},
    },
    "potion_hp_big": {
        "name": "Health Potion XL", "emoji": "💖", "type": "consumable",
        "rarity": "uncommon", "buy_price": 80, "sell_price": 35,
        "description": "Memulihkan 150 HP.",
        "effect": {"heal": 150},
    },
    "potion_hp_mega": {
        "name": "Mega Health Potion", "emoji": "💗", "type": "consumable",
        "rarity": "rare", "buy_price": 200, "sell_price": 90,
        "description": "Memulihkan 500 HP.",
        "effect": {"heal": 500},
    },
    "potion_atk": {
        "name": "ATK Boost Potion", "emoji": "⚔️", "type": "consumable",
        "rarity": "rare", "buy_price": 150, "sell_price": 65,
        "description": "Meningkatkan ATK +10 selama 3 battle.",
        "effect": {"atk_boost": 10, "duration": 3},
    },

    # --- Weapons ---
    "sword_wood": {
        "name": "Pedang Kayu", "emoji": "🪵", "type": "weapon",
        "rarity": "common", "buy_price": 50, "sell_price": 20,
        "description": "Pedang kayu sederhana. Lebih baik dari tangan kosong.",
        "stats": {"atk": 3},
    },
    "sword_iron": {
        "name": "Pedang Besi", "emoji": "⚔️", "type": "weapon",
        "rarity": "uncommon", "buy_price": 200, "sell_price": 85,
        "description": "Pedang besi yang cukup tajam.",
        "stats": {"atk": 6},
    },
    "sword_fire": {
        "name": "Pedang Api", "emoji": "🔥", "type": "weapon",
        "rarity": "rare", "buy_price": 800, "sell_price": 350,
        "description": "Pedang yang terbakar api abadi.",
        "stats": {"atk": 10, "crit": 0.03},
    },
    "sword_dragon": {
        "name": "Dragon Slayer", "emoji": "🐉", "type": "weapon",
        "rarity": "epic", "sell_price": 800,
        "description": "Pedang legendaris pembunuh naga.",
        "stats": {"atk": 18, "crit": 0.05},
    },
    "sword_legend": {
        "name": "Excalibur", "emoji": "✨", "type": "weapon",
        "rarity": "legendary", "sell_price": 2000,
        "description": "Pedang suci terkuat yang pernah ada.",
        "stats": {"atk": 30, "crit": 0.08, "spd": 5},
    },

    # --- Armor ---
    "armor_leather": {
        "name": "Armor Kulit", "emoji": "🧥", "type": "armor",
        "rarity": "common", "buy_price": 50, "sell_price": 20,
        "description": "Armor kulit ringan.",
        "stats": {"def": 3, "hp": 10},
    },
    "armor_iron": {
        "name": "Armor Besi", "emoji": "🛡️", "type": "armor",
        "rarity": "uncommon", "buy_price": 200, "sell_price": 85,
        "description": "Armor besi yang kokoh.",
        "stats": {"def": 6, "hp": 20},
    },
    "armor_dark": {
        "name": "Dark Armor", "emoji": "🖤", "type": "armor",
        "rarity": "rare", "buy_price": 800, "sell_price": 350,
        "description": "Armor gelap yang menyerap serangan.",
        "stats": {"def": 12, "hp": 40},
    },
    "armor_dragon": {
        "name": "Dragon Armor", "emoji": "🐲", "type": "armor",
        "rarity": "epic", "sell_price": 900,
        "description": "Armor dari sisik naga yang hampir tak bisa ditembus.",
        "stats": {"def": 20, "hp": 60},
    },
    "armor_legend": {
        "name": "Armor of Gods", "emoji": "👼", "type": "armor",
        "rarity": "legendary", "sell_price": 2500,
        "description": "Armor dewa yang memberikan perlindungan absolut.",
        "stats": {"def": 35, "hp": 100, "spd": 3},
    },

    # --- Accessories ---
    "ring_speed": {
        "name": "Ring of Speed", "emoji": "💍", "type": "accessory",
        "rarity": "uncommon", "buy_price": 300, "sell_price": 130,
        "description": "Cincin yang meningkatkan kecepatan.",
        "stats": {"spd": 5},
    },
    "ring_def": {
        "name": "Ring of Defense", "emoji": "💍", "type": "accessory",
        "rarity": "uncommon", "buy_price": 300, "sell_price": 130,
        "description": "Cincin pelindung.",
        "stats": {"def": 5},
    },
    "ring_crit": {
        "name": "Ring of Critical", "emoji": "💍", "type": "accessory",
        "rarity": "rare", "buy_price": 600, "sell_price": 260,
        "description": "Cincin yang meningkatkan peluang critical.",
        "stats": {"crit": 0.08},
    },
    "ring_legend": {
        "name": "Ring of Eternity", "emoji": "💫", "type": "accessory",
        "rarity": "legendary", "sell_price": 1500,
        "description": "Cincin abadi dari dimensi lain.",
        "stats": {"atk": 10, "def": 10, "spd": 10, "crit": 0.05},
    },
    "amulet_crit": {
        "name": "Amulet of Critical", "emoji": "📿", "type": "accessory",
        "rarity": "rare", "buy_price": 900, "sell_price": 400,
        "description": "Amulet yang meningkatkan critical hit.",
        "stats": {"crit": 0.08, "atk": 3},
    },
    "amulet_hp": {
        "name": "Amulet of Vitality", "emoji": "📿", "type": "accessory",
        "rarity": "rare", "buy_price": 700, "sell_price": 300,
        "description": "Amulet yang meningkatkan vitalitas.",
        "stats": {"hp": 50, "def": 3},
    },
}

# Shop items (only items with buy_price)
SHOP_ITEMS = {k: v for k, v in ITEMS.items() if "buy_price" in v}

# Rarity colors for embeds
RARITY_COLORS = {
    "common": 0x969696,
    "uncommon": 0x2ECC71,
    "rare": 0x3498DB,
    "epic": 0x9B59B6,
    "legendary": 0xF39C12,
}

RARITY_EMOJI = {
    "common": "⬜",
    "uncommon": "🟩",
    "rare": "🟦",
    "epic": "🟪",
    "legendary": "🟧",
}


# ==================== PETS ====================

PETS = {
    "pet_cat": {
        "name": "Kucing Biasa", "emoji": "🐱", "rarity": "common",
        "description": "Kucing manis yang suka bertarung.",
        "bonus": {"atk": 2}, "gacha_rate": 0.25,
        "level_bonus": {"atk": 1},
    },
    "pet_dog": {
        "name": "Anjing Setia", "emoji": "🐕", "rarity": "common",
        "description": "Anjing yang setia melindungi tuannya.",
        "bonus": {"def": 2}, "gacha_rate": 0.25,
        "level_bonus": {"def": 1},
    },
    "pet_rabbit": {
        "name": "Kelinci Cepat", "emoji": "🐰", "rarity": "common",
        "description": "Kelinci yang sangat cepat.",
        "bonus": {"spd": 3}, "gacha_rate": 0.18,
        "level_bonus": {"spd": 1},
    },
    "pet_hamster": {
        "name": "Hamster Lucu", "emoji": "🐹", "rarity": "common",
        "description": "Hamster kecil yang menggemaskan.",
        "bonus": {"hp": 15}, "gacha_rate": 0.12,
        "level_bonus": {"hp": 5},
    },
    "pet_owl": {
        "name": "Burung Hantu", "emoji": "🦉", "rarity": "uncommon",
        "description": "Burung hantu bijak yang membantu dalam pertempuran.",
        "bonus": {"atk": 5, "spd": 2}, "gacha_rate": 0.07,
        "level_bonus": {"atk": 2, "spd": 1},
    },
    "pet_wolf": {
        "name": "Serigala", "emoji": "🐺", "rarity": "uncommon",
        "description": "Serigala liar yang telah dijinakkan.",
        "bonus": {"atk": 4, "def": 3}, "gacha_rate": 0.05,
        "level_bonus": {"atk": 1, "def": 1},
    },
    "pet_fox": {
        "name": "Rubah Licik", "emoji": "🦊", "rarity": "uncommon",
        "description": "Rubah cerdik yang suka menipu musuh.",
        "bonus": {"spd": 5, "crit": 0.03}, "gacha_rate": 0.04,
        "level_bonus": {"spd": 2},
    },
    "pet_eagle": {
        "name": "Elang Emas", "emoji": "🦅", "rarity": "rare",
        "description": "Elang emas yang menukik dari langit.",
        "bonus": {"atk": 8, "spd": 5}, "gacha_rate": 0.02,
        "level_bonus": {"atk": 3, "spd": 2},
    },
    "pet_tiger": {
        "name": "Harimau Putih", "emoji": "🐅", "rarity": "rare",
        "description": "Harimau putih langka dan kuat.",
        "bonus": {"atk": 7, "def": 5, "crit": 0.03}, "gacha_rate": 0.012,
        "level_bonus": {"atk": 2, "def": 2},
    },
    "pet_dragon_baby": {
        "name": "Baby Dragon", "emoji": "🐲", "rarity": "rare",
        "description": "Naga kecil yang baru menetas. Penuh potensi!",
        "bonus": {"atk": 10, "def": 5}, "gacha_rate": 0.008,
        "level_bonus": {"atk": 3, "def": 2},
    },
    "pet_cerberus": {
        "name": "Cerberus", "emoji": "🐕‍🦺", "rarity": "epic",
        "description": "Anjing berkepala tiga penjaga neraka.",
        "bonus": {"atk": 12, "def": 8, "hp": 30}, "gacha_rate": 0.003,
        "level_bonus": {"atk": 4, "def": 3, "hp": 10},
    },
    "pet_phoenix": {
        "name": "Phoenix", "emoji": "🔥", "rarity": "epic",
        "description": "Burung api yang bisa bangkit dari kematian.",
        "bonus": {"atk": 12, "spd": 8}, "gacha_rate": 0.002,
        "level_bonus": {"atk": 4, "spd": 3},
        "special": "auto_revive",  # Revive once per battle with 30% HP
    },
    "pet_unicorn": {
        "name": "Unicorn", "emoji": "🦄", "rarity": "legendary",
        "description": "Unicorn legendaris yang menyembuhkan tuannya.",
        "bonus": {"atk": 15, "def": 10, "hp": 50}, "gacha_rate": 0.001,
        "level_bonus": {"atk": 5, "def": 3, "hp": 15},
        "special": "heal_per_turn",  # Heal 10% max HP per turn
    },
}

GACHA_COST = 100
GACHA_10_COST = 900  # 10% discount


def do_gacha() -> str:
    """Perform a single gacha pull. Returns pet_id."""
    roll = random.random()
    cumulative = 0.0

    for pet_id, pet in PETS.items():
        cumulative += pet["gacha_rate"]
        if roll <= cumulative:
            return pet_id

    # Fallback to common pet
    return "pet_cat"


# ==================== TRIVIA QUESTIONS ====================

TRIVIA_QUESTIONS = [
    {
        "question": "Apa ibu kota Indonesia?",
        "options": ["Jakarta", "Bandung", "Surabaya", "Nusantara"],
        "answer": 0,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Planet terbesar di tata surya adalah?",
        "options": ["Mars", "Jupiter", "Saturnus", "Neptunus"],
        "answer": 1,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Berapa jumlah provinsi di Indonesia (2024)?",
        "options": ["34", "37", "38", "36"],
        "answer": 2,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Siapa presiden pertama Indonesia?",
        "options": ["Soekarno", "Soeharto", "Habibie", "Megawati"],
        "answer": 0,
        "category": "📚 Sejarah",
    },
    {
        "question": "Gunung tertinggi di dunia adalah?",
        "options": ["K2", "Kilimanjaro", "Everest", "Denali"],
        "answer": 2,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Bahasa pemrograman apa yang dibuat oleh Guido van Rossum?",
        "options": ["Java", "C++", "Python", "Ruby"],
        "answer": 2,
        "category": "💻 Teknologi",
    },
    {
        "question": "Anime 'Naruto' dibuat oleh siapa?",
        "options": ["Eiichiro Oda", "Masashi Kishimoto", "Akira Toriyama", "Tite Kubo"],
        "answer": 1,
        "category": "🎌 Anime",
    },
    {
        "question": "Apa nama mata uang Jepang?",
        "options": ["Won", "Yen", "Yuan", "Baht"],
        "answer": 1,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Game 'Minecraft' dibuat oleh siapa?",
        "options": ["Notch (Markus Persson)", "Gabe Newell", "Shigeru Miyamoto", "John Carmack"],
        "answer": 0,
        "category": "🎮 Gaming",
    },
    {
        "question": "Berapa hasil dari 15 × 15?",
        "options": ["200", "215", "225", "250"],
        "answer": 2,
        "category": "🔢 Matematika",
    },
    {
        "question": "Hewan apa yang dikenal sebagai 'Raja Hutan'?",
        "options": ["Harimau", "Singa", "Beruang", "Serigala"],
        "answer": 1,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Pulau terbesar di Indonesia adalah?",
        "options": ["Sumatera", "Jawa", "Kalimantan", "Papua"],
        "answer": 2,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "One Piece dimulai serialisasi tahun berapa?",
        "options": ["1995", "1997", "1999", "2001"],
        "answer": 1,
        "category": "🎌 Anime",
    },
    {
        "question": "Siapa CEO Tesla?",
        "options": ["Jeff Bezos", "Bill Gates", "Elon Musk", "Mark Zuckerberg"],
        "answer": 2,
        "category": "💻 Teknologi",
    },
    {
        "question": "Candi Borobudur terletak di provinsi?",
        "options": ["Jawa Timur", "Jawa Tengah", "DIY Yogyakarta", "Jawa Barat"],
        "answer": 1,
        "category": "📚 Sejarah",
    },
    {
        "question": "Berapa jumlah pemain dalam satu tim sepak bola?",
        "options": ["9", "10", "11", "12"],
        "answer": 2,
        "category": "⚽ Olahraga",
    },
    {
        "question": "Apa sistem operasi yang dikembangkan oleh Google untuk HP?",
        "options": ["iOS", "Windows Phone", "Android", "HarmonyOS"],
        "answer": 2,
        "category": "💻 Teknologi",
    },
    {
        "question": "Dalam anime Dragon Ball, siapa rival utama Goku?",
        "options": ["Piccolo", "Vegeta", "Frieza", "Cell"],
        "answer": 1,
        "category": "🎌 Anime",
    },
    {
        "question": "Apa nama samudra terbesar di dunia?",
        "options": ["Atlantik", "Hindia", "Pasifik", "Arktik"],
        "answer": 2,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Discord dibuat tahun berapa?",
        "options": ["2013", "2015", "2017", "2019"],
        "answer": 1,
        "category": "💻 Teknologi",
    },
    {
        "question": "Apa kepanjangan dari 'HTML'?",
        "options": ["Hyper Text Markup Language", "High Tech Modern Language", "Hyper Transfer Markup Language", "Home Tool Markup Language"],
        "answer": 0,
        "category": "💻 Teknologi",
    },
    {
        "question": "Siapa tokoh utama dalam anime 'Attack on Titan'?",
        "options": ["Levi Ackerman", "Eren Yeager", "Mikasa Ackerman", "Armin Arlert"],
        "answer": 1,
        "category": "🎌 Anime",
    },
    {
        "question": "Negara mana yang memiliki populasi terbanyak di dunia?",
        "options": ["Amerika Serikat", "Indonesia", "India", "China"],
        "answer": 2,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Berapa kecepatan cahaya (dalam km/detik)?",
        "options": ["100.000", "200.000", "300.000", "400.000"],
        "answer": 2,
        "category": "🔬 Sains",
    },
    {
        "question": "Game 'Valorant' dikembangkan oleh?",
        "options": ["Blizzard", "Riot Games", "Epic Games", "Valve"],
        "answer": 1,
        "category": "🎮 Gaming",
    },
    {
        "question": "Apa nama teknik andalan Luffy di One Piece?",
        "options": ["Rasengan", "Kamehameha", "Gomu Gomu no Pistol", "Bankai"],
        "answer": 2,
        "category": "🎌 Anime",
    },
    {
        "question": "Sungai terpanjang di dunia adalah?",
        "options": ["Amazon", "Nil", "Mississippi", "Yangtze"],
        "answer": 1,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Apa nama virus yang menyebabkan pandemi 2020?",
        "options": ["SARS", "MERS", "COVID-19", "H1N1"],
        "answer": 2,
        "category": "🌍 Pengetahuan Umum",
    },
    {
        "question": "Siapa pencipta Facebook?",
        "options": ["Steve Jobs", "Mark Zuckerberg", "Larry Page", "Jack Dorsey"],
        "answer": 1,
        "category": "💻 Teknologi",
    },
    {
        "question": "Dalam game Mobile Legends, hero Layla termasuk role apa?",
        "options": ["Tank", "Fighter", "Marksman", "Mage"],
        "answer": 2,
        "category": "🎮 Gaming",
    },
]


# ==================== WORD SCRAMBLE ====================

WORD_SCRAMBLE_WORDS = [
    "naga", "pedang", "perisai", "potion", "dungeon", "monster",
    "petualang", "kastil", "sihir", "armor", "kristal", "elixir",
    "dragon", "phoenix", "warrior", "mage", "assassin", "archer",
    "battle", "quest", "treasure", "diamond", "emerald", "ruby",
    "golem", "zombie", "skeleton", "demon", "angel", "titan",
    "sword", "shield", "magic", "power", "shadow", "flame",
    "thunder", "ice", "earth", "wind", "light", "dark",
    "legend", "mythic", "ancient", "sacred", "cursed", "blessed",
    "adventure", "explore", "victory", "champion", "hero", "guild",
]


def scramble_word(word: str) -> str:
    """Scramble a word's letters, ensuring it's different from original."""
    letters = list(word)
    for _ in range(20):  # Try up to 20 times to get a different arrangement
        random.shuffle(letters)
        scrambled = "".join(letters)
        if scrambled != word:
            return scrambled
    return "".join(letters)


# ==================== PVP RANK TIERS ====================

PVP_RANKS = [
    (0, 799, "Bronze", "🥉"),
    (800, 1099, "Silver", "⚪"),
    (1100, 1399, "Gold", "🥇"),
    (1400, 1699, "Platinum", "💠"),
    (1700, 1999, "Diamond", "💎"),
    (2000, 9999, "Champion", "👑"),
]


def get_pvp_rank(elo: int) -> tuple:
    """Returns (rank_name, emoji) for the given ELO."""
    for low, high, name, emoji in PVP_RANKS:
        if low <= elo <= high:
            return name, emoji
    return "Unranked", "❓"


# ==================== LEVEL ROLES ====================

LEVEL_ROLES = {
    5: "⭐ Active Member",
    10: "🔥 Regular",
    20: "💎 Veteran",
    50: "👑 Legend",
}
