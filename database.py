"""
database.py — PostgreSQL database manager untuk Ghost Assistant RPG
Menggunakan asyncpg dengan connection pooling
"""

import asyncpg
import os
from datetime import datetime, timezone

# PostgreSQL connection from Railway environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Connection pool (initialized in init_db)
pool: asyncpg.Pool = None


# ==================== INIT & CONNECTION ====================

async def init_db():
    """Initialize PostgreSQL connection pool and create tables."""
    global pool

    if not DATABASE_URL:
        print("[DB] ERROR: DATABASE_URL not set!")
        return

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)

    async with pool.acquire() as conn:
        # User profiles (XP, level, coins, daily)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id      BIGINT,
                guild_id     BIGINT,
                xp           INTEGER DEFAULT 0,
                level        INTEGER DEFAULT 1,
                coins        INTEGER DEFAULT 0,
                total_games  INTEGER DEFAULT 0,
                games_won    INTEGER DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                last_daily   TEXT DEFAULT NULL,
                last_xp_gain TEXT DEFAULT NULL,
                PRIMARY KEY (user_id, guild_id)
            )
        """)

        # Characters (RPG class & stats)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                user_id        BIGINT,
                guild_id       BIGINT,
                class_name     TEXT NOT NULL,
                max_hp         INTEGER DEFAULT 100,
                current_hp     INTEGER DEFAULT 100,
                floor_level    INTEGER DEFAULT 1,
                last_adventure TEXT DEFAULT NULL,
                PRIMARY KEY (user_id, guild_id)
            )
        """)

        # Inventory
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id           SERIAL PRIMARY KEY,
                user_id      BIGINT,
                guild_id     BIGINT,
                item_id      TEXT NOT NULL,
                quantity     INTEGER DEFAULT 1,
                is_equipped  BOOLEAN DEFAULT FALSE
            )
        """)

        # Pets
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id           SERIAL PRIMARY KEY,
                user_id      BIGINT,
                guild_id     BIGINT,
                pet_id       TEXT NOT NULL,
                pet_name     TEXT DEFAULT NULL,
                pet_level    INTEGER DEFAULT 1,
                pet_xp       INTEGER DEFAULT 0,
                is_active    BOOLEAN DEFAULT FALSE,
                obtained_at  TEXT
            )
        """)

        # PvP stats
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pvp_stats (
                user_id      BIGINT,
                guild_id     BIGINT,
                elo          INTEGER DEFAULT 1000,
                pvp_wins     INTEGER DEFAULT 0,
                pvp_losses   INTEGER DEFAULT 0,
                pvp_streak   INTEGER DEFAULT 0,
                best_streak  INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        """)

        # Game history
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                id           SERIAL PRIMARY KEY,
                user_id      BIGINT,
                guild_id     BIGINT,
                game_type    TEXT,
                result       TEXT,
                xp_gained    INTEGER,
                coins_gained INTEGER,
                played_at    TEXT
            )
        """)

        # Active battles (state for multi-turn PvE)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS active_battles (
                id             SERIAL PRIMARY KEY,
                user_id        BIGINT,
                guild_id       BIGINT,
                channel_id     BIGINT,
                message_id     BIGINT,
                monster_id     TEXT,
                monster_name   TEXT,
                monster_emoji  TEXT,
                monster_hp     INTEGER,
                monster_max_hp INTEGER,
                monster_atk    INTEGER,
                monster_def    INTEGER,
                is_boss        BOOLEAN DEFAULT FALSE,
                floor_num      INTEGER DEFAULT 1,
                battle_log     TEXT DEFAULT '',
                started_at     TEXT
            )
        """)

        # Active PvP duels
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS active_duels (
                id              SERIAL PRIMARY KEY,
                challenger_id   BIGINT,
                defender_id     BIGINT,
                guild_id        BIGINT,
                channel_id      BIGINT,
                message_id      BIGINT,
                challenger_hp   INTEGER,
                defender_hp     INTEGER,
                challenger_max  INTEGER,
                defender_max    INTEGER,
                current_turn    BIGINT,
                battle_log      TEXT DEFAULT '',
                started_at      TEXT
            )
        """)

    print("[DB] PostgreSQL connected and all tables ready.")


