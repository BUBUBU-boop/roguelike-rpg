from flask import (
    Flask,
    jsonify,
    request,
    send_file
)

import sqlite3
import random
from datetime import datetime

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
CREATE TABLE IF NOT EXISTS death_records(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    player_name TEXT,

    level INTEGER,

    floor INTEGER,

    enemy_name TEXT,

    death_time TEXT

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

last_dead_enemy = ""

death_record_saved = False


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

    if enemy_type == "slime":

        return Enemy(
            "スライム",
            10 + level * 4,
            2 + level,
            5 + level
        )

    elif enemy_type == "goblin":

        return Enemy(
            "ゴブリン",
            20 + level * 4,
            4 + level,
            10 + level
        )

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
# PLAYER
# =====================

@app.route("/player")
def get_player():

    return jsonify(
        {
            "level": player.level,
            "exp": player.exp,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "attack": player.attack,
            "defense": player.defense,
            "floor": dungeon.floor,
            "dead": player.dead
        }
    )


# =====================
# ENEMY
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
                "status":"game_over"
            }
        )

    if current_enemy is not None:

        return jsonify(
            {
                "status":"already"
            }
        )

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
            "status":"battle_start",
            "enemy":current_enemy.name
        }
    )


# =====================
# ATTACK
# =====================

@app.route("/attack")
def attack():

    global current_enemy
    global last_dead_enemy
    global death_record_saved

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

    damage = max(
        1,
        current_enemy.attack
        - player.defense
    )

    player.hp -= damage

    if player.hp <= 0:

        player.hp = 0

        player.dead = True

        death_record_saved = False

        last_dead_enemy = current_enemy.name

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
    global last_dead_enemy
    global death_record_saved

    if current_enemy is None:

        return jsonify(
            {
                "status":"no_enemy"
            }
        )

    damage = max(
        1,
        (current_enemy.attack // 2)
        - player.defense
    )

    player.hp -= damage

    if player.hp <= 0:

        player.hp = 0

        player.dead = True

        death_record_saved = False

        last_dead_enemy = current_enemy.name

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
    global last_dead_enemy
    global death_record_saved

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

        death_record_saved = False

        last_dead_enemy = current_enemy.name

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
# RUN
# =====================

@app.route("/run")
def run_away():

    global current_enemy
    global last_dead_enemy
    global death_record_saved

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

        death_record_saved = False

        last_dead_enemy = current_enemy.name

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
# SAVE DEATH RECORD
# =====================

@app.route(
    "/save_death_record",
    methods=["POST"]
)
def save_death_record():

    global death_record_saved

    if death_record_saved:

        return jsonify(
            {
                "status":"already_saved"
            }
        )

    data = request.json

    player_name = data.get(
        "player_name",
        ""
    ).strip()

    if player_name == "":

        player_name = "名無し"

    cursor.execute(
        """
        INSERT INTO death_records(
            player_name,
            level,
            floor,
            enemy_name,
            death_time
        )
        VALUES(
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            player_name,
            player.level,
            dungeon.floor,
            last_dead_enemy,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    conn.commit()

    death_record_saved = True

    return jsonify(
        {
            "status":"saved"
        }
    )


# =====================
# DEATH RECORDS
# =====================

@app.route("/death_records")
def death_records():

    rows = cursor.execute(
        """
        SELECT
            player_name,
            level,
            floor,
            enemy_name,
            death_time
        FROM death_records
        ORDER BY floor DESC
        """
    ).fetchall()

    result = []

    for row in rows:

        result.append(
            {
                "player_name":row[0],
                "level":row[1],
                "floor":row[2],
                "enemy_name":row[3],
                "death_time":row[4]
            }
        )

    return jsonify(result)


# =====================
# IMPORT SAVE
# =====================

@app.route(
    "/import_save",
    methods=["POST"]
)
def import_save():

    data = request.json

    player.level = data["level"]
    player.exp = data["exp"]
    player.hp = data["hp"]
    player.max_hp = data["max_hp"]
    player.attack = data["attack"]
    player.defense = data["defense"]

    dungeon.floor = data["floor"]

    player.dead = False

    return jsonify(
        {
            "status":"loaded"
        }
    )


# =====================
# RESET
# =====================

@app.route("/reset")
def reset():

    global player
    global dungeon
    global current_enemy
    global death_record_saved

    player = Player()

    dungeon = Dungeon()

    current_enemy = None

    death_record_saved = False

    return jsonify(
        {
            "status":"reset"
        }
    )


# =====================
# RUN APP
# =====================

if __name__ == "__main__":

    app.run(
        debug=True
    )
