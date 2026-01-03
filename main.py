import curses
import time
import random
from curses import wrapper

Game_Lost = False

SCREEN_SIZE_X = 75
SCREEN_SIZE_Y = 15

GAME_TICK = 1.3 #seconds
DIFFICULTY = 1
PROJECTILE_SPEED = 0.35

score = 0

last_tick = time.monotonic()
last_tick_projectiles = time.monotonic()
last_tick_enemies = time.monotonic()
last_tick_powers = time.monotonic()

play_area = [[0 for x in range(1, SCREEN_SIZE_X)]
             for y in range(1, SCREEN_SIZE_Y)]

enemies = [[] for i in range(1, SCREEN_SIZE_X - 1)]
enemies_raw = []
projectiles = []
player = {"x" : SCREEN_SIZE_X // 2, "y" : SCREEN_SIZE_Y - 2, "hp" : 500, "damage": 100, "powerup_chance": 15, "player_level" : 0}
powerup = {"x" : 0, "y" : 0}

enemy_types = {
    "basic": {
        "hp": 100,
        "char": "*",
        "score": 100
    },

    "common": {
        "hp": 200,
        "char": "=",
        "score": 150
    },

    "fighter": {
        "hp": 200,
        "char": "V",
        "score": 150
    },

    "mini_tank": {
        "hp": 400,
        "char": "m",
        "score": 350
    },

    "tank": {
        "hp": 700,
        "char": "m",
        "score": 350
    },

    "scout": {
        "hp": 80,
        "char": "s",
        "score": 120
    },

    "brute": {
        "hp": 500,
        "char": "B",
        "score": 500
    },

    "elite": {
        "hp": 350,
        "char": "E",
        "score": 300
    },

    "swarm": {
        "hp": 50,
        "char": "+",
        "score": 70
    },

    "boss": {
        "hp": 30000,
        "char": "#",
        "score": 5000
    },

}

PREMADE_ROUNDS = { #Rounds 1 - 20 rughrhghghd
    1:  (1.5, (1, 2), (1, 2), ["basic"]),
    2:  (1.5, (2, 3), (1, 2), ["basic"]),
    3:  (1.4, (3, 4), (1, 2), ["basic", "scout"]),
    4:  (1.4, (4, 5), (0.9, 1.5), ["basic", "scout"]),

    5:  (1.3, (5, 6), (0.8, 1.3), ["basic", "common"]),
    6:  (1.3, (6, 7), (0.8, 1.2), ["common", "scout"]),
    7:  (1.3, (7, 8), (0.7, 1.2), ["basic", "common", "swarm"]),

    8:  (1.2, (8, 9), (0.7, 1.1), ["common", "swarm"]),
    9:  (1.2, (9,10), (0.6, 1.0), ["common", "fighter"]),
    10: (1.2, (10,12), (0.6, 1.0), ["fighter"]),

    11: (1.1, (10,12), (0.6, 0.9), ["fighter", "elite"]),
    12: (1.1, (12,14), (0.5, 0.9), ["elite", "swarm"]),
    13: (1.1, (14,16), (0.5, 0.8), ["elite", "common"]),

    14: (1.0, (15,18), (0.5, 0.8), ["elite", "brute"]),
    15: (1.0, (18,20), (0.5, 0.7), ["brute"]),

    16: (0.95, (18,22), (0.45, 0.7), ["brute", "elite"]),
    17: (0.9, (20,24), (0.45, 0.65), ["elite", "fighter"]),
    18: (0.9, (22,26), (0.4, 0.6), ["fighter", "brute"]),

    19: (0.85, (25,30), (0.4, 0.6), ["elite", "brute", "swarm"]),
    20: (0.8, (1, 1), (2.0, 2.0), ["boss"]),
}

def levelUp():
    global PROJECTILE_SPEED
    player["player_level"] += 1
    if player["player_level"] == 1:
        player["damage"] += 50
        return "POWER UP: Damage Up"
    if player["player_level"] == 2:
        player["hp"] += 200
        return "POWER UP: HP Up"
    if player["player_level"] == 3:
        player["hp"] += 300
        return "POWER UP: HP Up"
    if player["player_level"] == 4:
        PROJECTILE_SPEED = 0.25
        return "POWER UP: Bullet Speed Up"
    if player["player_level"] == 5:
        player["damage"] += 100
        return "POWER UP: Damage Up PLUS"
    if player["player_level"] == 6:
        player["hp"] += 500
        return "POWER UP: HP Up PLUS"
    if player["player_level"] == 7:
        PROJECTILE_SPEED = 0.15
        return "POWER UP: Bullet Speed Up"
    if player["player_level"] == 8:
        PROJECTILE_SPEED = 0.1
        return "POWER UP: Bullet Speed Up"
    if player["player_level"] == 9:
        player["powerup_chance"] = 30
        return "POWER UP: Increased P Chance"
    if player["player_level"] == 10:
        player["damage"] += 100
        return "POWER UP: Damage Up PLUS"
    if player["player_level"] > 10:
        player["hp"] += 300
        return "POWER UP: HP Up"



# def generateLevel(currentLevel):
#     global GAME_TICK
#
#     if currentLevel <= 1:
#         GAME_TICK = 1.5
#         enemy_count = random.randint(1,2 )
#         enemy_treshold = random.randint(1, 2)
#         enemy_spawns = ["basic"]
#     elif currentLevel <= 4:
#         GAME_TICK = 1.4
#         enemy_count = random.randint(3,5 )
#         enemy_treshold = round(random.uniform(1, 2.0), 2)
#         enemy_spawns = ["basic"]
#     elif currentLevel <= 7:
#         GAME_TICK = 1.4
#         enemy_count = random.randint(5,7 )
#         enemy_treshold = round(random.uniform(0.9, 1.3), 2)
#         enemy_spawns = ["basic", "common"]
#
#
#     enemy_list = []
#
#     for i in range(0, enemy_count):
#          enemy_list.append([enemy_spawns[random.randint(0, len(enemy_spawns) - 1)], enemy_treshold])
#          enemies_raw.append(i)
#
#
#     return currentLevel + 1, enemy_list

def generateLevel(level):
    global GAME_TICK

    if level <= 20:
        GAME_TICK, count_rng, thresh_rng, enemy_spawns = PREMADE_ROUNDS[level]
        enemy_count = random.randint(*count_rng)
        enemy_treshold = round(random.uniform(*thresh_rng), 2)
    else:
        # Endless modeeee yoo
        GAME_TICK = max(0.4, 0.8 - (level - 20) * 0.02)
        enemy_count = 20 + (level - 20) * 2
        enemy_treshold = max(0.3, 0.8 - (level - 20) * 0.03)
        enemy_spawns = list(enemy_types.keys())

    enemy_list = []
    for i in range(enemy_count):
        enemy_list.append([
            random.choice(enemy_spawns),
            enemy_treshold
        ])
        enemies_raw.append(i)

    return level + 1, enemy_list

def is_boss_round(level_data):
    return len(level_data) == 1 and level_data[0][0] == "boss"


def draw_screen_border(stdscr):
    for i in range(0, SCREEN_SIZE_Y):
        if i == 0 or i == SCREEN_SIZE_Y - 1:
            for j in range(0, SCREEN_SIZE_X):
                stdscr.addstr(i , j, "*")
        else:
            stdscr.addstr(i, 0, "*") # left b
            stdscr.addstr(i, SCREEN_SIZE_X - 1, "*") # right b

    stdscr.addstr(2, SCREEN_SIZE_X + 2, "LEVEL 1")
    stdscr.addstr(3, SCREEN_SIZE_X + 2, "SCORE: 0")
    stdscr.addstr(5, SCREEN_SIZE_X + 2, "HP: 500")


class Enemy:
    def __init__(self, y, x, char, hp, score):
        self.x = x
        self.y = y
        self.char = char
        self.hp = hp
        self.score = score

class Projectile:
    def __init__(self, y, x, char, direction):
        self.x = x
        self.y = y
        self.char = char

        self.direction = direction

class Power:
    def __init__(self, y, x, char, direction):
        self.x = x
        self.y = y
        self.char = char

        self.direction = direction

boss_max_hp = 0
boss_ref = None
boss_phase = "normal"
boss_laser_rows = []
boss_phase_timer = 0

def main(stdscr):
    global player, last_tick, last_tick_enemies, score, boss_max_hp, boss_ref, boss_phase, boss_laser_rows, boss_phase_timer
    stdscr.clear()

    key = ''
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    h, w = stdscr.getmaxyx()

    stdscr.clear()
    stdscr.nodelay(True)
    #print(h, w)

    draw_screen_border(stdscr)

    keys_held = set()

    lev = 0
    while (Game_Lost == False and key != ord('q') and player["hp"] > 0):
        lev += 1
        stdscr.addstr(4, 30, "                ")
        current_lev, level_data = generateLevel(lev)

        if is_boss_round(level_data):
            stdscr.addstr(4, 30, "!!! BOSS APPROACHING !!!")
            stdscr.refresh()
            time.sleep(2)
            stdscr.addstr(4, 30, " " * 30)

        current_enemy_index = 0

        stdscr.addstr(2, SCREEN_SIZE_X + 2, f"LEVEL: {lev}")
        #stdscr.addstr(3, SCREEN_SIZE_X + 2, "SCORE: 500")

        while (Game_Lost == False and key != ord('q') and len(enemies_raw) > 0 and player["hp"] > 0):
            now = time.monotonic()
            try:
                key = stdscr.getch()

                if key != -1:
                    keys_held.add(key)
            except:
                key = None

            shoot = False

            stdscr.addstr(player["y"], player["x"], " ")

            play_area[player["y"]][player["x"]] = 0

            #if input == "KEY_LEFT":
            if ord('a') in keys_held:
                player["x"]-= 1
            if ord('d') in keys_held:
                player["x"] += 1
            if ord('w') in keys_held:
                player["y"] -= 1
            if ord('s') in keys_held:
                player["y"]+= 1

            player["x"] = max(1, min(player["x"], SCREEN_SIZE_X - 2))
            player["y"] = max(1, min(player["y"], SCREEN_SIZE_Y - 2))
            play_area[player["y"]][player["x"]] = 2


            if ord(' ') in keys_held:
                shoot = True



            if shoot == True and player["y"] > 0:
                #stdscr.addstr(player["y"] - 1, player["x"], "o")
                if player["player_level"] >= 5:
                    projectiles.append(Projectile(player["y"], player["x"], '|', "forward"))
                elif player["player_level"] >= 1:
                    projectiles.append(Projectile(player["y"], player["x"], 'x', "forward"))
                else:
                    projectiles.append(Projectile(player["y"], player["x"], 'o', "forward"))

            if boss_ref and boss_ref.hp > 0:
                bar_width = 20
                hp_ratio = boss_ref.hp / boss_max_hp
                filled = int(bar_width * hp_ratio)

                if hp_ratio > 0.6:
                    color = curses.color_pair(1)
                elif hp_ratio > 0.3:
                    color = curses.color_pair(2)
                else:
                    color = curses.color_pair(3)

                stdscr.addstr(1, SCREEN_SIZE_X + 2, "BOSS HP")
                stdscr.addstr(2, SCREEN_SIZE_X + 2, "[" + " " * bar_width + "]")
                stdscr.addstr(2, SCREEN_SIZE_X + 3, "█" * filled, color)

                if boss_phase == "normal" and hp_ratio < 0.6:
                    if random.random() < 0.01:  # 1% chance per frame
                        boss_phase = "laser"
                        boss_phase_timer = time.monotonic() + 2.5  # laser duration
                        boss_laser_rows = random.sample(
                            range(3, SCREEN_SIZE_Y - 3),
                            random.randint(2, 4)
                        )

            if boss_phase == "laser":
                if player["y"] in boss_laser_rows:
                    player["hp"] -= 5
                    stdscr.addstr(5, SCREEN_SIZE_X + 2, f"HP: {player['hp']}")

            #RENDER AND GAME UPDATE
            if len(level_data) > current_enemy_index and now - last_tick_enemies >= level_data[current_enemy_index][1]:
                last_tick_enemies = now

                enemy_type = level_data[current_enemy_index][0]
                enemy = enemy_types.get(enemy_type)

                if enemy_type == "boss":
                    newEnemySpawnX = SCREEN_SIZE_X // 2
                else:
                    newEnemySpawnX = random.randint(1, SCREEN_SIZE_X - 3)

                e = enemies[newEnemySpawnX].append(Enemy(0, newEnemySpawnX, enemy["char"], enemy["hp"], enemy["score"]))
                if enemy_type == "boss":
                    boss_ref = enemies[newEnemySpawnX][-1]
                    boss_max_hp = boss_ref.hp


                #level_data.remove(level_data[current_enemy_index])

                current_enemy_index += 1

            if now - last_tick >= GAME_TICK:
                last_tick = now
                #enemies.append(Enemy(0, random.randint(1, SCREEN_SIZE_X - 2), '👾'))

                for i in range(1, SCREEN_SIZE_X - 2):
                    if enemies[i]:
                        for enemy in enemies[i][:]:
                            #print(enemy, " ", enemy.char)
                            if enemy.y + 1 < SCREEN_SIZE_Y - 1 and (enemy.y == player["y"] and enemy.x == player["x"]) == False:
                                stdscr.addstr(enemy.y, enemy.x, " ")

                                if enemy.char == "#":  # DAAA boss
                                    enemy.y = 4
                                    if random.random() < 0.4:
                                        enemies[enemy.x].remove(enemy)
                                        enemy.x += random.choice([-1 * random.randint(1, 5), 1 * random.randint(1, 5)])
                                        enemy.x = max(1, min(enemy.x, SCREEN_SIZE_X - 2))
                                        enemies[enemy.x].append(enemy)


                                    # if random.random() < 0.3:
                                    #     enemy.y += random.choice(
                                    #         [-1 * random.randint(1, 5), 1 * random.randint(1, 5)])
                                    #     enemy.y = max(1, min(enemy.x, SCREEN_SIZE_X - 2))
                                else:
                                    enemy.y += 1
                                stdscr.addstr(enemy.y, enemy.x, enemy.char)
                            elif enemy.y >= SCREEN_SIZE_Y - 2:
                                stdscr.addstr(enemy.y, enemy.x, " ")
                                enemies[i].remove(enemy)
                                enemies_raw.pop(0)

                                if enemy.char == "#":
                                    player["hp"] -= 150
                                else:
                                    player["hp"] -= enemy.hp

                                stdscr.addstr(5, SCREEN_SIZE_X + 2, f"HP: {player.get('hp')}")

                                del enemy
                            elif enemy.x == player["x"] and enemy.y == player["y"]:
                                player["hp"] -= enemy.hp
                                stdscr.addstr(5, SCREEN_SIZE_X + 2, f"HP: {player.get('hp')}")



            if now - last_tick_projectiles >= PROJECTILE_SPEED and len(projectiles) > 0:
                for bullet in projectiles[:]:
                    direction = 0
                    if bullet.direction == "forward": direction = -1

                    enemy_hit = False
                    if bullet.y - 1 > 0:
                        if len(enemies[bullet.x]) != 0:
                            for enemy in enemies[bullet.x]:
                                if bullet.y - 1 == enemy.y:
                                    enemy.hp -= player.get("damage")
                                    enemy_hit = True
                                    if enemy.hp <= 0:
                                        score += enemy.score
                                        stdscr.addstr(3, SCREEN_SIZE_X + 2, f"SCORE: {score}")
                                        stdscr.addstr(bullet.y - 1, enemy.x, " ")

                                        if random.randint(0, 100) < player.get("powerup_chance"):
                                            if powerup["x"] == 0 and powerup["y"] == 0:
                                                powerup["x"] = enemy.x
                                                powerup["y"] = enemy.y + 1
                                                #stdscr.addstr(enemy.y + 2, enemy.x, "P")

                                        enemies[bullet.x].remove(enemy)
                                        enemies_raw.pop(0)

                                        del enemy

                        if not enemy_hit:
                            stdscr.addstr(bullet.y, bullet.x, " ")
                            bullet.y += direction
                            stdscr.addstr(bullet.y, bullet.x, bullet.char)
                        else:
                            stdscr.addstr(bullet.y, bullet.x, " ")
                            projectiles.remove(bullet)
                            del bullet

                    else:
                        stdscr.addstr(bullet.y, bullet.x, " ")
                        projectiles.remove(bullet)
                        del bullet
                #stdscr.addstr(player_y - 5, player_x, "X")_



            stdscr.addstr(player["y"], player["x"], "O")

            if player["y"] == powerup["y"] and player["x"] == powerup["x"]:
                powerup["x"] = 0
                powerup["y"] = 0

                message = levelUp()

                stdscr.addstr(4, 30, message)
                stdscr.refresh()
                time.sleep(1)
                stdscr.addstr(4, 30, " " * len(message))

            if 1 <= powerup["x"] < SCREEN_SIZE_X - 1 and 1 <= powerup["y"] < SCREEN_SIZE_Y - 1:
                stdscr.addstr(powerup["y"], powerup["x"], "P")

            for y in boss_laser_rows:
                for x in range(1, SCREEN_SIZE_X - 1):
                    stdscr.addstr(y, x, " ")

            if boss_phase == "laser":
                for y in boss_laser_rows:
                    for x in range(1, SCREEN_SIZE_X - 1):
                        stdscr.addstr(y, x, "-", curses.color_pair(3))

            if boss_phase == "laser" and time.monotonic() > boss_phase_timer:
                boss_phase = "normal"
                boss_laser_rows.clear()

            stdscr.refresh()
            keys_held.clear()
            curses.napms(20)



        stdscr.addstr(4, 30, "LEVEL COMPLETE!")
        stdscr.refresh()
        curses.napms(2000)

    stdscr.clear()
    stdscr.refresh()
    stdscr.addstr(4, 30, "GAME  OVER!")
    stdscr.refresh()

    time.sleep(3)

wrapper(main)