async def close_db():
    """Close the database connection pool."""
    global pool
    if pool:
        await pool.close()
        print("[DB] PostgreSQL connection pool closed.")


# ==================== USER PROFILES ====================

async def get_profile(user_id: int, guild_id: int) -> dict:
    """Get user profile, create one if it doesn't exist."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )

        if row is None:
            await conn.execute(
                "INSERT INTO user_profiles (user_id, guild_id) VALUES ($1, $2)",
                user_id, guild_id
            )
            return {
                "user_id": user_id, "guild_id": guild_id,
                "xp": 0, "level": 1, "coins": 0,
                "total_games": 0, "games_won": 0,
                "daily_streak": 0, "last_daily": None, "last_xp_gain": None,
            }
        return dict(row)


def xp_for_next_level(current_level: int) -> int:
    """Calculate XP needed for just the next level."""
    return current_level * 100


def get_total_xp_for_level(level: int) -> int:
    """Calculate total cumulative XP needed to reach a specific level."""
    return sum(i * 100 for i in range(1, level))


async def add_xp(user_id: int, guild_id: int, amount: int) -> tuple:
    """Add XP to a user. Returns (new_level, leveled_up, levels_gained)."""
    profile = await get_profile(user_id, guild_id)
    new_xp = profile["xp"] + amount
    current_level = profile["level"]
    new_level = current_level

    while True:
        needed = get_total_xp_for_level(new_level + 1)
        if new_xp >= needed:
            new_level += 1
        else:
            break

    leveled_up = new_level > current_level
    levels_gained = new_level - current_level

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE user_profiles SET xp = $1, level = $2 WHERE user_id = $3 AND guild_id = $4",
            new_xp, new_level, user_id, guild_id
        )
    return new_level, leveled_up, levels_gained


async def add_coins(user_id: int, guild_id: int, amount: int) -> int:
    """Add (or subtract if negative) coins. Returns new balance."""
    profile = await get_profile(user_id, guild_id)
    new_coins = max(0, profile["coins"] + amount)

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE user_profiles SET coins = $1 WHERE user_id = $2 AND guild_id = $3",
            new_coins, user_id, guild_id
        )
    return new_coins


async def get_coins(user_id: int, guild_id: int) -> int:
    """Get user's coin balance."""
    profile = await get_profile(user_id, guild_id)
    return profile["coins"]


async def update_last_xp_gain(user_id: int, guild_id: int):
    """Update the timestamp of the last XP gain from chat."""
    now = datetime.now(timezone.utc).isoformat()
    await get_profile(user_id, guild_id)
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE user_profiles SET last_xp_gain = $1 WHERE user_id = $2 AND guild_id = $3",
            now, user_id, guild_id
        )


async def record_game(user_id: int, guild_id: int, game_type: str, result: str, xp: int, coins: int):
    """Record a game result and update user stats."""
    now = datetime.now(timezone.utc).isoformat()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO game_history (user_id, guild_id, game_type, result, xp_gained, coins_gained, played_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            user_id, guild_id, game_type, result, xp, coins, now
        )
        won_increment = 1 if result == "win" else 0
        await conn.execute(
            """UPDATE user_profiles SET total_games = total_games + 1, games_won = games_won + $1
               WHERE user_id = $2 AND guild_id = $3""",
            won_increment, user_id, guild_id
        )


async def claim_daily(user_id: int, guild_id: int) -> tuple:
    """Claim daily reward. Returns (success, coins_awarded, new_streak, already_claimed)."""
    profile = await get_profile(user_id, guild_id)
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    if profile["last_daily"] == today_str:
        return False, 0, profile["daily_streak"], True

    old_streak = profile["daily_streak"]
    if profile["last_daily"]:
        last_date = datetime.strptime(profile["last_daily"], "%Y-%m-%d")
        diff = (now - last_date.replace(tzinfo=timezone.utc)).days
        new_streak = old_streak + 1 if diff == 1 else 1
    else:
        new_streak = 1

    streak_bonus = min(new_streak * 10, 200)
    coins_awarded = 50 + streak_bonus

    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE user_profiles SET coins = coins + $1, daily_streak = $2, last_daily = $3
               WHERE user_id = $4 AND guild_id = $5""",
            coins_awarded, new_streak, today_str, user_id, guild_id
        )
    return True, coins_awarded, new_streak, False


# ==================== CHARACTERS ====================

async def create_character(user_id: int, guild_id: int, class_name: str, max_hp: int) -> dict:
    """Create a new character."""
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO characters (user_id, guild_id, class_name, max_hp, current_hp)
               VALUES ($1, $2, $3, $4, $4)
               ON CONFLICT (user_id, guild_id) DO UPDATE
               SET class_name = $3, max_hp = $4, current_hp = $4, floor_level = 1""",
            user_id, guild_id, class_name, max_hp
        )
    return {"user_id": user_id, "guild_id": guild_id, "class_name": class_name,
            "max_hp": max_hp, "current_hp": max_hp, "floor_level": 1}


