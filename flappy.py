from pygamelib import engine, board_items, constants, functions
from pygamelib.base import Vector2D, Text
from pygamelib.gfx.core import Color, Sprite, Sprixel, Font, SpriteCollection
from pygamelib.gfx.particles import (
    SpriteEmitter,
    EmitterProperties,
    ParticleSprixel,
    Particle,
    ColorParticle,
    ParticleEmitter,
)
from pygamelib.assets import graphics
import time
import random

# WARNING: This is not a state of the art implementation.
# The bulk of this should be in a big wrapping class to avoid global variables.
# The algorithm can use some optimizations.


# Define constants
GRAVITY = Vector2D(300, 0)
# FLAP_COEFFICIENT = 0.075
FLAP_COEFFICIENT = 0.09
OBSTACLES_SPEED = 50
OBSTACLES_HOLE_SIZE = 20
OBSTACLES_GAP_SIZE = 80
OBSTACLES_WIDTH = 12
OBSTACLES_MIN_HEIGHT = 1


# Some useful global variables
obstacles = []
green = Color(0, 255, 0)
red = Color(255, 0, 0)
white = Color(255, 255, 255)
# bird_color = Color(255, 255, 0)
bird_color = Color(0, 0, 255)
# bird_color = white
# sky_blue = Color(0, 142, 253)
sky_blue = Color(113, 197, 208)
sky_blue_sprixel = Sprixel(" ", sky_blue)
big_font = Font("8bits")
wasted_text = Text("WASTED", font=big_font, fg_color=red, bg_color=sky_blue)
# graphic_assets = SpriteCollection.load_json_file("pb_bg.spr")
# city_bg = graphic_assets["pb_bg"]
hd_player = SpriteCollection.load_json_file("player.spr")
ascii_bird_fall = hd_player["bird_fall"]
ascii_bird_flap = hd_player["bird_flap"]
ascii_bird_fall.null_sprixel = Sprixel()
ascii_bird_flap.null_sprixel = Sprixel()

# Speed modificator to increase difficulty as the game goes
obstacles_speed_modificator = 1.0

# Define particle system's properties for the bird explosion
expl_props = EmitterProperties(
    variance=4.0,
    emit_number=1,
    emit_rate=0.01,
    lifespan=1,
    particle=Particle(
        sprixel=ParticleSprixel(graphics.GeometricShapes.BULLET, bg_color=sky_blue),
    ),
    particle_lifespan=150,
)
PARTICLE_GRAVITY = Vector2D(0.1, 0.0)
# Define a global array for the particle emitters
particle_emitters = []


# Define game sprites.

# ascii_bird_fall = Sprite(
#     sprixels=[
#         [
#             Sprixel(" ", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("\\", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("\\", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel(" ", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel(" ", fg_color=bird_color, bg_color=sky_blue),
#         ],
#         [
#             Sprixel(" ", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("<", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("\\", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("\\", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("Q", fg_color=bird_color, bg_color=sky_blue),
#         ],
#     ]
# )

# ascii_bird_flap = Sprite(
#     sprixels=[
#         [
#             Sprixel(" ", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("<", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("/", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("/", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("Q", fg_color=bird_color, bg_color=sky_blue),
#         ],
#         [
#             Sprixel(" ", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("/", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel("/", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel(" ", fg_color=bird_color, bg_color=sky_blue),
#             Sprixel(" ", fg_color=bird_color, bg_color=sky_blue),
#         ],
#     ]
# )

# Performance global structure and text
perf_data = {
    "start_time": time.perf_counter(),
    "frame_count": 0,
    "refresh_count": 0,
}
fps = Text("FPS: 0")


def draw_rectangle(
    game: engine.Game, x: int, y: int, width: int, height: int, color: Color
) -> board_items.Tile:
    # if y + height >= game.screen.height:
    #     height = game.screen.height - y - 1
    s = Sprite(size=[width, height])
    for row in range(0, height):
        for column in range(0, width):
            s.set_sprixel(row, column, Sprixel(" ", color))
    t = board_items.Tile(sprite=s, overlappable=False)
    game.screen.place(t, y, x, 3)
    t.store_position(y, x)
    return t


