from flask import Flask, jsonify, send_file
import sqlite3
import random

app = Flask(__name__)

# =====================
# SQLite
# =====================

conn = sqlite3.connect(
    "game.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS player_save(
    id INTEGER PRIMARY KEY,
    level INTEGER,
    exp INTEGER,
    hp INTEGER,
    max_hp INTEGER,
    attack INTEGER,
    floor INTEGER
)
""")

conn.commit()

# =====================
# Player
# =====================

class Player:

    def __init__(self):

        self.level = 1

        self.exp = 0

        self.max_hp = 30

        self.hp = 30

        self.attack = 5

        self.defense = 2

        self.dead = False

        self.heal_count = 0


# =====================
# Enemy
# =====================

class Enemy:

    def __init__(
        self,
        name,
        hp,
        attack,
        exp
    ):

        self.name = name

        self.hp = hp

        self.attack = attack

        self.exp = exp


# =====================
# Dungeon
# =====================

class Dungeon:

    def __init__(self):

        self.floor = 1


player = Player()

dungeon = Dungeon()

current_enemy = None


# =====================
# Enemy Factory
# =====================

def create_enemy():

    level = player.level

    enemy_pool = [
        "slime"
    ]

    if level >= 3:

        enemy_pool.append(
            "goblin"
        )

    if level >= 6:

        enemy_pool.append(
            "orc"
        )

    enemy_type = random.choice(
        enemy_pool
    )

    # -----------------
    # スライム
    # -----------------

    if enemy_type == "slime":

        return Enemy(
            "スライム",
            10 + level * 4,
            2 + level,
            5 + level
        )

    # -----------------
    # ゴブリン
    # -----------------

    elif enemy_type == "goblin":

        return Enemy(
            "ゴブリン",
            20 + level * 4,
            4 + level,
            10 + level
        )

    # -----------------
    # オーク
    # -----------------

    return Enemy(
        "オーク",
        35 + level * 4,
        6 + level,
        20 + level
    )


# =====================
# TOP
# =====================

@app.route("/")
def index():

    return send_file(
        "index.html"
    )


# =====================
# PLAYER API
# =====================

@app.route("/player")
def get_player():

    return jsonify(
        {
            "level": player.level,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "attack": player.attack,
            "exp": player.exp,
            "floor": dungeon.floor
        }
    )


# =====================
# ENEMY API
# =====================

@app.route("/enemy")
def get_enemy():

    global current_enemy

    if current_enemy is None:

        return jsonify(
            {
                "enemy": None
            }
        )

    return jsonify(
        {
            "enemy": current_enemy.name,
            "hp": current_enemy.hp
        }
    )


# =====================
# START BATTLE
# =====================

@app.route("/start_battle")
def start_battle():

    global current_enemy

    if player.dead:

        return jsonify(
            {
                "status": "game_over"
            }
        )

    if current_enemy is not None:

        return jsonify(
            {
                "status": "already"
            }
        )

    # -----------------
    # ラスボス
    # -----------------

    if dungeon.floor == 30:

        current_enemy = Enemy(
            "ドラゴン",
            200,
            15,
            100
        )

    else:

        current_enemy = create_enemy()

    player.heal_count = 0

    return jsonify(
        {
            "status": "battle_start",
            "enemy": current_enemy.name
        }
    )

# =====================
# ATTACK
# =====================

@app.route("/attack")
def attack():

    global current_enemy

    if player.dead:

        return jsonify(
            {
                "status":"game_over"
            }
        )

    if current_enemy is None:

        return jsonify(
            {
                "status":"no_enemy"
            }
        )

    current_enemy.hp -= player.attack

    # -----------------
    # 撃破
    # -----------------

    if current_enemy.hp <= 0:

        gained_exp = current_enemy.exp

        defeated_enemy = current_enemy.name

        player.exp += gained_exp

        current_enemy = None

        need_exp = player.level * 20

        level_up = False

        if player.exp >= need_exp:

            player.level += 1

            player.exp = 0

            player.max_hp += 2

            player.attack += 1

            player.hp = player.max_hp

            level_up = True

        return jsonify(
            {
                "status":"victory",
                "enemy":defeated_enemy,
                "level_up":level_up
            }
        )

    # -----------------
    # 敵反撃
    # -----------------

    damage = max(
        1,
        current_enemy.attack
        - player.defense
    )

    player.hp -= damage

    if player.hp <= 0:

        player.hp = 0

        player.dead = True

        return jsonify(
            {
                "status":"game_over"
            }
        )

    return jsonify(
        {
            "status":"continue",
            "enemy_hp":current_enemy.hp,
            "player_hp":player.hp
        }
    )


# =====================
# DEFEND
# =====================

@app.route("/defend")
def defend():

    global current_enemy

    if current_enemy is None:

        return jsonify(
            {
                "status":"no_enemy"
            }
        )

    damage = max(
        1,
        (
            current_enemy.attack // 2
        )
        - player.defense
    )

    player.hp -= damage

    if player.hp <= 0:

        player.hp = 0

        player.dead = True

        return jsonify(
            {
                "status":"game_over"
            }
        )

    return jsonify(
        {
            "status":"defended"
        }
    )


# =====================
# HEAL
# =====================

@app.route("/heal")
def heal():

    global current_enemy

    if current_enemy is None:

        return jsonify(
            {
                "status":"no_enemy"
            }
        )

    if player.heal_count >= 2:

        return jsonify(
            {
                "status":"heal_limit"
            }
        )

    player.heal_count += 1

    player.hp += 10

    if player.hp > player.max_hp:

        player.hp = player.max_hp

    damage = max(
        1,
        current_enemy.attack
        - player.defense
    )

    player.hp -= damage

    if player.hp <= 0:

        player.hp = 0

        player.dead = True

        return jsonify(
            {
                "status":"game_over"
            }
        )

    return jsonify(
        {
            "status":"healed"
        }
    )


# =====================
# ESCAPE
# =====================

@app.route("/run")
def run_away():

    global current_enemy

    if current_enemy is None:

        return jsonify(
            {
                "status":"no_enemy"
            }
        )

    success = random.randint(
        1,
        100
    ) <= 40

    if success:

        current_enemy = None

        return jsonify(
            {
                "status":"escaped"
            }
        )

    damage = max(
        1,
        current_enemy.attack
        - player.defense
    )

    player.hp -= damage

    if player.hp <= 0:

        player.hp = 0

        player.dead = True

        return jsonify(
            {
                "status":"game_over"
            }
        )

    return jsonify(
        {
            "status":"failed_escape"
        }
    )


# =====================
# NEXT FLOOR
# =====================

@app.route("/next_floor")
def next_floor():

    if player.dead:

        return jsonify(
            {
                "status":"game_over"
            }
        )

    if current_enemy is not None:

        return jsonify(
            {
                "status":"battle_first"
            }
        )

    dungeon.floor += 1

    if dungeon.floor > 30:

        dungeon.floor = 30

    return jsonify(
        {
            "status":"ok",
            "floor":dungeon.floor
        }
    )


# =====================
# SAVE
# =====================

@app.route("/save")
def save_game():

    cursor.execute(
        "DELETE FROM player_save"
    )

    cursor.execute(
        """
        INSERT INTO player_save(
            id,
            level,
            exp,
            hp,
            max_hp,
            attack,
            floor
        )
        VALUES(
            1,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            player.level,
            player.exp,
            player.hp,
            player.max_hp,
            player.attack,
            dungeon.floor
        )
    )

    conn.commit()

    return jsonify(
        {
            "status":"saved"
        }
    )


# =====================
# LOAD
# =====================

@app.route("/load")
def load_game():

    global current_enemy

    row = cursor.execute(
        """
        SELECT
            level,
            exp,
            hp,
            max_hp,
            attack,
            floor
        FROM player_save
        WHERE id = 1
        """
    ).fetchone()

    if row is None:

        return jsonify(
            {
                "status":"not_found"
            }
        )

    player.level = row[0]
    player.exp = row[1]
    player.hp = row[2]
    player.max_hp = row[3]
    player.attack = row[4]

    dungeon.floor = row[5]

    player.dead = False

    current_enemy = None

    return jsonify(
        {
            "status":"loaded"
        }
    )


# =====================
# RUN
# =====================

if __name__ == "__main__":

    app.run(
        debug=True
    )