async def get_character(user_id: int, guild_id: int) -> dict | None:
    """Get character data. Returns None if no character exists."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM characters WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        return dict(row) if row else None


async def update_character_hp(user_id: int, guild_id: int, current_hp: int, max_hp: int = None):
    """Update character HP."""
    async with pool.acquire() as conn:
        if max_hp is not None:
            await conn.execute(
                "UPDATE characters SET current_hp = $1, max_hp = $2 WHERE user_id = $3 AND guild_id = $4",
                current_hp, max_hp, user_id, guild_id
            )
        else:
            await conn.execute(
                "UPDATE characters SET current_hp = $1 WHERE user_id = $2 AND guild_id = $3",
                current_hp, user_id, guild_id
            )


async def update_floor(user_id: int, guild_id: int, floor: int):
    """Update character's dungeon floor."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE characters SET floor_level = $1 WHERE user_id = $2 AND guild_id = $3",
            floor, user_id, guild_id
        )


async def update_last_adventure(user_id: int, guild_id: int):
    """Update last adventure timestamp."""
    now = datetime.now(timezone.utc).isoformat()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE characters SET last_adventure = $1 WHERE user_id = $2 AND guild_id = $3",
            now, user_id, guild_id
        )


async def heal_character(user_id: int, guild_id: int):
    """Heal character to full HP."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE characters SET current_hp = max_hp WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )


# ==================== INVENTORY ====================

async def add_item(user_id: int, guild_id: int, item_id: str, quantity: int = 1):
    """Add item to inventory. Stacks if same item exists (non-equipped)."""
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            """SELECT id, quantity FROM inventory
               WHERE user_id = $1 AND guild_id = $2 AND item_id = $3 AND is_equipped = FALSE""",
            user_id, guild_id, item_id
        )
        if existing:
            await conn.execute(
                "UPDATE inventory SET quantity = quantity + $1 WHERE id = $2",
                quantity, existing["id"]
            )
        else:
            await conn.execute(
                """INSERT INTO inventory (user_id, guild_id, item_id, quantity, is_equipped)
                   VALUES ($1, $2, $3, $4, FALSE)""",
                user_id, guild_id, item_id, quantity
            )


async def remove_item(user_id: int, guild_id: int, item_id: str, quantity: int = 1) -> bool:
    """Remove item from inventory. Returns True if successful."""
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            """SELECT id, quantity FROM inventory
               WHERE user_id = $1 AND guild_id = $2 AND item_id = $3 AND is_equipped = FALSE""",
            user_id, guild_id, item_id
        )
        if not existing or existing["quantity"] < quantity:
            return False

        new_qty = existing["quantity"] - quantity
        if new_qty <= 0:
            await conn.execute("DELETE FROM inventory WHERE id = $1", existing["id"])
        else:
            await conn.execute("UPDATE inventory SET quantity = $1 WHERE id = $2", new_qty, existing["id"])
        return True


async def get_inventory(user_id: int, guild_id: int) -> list:
    """Get all inventory items."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM inventory WHERE user_id = $1 AND guild_id = $2 ORDER BY item_id",
            user_id, guild_id
        )
        return [dict(r) for r in rows]