def generate_new_obstacle(game: engine.Game, color: Color):
    s = game.screen
    hole_pos = random.randint(
        OBSTACLES_HOLE_SIZE,
        game.screen.height - (OBSTACLES_HOLE_SIZE + OBSTACLES_MIN_HEIGHT),
    )
    up = draw_rectangle(
        game, s.width - OBSTACLES_WIDTH, 1, OBSTACLES_WIDTH, hole_pos, color
    )
    setattr(up, "scored", False)
    down = draw_rectangle(
        game,
        s.width - OBSTACLES_WIDTH,
        hole_pos + OBSTACLES_HOLE_SIZE,
        OBSTACLES_WIDTH,
        game.screen.height - hole_pos - OBSTACLES_HOLE_SIZE,
        color,
    )
    obstacles.append((up, down))


def move_player(game: engine.Game, new_row: int):
    # if (
    # game.player.row != new_row and new_row + game.player.height < game.screen.height
    # ):
    if game.player.row != new_row:
        if new_row + game.player.height >= game.screen.height:
            new_row = game.screen.height - game.player.height
        game.screen.delete(game.player.screen_row, game.player.screen_column)
        game.screen.place(
            sky_blue_sprixel, game.player.screen_row, game.player.screen_column
        )
        game.screen.place(game.player, new_row, game.player.screen_column)
        game.player.store_position(new_row, game.player.screen_column)


def move_obstacles(game: engine.Game, dt):
    global obstacles_speed_modificator
    to_remove = []
    for obstacle_pair in obstacles:
        for obstacle in obstacle_pair:
            new_col = round(
                obstacle.column - OBSTACLES_SPEED * obstacles_speed_modificator * dt
            )
            if (
                obstacle == obstacle_pair[0]
                and not obstacle.scored
                and new_col <= game.player.screen_column
            ):
                game.player.value += 1
                # if game.player.value % 5 == 0:
                #     obstacles_speed_modificator += 0.1
                obstacles_speed_modificator += 0.02
                game.score_label.text = str(game.player.value)
                obstacle.scored = True
            game.screen.delete(obstacle.screen_row, obstacle.screen_column)
            game.screen.place(
                sky_blue_sprixel, obstacle.screen_row, obstacle.screen_column
            )
            # if obstacle.column < -obstacle.width:
            if obstacle.column <= 0:
                if obstacle_pair not in to_remove:
                    to_remove.append(obstacle_pair)
            else:
                game.screen.place(obstacle, obstacle.screen_row, new_col)
                obstacle.store_position(obstacle.screen_row, new_col)
    for pair in to_remove:
        obstacles.remove(pair)


def bird_collides_with_obstacle(game: engine.Game):
    for obstacle_pair in obstacles:
        for obstacle in obstacle_pair:
            if game.player.collides_with(obstacle):
                return True


def update_fps(game: engine.Game):
    # We update the performance counters
    if game.show_fps:
        perf_data["frame_count"] += 1
        fps_count = round(
            perf_data["frame_count"] / (time.perf_counter() - perf_data["start_time"]),
            2,
        )
        # and update the label.
        fps.text = f"FPS: {fps_count}"
        perf_data["refresh_count"] += 1
        if perf_data["refresh_count"] >= 10:
            # Force a refresh of the screen every 10 frames.
            game.screen.trigger_rendering()
            perf_data["refresh_count"] = 0