async def get_equipped_items(user_id: int, guild_id: int) -> list:
    """Get equipped items only."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM inventory WHERE user_id = $1 AND guild_id = $2 AND is_equipped = TRUE",
            user_id, guild_id
        )
        return [dict(r) for r in rows]


async def equip_item(user_id: int, guild_id: int, item_id: str, item_type: str) -> bool:
    """Equip an item. Unequips existing item in same slot first."""
    async with pool.acquire() as conn:
        # Check if user has the item (non-equipped)
        item_row = await conn.fetchrow(
            """SELECT id, quantity FROM inventory
               WHERE user_id = $1 AND guild_id = $2 AND item_id = $3 AND is_equipped = FALSE""",
            user_id, guild_id, item_id
        )
        if not item_row:
            return False

        # Unequip current item in same type/slot
        from game_data import ITEMS
        equipped = await conn.fetch(
            "SELECT id, item_id FROM inventory WHERE user_id = $1 AND guild_id = $2 AND is_equipped = TRUE",
            user_id, guild_id
        )
        for eq in equipped:
            eq_data = ITEMS.get(eq["item_id"], {})
            if eq_data.get("type") == item_type:
                # Move back to inventory stack
                existing_stack = await conn.fetchrow(
                    """SELECT id, quantity FROM inventory
                       WHERE user_id = $1 AND guild_id = $2 AND item_id = $3 AND is_equipped = FALSE""",
                    user_id, guild_id, eq["item_id"]
                )
                if existing_stack:
                    await conn.execute("UPDATE inventory SET quantity = quantity + 1 WHERE id = $1", existing_stack["id"])
                    await conn.execute("DELETE FROM inventory WHERE id = $1", eq["id"])
                else:
                    await conn.execute("UPDATE inventory SET is_equipped = FALSE WHERE id = $1", eq["id"])

        # Equip the new item
        if item_row["quantity"] > 1:
            await conn.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id = $1", item_row["id"])
            await conn.execute(
                """INSERT INTO inventory (user_id, guild_id, item_id, quantity, is_equipped)
                   VALUES ($1, $2, $3, 1, TRUE)""",
                user_id, guild_id, item_id
            )
        else:
            await conn.execute("UPDATE inventory SET is_equipped = TRUE WHERE id = $1", item_row["id"])

        return True


async def unequip_item(user_id: int, guild_id: int, item_type: str) -> str | None:
    """Unequip item from slot. Returns unequipped item_id or None."""
    from game_data import ITEMS
    async with pool.acquire() as conn:
        equipped = await conn.fetch(
            "SELECT id, item_id FROM inventory WHERE user_id = $1 AND guild_id = $2 AND is_equipped = TRUE",
            user_id, guild_id
        )
        for eq in equipped:
            eq_data = ITEMS.get(eq["item_id"], {})
            if eq_data.get("type") == item_type:
                # Move back to stack
                existing_stack = await conn.fetchrow(
                    """SELECT id FROM inventory
                       WHERE user_id = $1 AND guild_id = $2 AND item_id = $3 AND is_equipped = FALSE""",
                    user_id, guild_id, eq["item_id"]
                )
                if existing_stack:
                    await conn.execute("UPDATE inventory SET quantity = quantity + 1 WHERE id = $1", existing_stack["id"])
                    await conn.execute("DELETE FROM inventory WHERE id = $1", eq["id"])
                else:
                    await conn.execute("UPDATE inventory SET is_equipped = FALSE WHERE id = $1", eq["id"])
                return eq["item_id"]
    return None


async def get_item_count(user_id: int, guild_id: int, item_id: str) -> int:
    """Get total count of an item (non-equipped)."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT COALESCE(SUM(quantity), 0) as total FROM inventory
               WHERE user_id = $1 AND guild_id = $2 AND item_id = $3 AND is_equipped = FALSE""",
            user_id, guild_id, item_id
        )
        return row["total"] if row else 0


# ==================== PETS ====================

async def add_pet(user_id: int, guild_id: int, pet_id: str) -> int:
    """Add a pet. Returns the pet's database ID."""
    now = datetime.now(timezone.utc).isoformat()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO pets (user_id, guild_id, pet_id, obtained_at)
               VALUES ($1, $2, $3, $4) RETURNING id""",
            user_id, guild_id, pet_id, now
        )
        return row["id"]


async def get_pets(user_id: int, guild_id: int) -> list:
    """Get all pets owned by user."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM pets WHERE user_id = $1 AND guild_id = $2 ORDER BY id",
            user_id, guild_id
        )
        return [dict(r) for r in rows]


async def get_active_pet(user_id: int, guild_id: int) -> dict | None:
    """Get the active pet."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM pets WHERE user_id = $1 AND guild_id = $2 AND is_active = TRUE",
            user_id, guild_id
        )
        return dict(row) if row else None


async def set_active_pet(user_id: int, guild_id: int, pet_db_id: int) -> bool:
    """Set a pet as active. Returns True if successful."""
    async with pool.acquire() as conn:
        # Check ownership
        pet = await conn.fetchrow(
            "SELECT id FROM pets WHERE id = $1 AND user_id = $2 AND guild_id = $3",
            pet_db_id, user_id, guild_id
        )
        if not pet:
            return False

        # Deactivate all pets first
        await conn.execute(
            "UPDATE pets SET is_active = FALSE WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        # Activate selected
        await conn.execute("UPDATE pets SET is_active = TRUE WHERE id = $1", pet_db_id)
        return True


async def name_pet(pet_db_id: int, user_id: int, guild_id: int, name: str) -> bool:
    """Name a pet. Returns True if successful."""
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE pets SET pet_name = $1 WHERE id = $2 AND user_id = $3 AND guild_id = $4",
            name, pet_db_id, user_id, guild_id
        )
        return "UPDATE 1" in result


async def add_pet_xp(pet_db_id: int, xp: int) -> tuple:
    """Add XP to pet. Returns (new_level, leveled_up)."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT pet_level, pet_xp FROM pets WHERE id = $1", pet_db_id)
        if not row:
            return 1, False

        new_xp = row["pet_xp"] + xp
        current_level = row["pet_level"]
        new_level = current_level

        # Pet level formula: level * 50 XP needed
        while new_xp >= new_level * 50:
            new_xp -= new_level * 50
            new_level += 1

        await conn.execute(
            "UPDATE pets SET pet_level = $1, pet_xp = $2 WHERE id = $3",
            new_level, new_xp, pet_db_id
        )
        return new_level, new_level > current_level


# ==================== PVP ====================

async def get_pvp_stats(user_id: int, guild_id: int) -> dict:
    """Get PvP stats, create if not exists."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM pvp_stats WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        if row is None:
            await conn.execute(
                "INSERT INTO pvp_stats (user_id, guild_id) VALUES ($1, $2)",
                user_id, guild_id
            )
            return {"user_id": user_id, "guild_id": guild_id, "elo": 1000,
                    "pvp_wins": 0, "pvp_losses": 0, "pvp_streak": 0, "best_streak": 0}
        return dict(row)


async def update_pvp_result(user_id: int, guild_id: int, won: bool, elo_change: int):
    """Update PvP stats after a duel."""
    async with pool.acquire() as conn:
        stats = await get_pvp_stats(user_id, guild_id)
        new_elo = max(0, stats["elo"] + elo_change)

        if won:
            new_streak = stats["pvp_streak"] + 1
            best = max(stats["best_streak"], new_streak)
            await conn.execute(
                """UPDATE pvp_stats SET elo = $1, pvp_wins = pvp_wins + 1,
                   pvp_streak = $2, best_streak = $3 WHERE user_id = $4 AND guild_id = $5""",
                new_elo, new_streak, best, user_id, guild_id
            )
        else:
            await conn.execute(
                """UPDATE pvp_stats SET elo = $1, pvp_losses = pvp_losses + 1,
                   pvp_streak = 0 WHERE user_id = $2 AND guild_id = $3""",
                new_elo, user_id, guild_id
            )


# ==================== BATTLES ====================

async def create_battle(user_id: int, guild_id: int, channel_id: int, message_id: int,
                        monster: dict, floor: int, is_boss: bool = False) -> int:
    """Create an active battle. Returns battle ID."""
    now = datetime.now(timezone.utc).isoformat()
    async with pool.acquire() as conn:
        # Remove any existing battle for this user
        await conn.execute(
            "DELETE FROM active_battles WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        row = await conn.fetchrow(
            """INSERT INTO active_battles
               (user_id, guild_id, channel_id, message_id, monster_id, monster_name, monster_emoji,
                monster_hp, monster_max_hp, monster_atk, monster_def, is_boss, floor_num, started_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8, $9, $10, $11, $12, $13)
               RETURNING id""",
            user_id, guild_id, channel_id, message_id,
            monster["id"], monster["name"], monster["emoji"],
            monster["hp"], monster["atk"], monster["def"],
            is_boss, floor, now
        )
        return row["id"]


async def get_active_battle(user_id: int, guild_id: int) -> dict | None:
    """Get active battle for user."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM active_battles WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        return dict(row) if row else None