def reset_game(game: engine.Game):
    global obstacles_speed_modificator
    game.player.value = 0
    game.score_label.text = "0"
    game.player.is_alive = True
    game.user_update = update_game
    for obstacle_pair in obstacles:
        for obstacle in obstacle_pair:
            game.screen.delete(obstacle.screen_row, obstacle.screen_column)
            game.screen.place(
                sky_blue_sprixel, obstacle.screen_row, obstacle.screen_column
            )
    obstacles.clear()
    game.screen.delete(
        game.screen.height // 2,
        game.screen.width // 2 - wasted_text.length // 2,
    )
    rt = "Press ENTER to play again or ESC to quit."
    game.screen.delete(
        game.screen.height // 2 + 5,
        game.screen.width // 2 - len(rt) // 2,
    )
    game.screen.place(
        sky_blue_sprixel,
        game.screen.height // 2,
        game.screen.width // 2 - wasted_text.length // 2,
    )
    game.screen.place(
        sky_blue_sprixel,
        game.screen.height // 2 + 5,
        game.screen.width // 2 - len(rt) // 2,
    )
    game.player.last_flap = 0
    game.player.velocity = Vector2D(0, 0)
    game.player.acceleration = Vector2D(0, 0)
    obstacles_speed_modificator = 1.0
    move_player(game, game.screen.height // 2)


def update_paused(game: engine.Game, inkey, dt):
    if inkey.name == "KEY_ENTER":
        reset_game(game)
        generate_new_obstacle(game, green)
        game.run()
    elif inkey.name == "KEY_ESCAPE":
        reset_game(game)
        game.screen.clear_buffers()
        init_welcome_screen(game)
        game.user_update = welcome_screen
        game.run()
    elif inkey == "Q":
        game.stop()
    game.screen.update()


def death_animation_update(game: engine.Game, inkey, dt):
    for _ in range(len(particle_emitters) - 1, -1, -1):
        emt = particle_emitters.pop()
        if emt.finished():
            game.screen.delete(emt.row, emt.column)
            game.screen.place(sky_blue_sprixel, emt.row, emt.column)
            continue
        emt.apply_force(PARTICLE_GRAVITY)
        emt.emit()
        emt.update()
        particle_emitters.append(emt)
    if len(particle_emitters) == 0:
        game.screen.place(
            sky_blue_sprixel, game.player.screen_row, game.player.screen_row
        )
        game.screen.place(
            sky_blue_sprixel, game.player.screen_row - 1, game.player.screen_row
        )
        game.screen.place(
            wasted_text,
            game.screen.height // 2,
            game.screen.width // 2 - wasted_text.length // 2,
            2,
        )
        rt = Text(
            "Press ENTER to play again or ESC to quit.",
            white,
            sky_blue,
            style=constants.BOLD,
        )
        game.screen.place(
            rt,
            game.screen.height // 2 + 5,
            game.screen.width // 2 - rt.length // 2,
            2,
        )
        game.pause()
    game.screen.force_update()


def update_game(game: engine.Game, inkey, dt):

    # First, we process the inputs
    if inkey == "Q":
        game.stop()
    elif inkey == " ":
        game.player.sprite = ascii_bird_flap
        game.screen.trigger_rendering()
        game.player.last_flap = 0
        game.player.acceleration.y = 0
        game.player.velocity.y = -GRAVITY.y * FLAP_COEFFICIENT
    if game.player.last_flap > 0.2:
        game.player.sprite = ascii_bird_fall
        game.screen.trigger_rendering()
        game.player.last_flap = 0
    else:
        game.player.last_flap += dt
    if inkey != " ":
        game.player.acceleration += GRAVITY * dt * 2

    # Cap the acceleration
    if game.player.acceleration.y > GRAVITY.y:
        game.player.acceleration.y = GRAVITY.y
    # Applying gravity/forces
    game.player.velocity += game.player.acceleration * dt
    new_row = game.player.screen_row + game.player.velocity.row * dt
    new_row = functions.clamp(new_row, 0, game.screen.height - game.player.height)
    move_player(game, round(new_row))

    # Move obstacles
    move_obstacles(game, dt)

    # Check if dead
    if (
        bird_collides_with_obstacle(game)
        or game.player.screen_row + game.player.height >= game.screen.height
    ):
        game.player.is_alive = False
        game.user_update = death_animation_update
        game.player.velocity.row = 0
        game.player.velocity.column = 0
        game.screen.delete(game.player.screen_row, game.player.screen_column)
        game.screen.place(
            sky_blue_sprixel, game.player.screen_row, game.player.screen_column
        )
        expl_props.row = game.player.screen_row - 1
        expl_props.column = game.player.screen_column
        sprite_emitter = SpriteEmitter(
            sprite=game.player.sprite, emitter_properties=expl_props
        )
        game.screen.place(sprite_emitter, expl_props.row - 1, expl_props.column, 2)
        particle_emitters.append(sprite_emitter)
    # else:
    #     # Check score
    #     for obstacle_pair in obstacles:
    #         o = obstacle_pair[0]
    #         if o.screen_column == game.player.screen_column:
    #             game.player.value += 1
    #             game.score_label.text = str(game.player.value)
    #     game.screen.place(f"Score: {game.player.value}", 0, 0)
    # Generate new obstacle
    if obstacles[-1][0].column < game.screen.width - (
        OBSTACLES_WIDTH + OBSTACLES_GAP_SIZE
    ):
        generate_new_obstacle(game, green)

    update_fps(game)

    # And finally we update the screen (refreshed on demand)
    game.screen.update()


def init_game(game: engine.Game):

    for r in range(game.screen.height):
        for c in range(game.screen.width):
            game.screen.place(sky_blue_sprixel, r, c)
    # game.screen.place(city_bg, game.screen.height - city_bg.height, 0, 1)
    # setattr(city_bg, "screen_column", 0)
    # setattr(city_bg, "screen_row", game.screen.height - city_bg.height)
    # setattr(city_bg, "current_column", 0.0)
    setattr(game.player, "last_flap", 0)
    setattr(game.player, "velocity", Vector2D(0, 0))
    setattr(game.player, "acceleration", Vector2D(0, 0))
    setattr(
        game, "score_label", Text("0", font=big_font, fg_color=white, bg_color=sky_blue)
    )
    # I want to use the sugar from BoardItem even though I'm not using a board.
    # Mainly for collision detection.
    game.player.store_position(game.screen.vcenter, round(game.screen.width / 3))
    if game.show_fps:
        game.screen.place(fps, 0, game.screen.width - fps.length - 5)
        game.fps_column = game.screen.width - fps.length - 5
    generate_new_obstacle(game, green)
    game.screen.place(
        game.score_label, 0, game.screen.hcenter - round(big_font.glyph("0").width / 2)
    )
    game.screen.place(game.player, game.screen.vcenter, round(game.screen.width / 3))


def init_welcome_screen(game: engine.Game):
    title = Text("pyscii bird", white, font=big_font)
    game.screen.place(title, 5, game.screen.hcenter - title.length // 2)
    setattr(game, "current_menu_index", 0)
    setattr(game, "menu_items", [])
    game.menu_items.append(Text("Play", white, style=constants.BOLD))
    game.menu_items.append(
        Text(f"Show FPS [{'ON' if game.show_fps else 'OFF'}]", white)
    )
    if game.show_fps:
        if game.fps_column != 0:
            game.screen.delete(0, game.fps_column)
        game.screen.place(fps, 0, game.screen.width - fps.length - 5)
        game.fps_column = game.screen.width - fps.length - 5
    game.menu_items.append(Text("Quit", white))

    base_row = 5 + big_font.height + 5
    base_column = game.screen.width // 2 - 6
    for i in range(len(game.menu_items)):
        game.screen.place(
            game.menu_items[i],
            base_row + i,
            base_column,
            2,
        )
    game.welcome_screen_initialized = True


def welcome_screen(game: engine.Game, inkey, dt: float):

    if not game.welcome_screen_initialized:
        init_welcome_screen(game)

    if inkey.name == "KEY_ENTER":
        if game.current_menu_index == 0:
            init_game(game)
            game.user_update = update_game
        elif game.current_menu_index == 1:
            game.show_fps = not game.show_fps
            game.menu_items[1].text = f"Show FPS [{'ON' if game.show_fps else 'OFF'}]"
            if game.show_fps:
                perf_data["start_time"] = time.perf_counter()
                perf_data["frame_count"] = 0
                game.screen.place(fps, 0, game.screen.width - fps.length - 5)
                game.fps_column = game.screen.width - fps.length - 5
            else:
                game.screen.delete(0, game.fps_column)
            game.screen.trigger_rendering()
        elif game.current_menu_index == 2:
            game.stop()
    elif inkey == "Q":
        game.stop()
    elif inkey == "s" or inkey.name == "KEY_DOWN":
        game.menu_items[game.current_menu_index].style = ""
        game.current_menu_index = (game.current_menu_index + 1) % len(game.menu_items)
        game.menu_items[game.current_menu_index].style = constants.BOLD
        game.screen.trigger_rendering()
    elif inkey == "z" or inkey == "w" or inkey.name == "KEY_UP":
        game.menu_items[game.current_menu_index].style = ""
        game.current_menu_index = (game.current_menu_index - 1) % len(game.menu_items)
        game.menu_items[game.current_menu_index].style = constants.BOLD
        game.screen.trigger_rendering()
    update_fps(game)
    game.screen.update()


def main():
    # Create a new game instance.
    game = engine.Game.instance(
        name="PYSCII Bird",
        user_update=welcome_screen,
        user_update_paused=update_paused,
        mode=constants.MODE_RT,
        player=board_items.ComplexPlayer(
            sprite=ascii_bird_fall, value=0, null_sprixel=Sprixel()
        ),
    )
    setattr(game, "welcome_screen_initialized", False)
    setattr(game, "show_fps", False)
    setattr(game, "fps_column", 0)
    setattr(game.player, "is_alive", True)
    game.run()


if __name__ == "__main__":
    main()