async def update_battle(battle_id: int, monster_hp: int, battle_log: str):
    """Update battle state."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE active_battles SET monster_hp = $1, battle_log = $2 WHERE id = $3",
            monster_hp, battle_log, battle_id
        )


async def end_battle(user_id: int, guild_id: int):
    """End/remove active battle."""
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM active_battles WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )


# ==================== DUELS ====================

async def create_duel(challenger_id: int, defender_id: int, guild_id: int,
                      channel_id: int, message_id: int,
                      challenger_hp: int, defender_hp: int) -> int:
    """Create an active duel. Returns duel ID."""
    now = datetime.now(timezone.utc).isoformat()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO active_duels
               (challenger_id, defender_id, guild_id, channel_id, message_id,
                challenger_hp, defender_hp, challenger_max, defender_max,
                current_turn, started_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $6, $7, $1, $8)
               RETURNING id""",
            challenger_id, defender_id, guild_id, channel_id, message_id,
            challenger_hp, defender_hp, now
        )
        return row["id"]


async def get_active_duel(user_id: int, guild_id: int) -> dict | None:
    """Get active duel involving user."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT * FROM active_duels
               WHERE guild_id = $1 AND (challenger_id = $2 OR defender_id = $2)""",
            guild_id, user_id
        )
        return dict(row) if row else None


async def update_duel(duel_id: int, challenger_hp: int, defender_hp: int,
                      current_turn: int, battle_log: str):
    """Update duel state."""
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE active_duels SET challenger_hp = $1, defender_hp = $2,
               current_turn = $3, battle_log = $4 WHERE id = $5""",
            challenger_hp, defender_hp, current_turn, battle_log, duel_id
        )


async def end_duel(duel_id: int):
    """End/remove active duel."""
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM active_duels WHERE id = $1", duel_id)


# ==================== LEADERBOARD ====================

async def get_leaderboard(guild_id: int, sort_by: str = "xp", limit: int = 10, offset: int = 0) -> list:
    """Get leaderboard sorted by the given field."""
    valid_sorts = {
        "xp": "xp DESC",
        "coins": "coins DESC",
        "games": "total_games DESC",
        "wins": "games_won DESC",
        "level": "level DESC, xp DESC",
    }
    order = valid_sorts.get(sort_by, "xp DESC")

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM user_profiles WHERE guild_id = $1 ORDER BY {order} LIMIT $2 OFFSET $3",
            guild_id, limit, offset
        )
        return [dict(r) for r in rows]


async def get_pvp_leaderboard(guild_id: int, limit: int = 10) -> list:
    """Get PvP leaderboard sorted by ELO."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM pvp_stats WHERE guild_id = $1 ORDER BY elo DESC LIMIT $2",
            guild_id, limit
        )
        return [dict(r) for r in rows]


async def get_floor_leaderboard(guild_id: int, limit: int = 10) -> list:
    """Get dungeon floor leaderboard."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM characters WHERE guild_id = $1 ORDER BY floor_level DESC LIMIT $2",
            guild_id, limit
        )
        return [dict(r) for r in rows]


async def get_user_rank(user_id: int, guild_id: int, sort_by: str = "xp") -> int:
    """Get user's rank position. Returns rank number (1-indexed)."""
    valid_sorts = {
        "xp": "xp DESC",
        "coins": "coins DESC",
        "level": "level DESC, xp DESC",
    }
    order = valid_sorts.get(sort_by, "xp DESC")

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT user_id FROM user_profiles WHERE guild_id = $1 ORDER BY {order}",
            guild_id
        )
        for i, row in enumerate(rows, 1):
            if row["user_id"] == user_id:
                return i
    return 0


async def get_total_users(guild_id: int) -> int:
    """Get total number of users with profiles."""
    async with pool.acquire() as conn:
        row = await conn.fetchval(
            "SELECT COUNT(*) FROM user_profiles WHERE guild_id = $1", guild_id
        )
        return row or 0
