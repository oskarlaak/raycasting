# TO DO:
# Redo the secret wall moving logic
# Main menu system
# Try to remove all shadows from sprites
# Make boss health bar update() func and add it to update_gameobjects()

# Extras:
# Move sounds to different folders
# Particles - blood, bullets etc
# Boss projectiles
# Level number HUD
# Has key HUD
# Create levels

# Problems:
# When you instantly pause game crashes
# Shooting is disabled now
# Portals can't attach to the same block but different sides

# NOTES:
# Game's tick rate is capped at 30
# All timed events are tick based
# All angles are in radians
# Normal enemies can only travel through Dynamic doors, bosses can travel through all types of doors
# There is no support for multiple bosses in one level
# Game font's default size is 32, but it can also display sizes 16 and 24
# Push walls and doors need to be placed in between wall for them to display and work properly
# Every sky texture will repeat it's texture 4 times around the player

# Sound Channels:
# 0 = pickup, environment sounds (doors, pushwalls, explosive barrels, end switches)
# 1 = player's weapon sounds
# 2 - 6 = normal enemy sounds
# 7 = boss sounds


class Colour:
    black = (0, 0, 0)
    dark_grey = (32, 32, 32)
    grey = (128, 128, 128)
    white = (255, 255, 255)
    red = (255, 0, 0)
    green = (0, 255, 0)
    dark_green = (0, 128, 0)
    blue = (0, 0, 255)
    yellow = (255, 255, 0)


class Player:
    max_hp = 100
    max_ammo = 100
    speed = 0.15  # Must be < half_hitbox, otherwise player can clip through walls
    half_hitbox = 0.2

    def __init__(self):
        self.saved_weapon_loadout = [5]

    def setup(self, pos, angle):  # Called every time level (re)starts
        self.x, self.y = pos
        self.viewangle = angle
        self.dir_x = cos(self.viewangle)
        self.dir_y = sin(self.viewangle)
        self.hp = Player.max_hp
        self.ammo = 20
        self.has_key = False
        self.weapon_nr = len(WEAPONS) - 1
        self.weapon_loadout = self.saved_weapon_loadout[:]

    def save_weapon_loadout(self):
        self.saved_weapon_loadout = self.weapon_loadout[:]

    def add_ammo(self, amount):
        self.ammo += amount
        if self.ammo > Player.max_ammo:
            self.ammo = PLAYER.max_ammo

    def add_hp(self, amount):
        self.hp += amount
        if self.hp > Player.max_hp:
            self.hp = PLAYER.max_hp

    def rotate(self, radians):
        self.viewangle = fixed_angle(self.viewangle + radians)

    def hurt(self, damage, enemy):
        EFFECTS.update(Colour.red)
        self.hp -= damage
        if self.hp <= 0:
            for channel_id in range(8):
                pygame.mixer.Channel(channel_id).fadeout(150)
            LEVEL.restart(enemy)

    def handle_movement(self):
        # Checks for movement (WASD)
        keys_pressed = pygame.key.get_pressed()
        self.dir_x = cos(self.viewangle)
        self.dir_y = sin(self.viewangle)
        old_pos = (self.x, self.y)

        if keys_pressed:
            x_move = 0
            y_move = 0
            if keys_pressed[K_w]:
                x_move += self.dir_x
                y_move += self.dir_y
            if keys_pressed[K_a]:
                x_move += self.dir_y
                y_move += -self.dir_x
            if keys_pressed[K_s]:
                x_move += -self.dir_x
                y_move += -self.dir_y
            if keys_pressed[K_d]:
                x_move += -self.dir_y
                y_move += self.dir_x

            if abs(x_move) > 0.0000001 or abs(y_move) > 0.0000001:  # 0.0000001 avoids calculation errors
                moving_angle = atan2(y_move, x_move)
                x_move = cos(moving_angle)
                y_move = sin(moving_angle)
                PLAYER.move(x_move * Player.speed, y_move * Player.speed)

        self.total_movement = sqrt(squared_dist(old_pos, (self.x, self.y)))

    def move(self, x_move, y_move):
        def one_point_collision(y, x):
            if int(x - x_move) == x - x_move:
                return True, False
            if int(y - y_move) == y - y_move:
                return False, True

            x_offset = x - int(x)
            y_offset = y - int(y)

            # Distance to closest round(x/y)
            delta_x = abs(round(x_offset) - x_offset)
            delta_y = abs(round(y_offset) - y_offset)
            if delta_x < delta_y:
                return True, False
            else:
                return False, True

        # Start off by moving player position
        self.x += x_move
        self.y += y_move

        # Hitbox sides
        right = self.x + Player.half_hitbox
        left = self.x - Player.half_hitbox
        down = self.y + Player.half_hitbox
        up = self.y - Player.half_hitbox

        # Hitbox corners
        # Everything that player can walk on is less than 0 on tilemap
        # So these will be True if there is a collision
        down_right = TILEMAP[int(down)][int(right)] > 0
        down_left = TILEMAP[int(down)][int(left)] > 0
        up_right = TILEMAP[int(up)][int(right)] > 0
        up_left = TILEMAP[int(up)][int(left)] > 0

        # Find the collision type
        x_collision = False
        y_collision = False

        if down_right:
            if up_left:
                x_collision = True
                y_collision = True
            elif down_left:
                y_collision = True
                if up_right:
                    x_collision = True
            elif up_right:
                x_collision = True
            else:
                x_collision, y_collision = one_point_collision(down, right)

        elif up_left:
            if down_left:
                x_collision = True
                if up_right:
                    y_collision = True
            elif up_right:
                y_collision = True
            else:
                x_collision, y_collision = one_point_collision(up, left)

        elif down_left:
            if up_right:
                x_collision = True
                y_collision = True
            else:
                x_collision, y_collision = one_point_collision(down, left)

        elif up_right:
            x_collision, y_collision = one_point_collision(up, right)

        # Apply changes to x/y if there was a collision
        if x_collision:
            if self.x - int(self.x) < Player.half_hitbox:
                self.x = int(self.x) + Player.half_hitbox
            else:
                self.x = ceil(self.x) - Player.half_hitbox

        if y_collision:
            if self.y - int(self.y) < Player.half_hitbox:
                self.y = int(self.y) + Player.half_hitbox
            else:
                self.y = ceil(self.y) - Player.half_hitbox


class Door:
    type = 'Normal'
    speed = 0.065
    open_ticks = 90

    def __init__(self, map_pos, tile_value):
        self.x, self.y = map_pos
        self.value = tile_value

        self.ticks = 0
        self.closed_state = 1  # 1 is fully closed, 0 is fully opened
        self.state = 0
        self.locked = False

    def start_opening(self):
        self.state = 1

    def room_to_close(self):
        # Checking if player is not in door's way
        safe_dist = 0.5 + Player.half_hitbox
        return abs(self.x + 0.5 - PLAYER.x) > safe_dist or abs(self.y + 0.5 - PLAYER.y) > safe_dist

    def start_closing_if_needed(self):
        self.ticks += 1
        if self.ticks >= Door.open_ticks and self.room_to_close():
            TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
            self.ticks = 0
            self.state += 1

    def move(self):
        if self.state > 0:
            if self.state == 1:  # Opening
                if self.closed_state == 1:
                    play_sound(self.open_sound, 0, (self.x + 0.5, self.y + 0.5))
                self.closed_state -= Door.speed
                if self.closed_state <= 0:
                    TILEMAP[self.y][self.x] = 0  # Make tile walkable
                    self.closed_state = 0
                    self.state += 1

            elif self.state == 2:  # Staying open
                self.start_closing_if_needed()

            elif self.state == 3:  # Closing
                if self.closed_state == 0:
                    play_sound(self.close_sound, 0, (self.x + 0.5, self.y + 0.5))
                self.closed_state += Door.speed
                if self.closed_state >= 1:
                    self.closed_state = 1
                    self.state = 0


class BossDoor(Door):
    # Boss door is a one way door that stays unlocked until both of the door sides have been visited
    # This makes sure that once you've gone to the other side of the door there's no going back
    # Going through the door also automatically "wakes up" the boss in the level if there is one
    type = 'Boss'

    def start_opening(self):
        self.state = 1
        if TILEMAP[self.y + 1][self.x] > 0:
            if PLAYER.x < self.x:  # Door's center x is actually 0.5 off but it doesn't matter here
                self.trigger_tile = (self.x + 1, self.y)
            else:
                self.trigger_tile = (self.x - 1, self.y)
        else:
            if PLAYER.y < self.y:  # Door's center y is actually 0.5 off but it doesn't matter here
                self.trigger_tile = (self.x, self.y + 1)
            else:
                self.trigger_tile = (self.x, self.y - 1)

    def start_closing_if_needed(self):
        self.ticks += 1
        if self.room_to_close():
            if (int(PLAYER.x), int(PLAYER.y)) == self.trigger_tile:
                # "Spawn boss"
                TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                self.locked = True
                self.state += 1
                for e in ENEMIES:
                    if e.type == 'Boss':
                        BOSSHEALTHBAR.start_showing(e)
                        e.chasing = True
                        break

            elif self.ticks >= Door.open_ticks:
                TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                self.ticks = 0
                self.state += 1


class PushWall:
    speed = 0.025

    def __init__(self, map_pos, tile_value):
        self.x, self.y = map_pos
        self.value = tile_value
        self.tile_offset = 0
        self.activated = False

    def start_moving(self):
        play_sound(self.sound, 0, (self.x + 0.5, self.y + 0.5))
        self.activated = True
        # Calculate the direction the push wall needs to move when activated
        if TILEMAP[self.y + 1][self.x] > 0:
            self.move_dir_y = 0
            if PLAYER.x < self.x:  # Push wall's center x is actually 0.5 off but it doesn't matter here
                self.move_dir_x = 1
            else:
                self.move_dir_x = -1
        else:
            self.move_dir_x = 0
            if PLAYER.y < self.y:  # Push wall's center y is actually 0.5 off but it doesn't matter here
                self.move_dir_y = 1
            else:
                self.move_dir_y = -1

    def move(self):
        if self.activated and TILEMAP[self.y + self.move_dir_y][self.x + self.move_dir_x] <= 0:
            self.tile_offset += self.speed
            if self.tile_offset >= 1:
                self.tile_offset = 0
                TILEMAP[self.y][self.x] = 0  # Make tile walkable
                EMPTY_TILES.add((self.x, self.y))
                PUSH_WALL_TILES.remove((self.x, self.y))
                self.x += self.move_dir_x
                self.y += self.move_dir_y
                TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                EMPTY_TILES.remove((self.x, self.y))
                PUSH_WALL_TILES.add((self.x, self.y))


class ThinWall:
    def __init__(self, map_pos):
        def wall_or_thin_wall(tile_value):
            return TILE_VALUES_INFO[tile_value].type == 'Wall' or TILE_VALUES_INFO[tile_value].type == 'Thin Wall'

        self.x, self.y = map_pos
        left_side_value = TILEMAP[self.y][self.x - 1]
        right_side_value = TILEMAP[self.y][self.x + 1]
        top_side_value = TILEMAP[self.y - 1][self.x]
        bottom_side_value = TILEMAP[self.y + 1][self.x]

        if wall_or_thin_wall(left_side_value) and wall_or_thin_wall(right_side_value):
            self.vertical = False
        elif wall_or_thin_wall(top_side_value) and wall_or_thin_wall(bottom_side_value):
            self.vertical = True
        elif wall_or_thin_wall(left_side_value) or wall_or_thin_wall(right_side_value):
            self.vertical = False
        else:
            self.vertical = True


class Portal:
    def __init__(self, blue):
        if blue:
            self.texture = Portal.blue_texture
        else:
            self.texture = Portal.red_texture
        self.created = False

    def create_portal(self):
        collison_x, collison_y = raycast((PLAYER.x, PLAYER.y), PLAYER.viewangle)

        if collison_x == int(collison_x):
            vertical = True
            if (collison_x, int(collison_y)) in EMPTY_TILES:
                side = 1  # Portal on right side
            else:
                side = 0  # Portal on left side
            map_x = collison_x - side
            map_y = int(collison_y)
        else:
            vertical = False
            if (int(collison_x), collison_y) in EMPTY_TILES:
                side = 1  # Portal on bottom side
            else:
                side = 0  # Portal on top side
            map_x = int(collison_x)
            map_y = collison_y - side

        if (map_x, map_y) not in DOOR_TILES and (map_x, map_y) not in PUSH_WALL_TILES:
            self.created = True
            self.map_x = map_x
            self.map_y = map_y
            self.vertical = vertical
            self.side = side


class WeaponModel:
    channel_id = 1
    switch_ticks = 6  # Needs to be even number

    def __init__(self):
        self.shooting = False
        self.switching = False

        self.size = int(D_W * 0.75)
        self.ticks = 0
        self.column = 0
        self.display_y = 0
        self.update()

    def shoot(self, weapon):
        def get_shootable_things():
            shootable_things = []
            for sprite in ENEMIES + EXPLOSIVES:
                if sprite.visible_to_player and sprite.hp:
                    shootable_things.append(sprite)
            shootable_things.sort(key=lambda x: x.dist_squared)  # Sort for closest dist first
            return shootable_things

        def bullet_hitscan(shootable_things, x_spread=0, max_range_squared=False):
            # Each bullet can hit maximum 3 enemies
            hit = False
            bullet_x_pos = H_W + x_spread
            damage_multiplier = 1
            for sprite in shootable_things:
                if sprite.start_x < bullet_x_pos < sprite.end_x:
                    if not max_range_squared or sprite.dist_squared < max_range_squared:
                        if sprite.hp:
                            hit = True
                            sprite.hurt(weapon.damage * damage_multiplier)
                            if damage_multiplier == 0.25:
                                break
                            else:
                                damage_multiplier /= 2
                    else:
                        break
            return hit

        # Shooting animation system
        self.ticks += 1
        if self.ticks == int(weapon.fire_delay / weapon.animation_frames):
            self.ticks = 0
            self.column += 1

            if self.column > weapon.animation_frames:  # If finished shot animation
                # If weapon automatic and mouse down
                if weapon.automatic and pygame.mouse.get_pressed()[0] and PLAYER.ammo >= self.weapon.ammo_consumption:
                    self.column = 1  # Keep going
                else:
                    self.column = 0  # Ends animation
                    self.shooting = False

            if self.column == weapon.shot_column:
                weapon_sound = self.weapon.sounds.fire
                PLAYER.add_ammo(-self.weapon.ammo_consumption)
                shootable_things = get_shootable_things()

                if weapon.type == 'Melee':
                    if bullet_hitscan(shootable_things, max_range_squared=weapon.range_squared):
                        weapon_sound = self.weapon.sounds.hit

                elif weapon.type == 'Hitscan':
                    bullet_hitscan(shootable_things, x_spread=random.randint(-weapon.max_x_spread, weapon.max_x_spread))

                elif weapon.type == 'Shotgun':
                    x_spread_difference = (weapon.max_x_spread * 2) / (weapon.shot_bullets - 1)
                    for i in range(weapon.shot_bullets):
                        bullet_hitscan(shootable_things, x_spread=-weapon.max_x_spread + round(i * x_spread_difference))

                play_sound(weapon_sound, WeaponModel.channel_id)

    def switch_weapons(self):
        self.ticks += 1
        if self.ticks == WeaponModel.switch_ticks / 2:
            PLAYER.weapon_nr = self.switching  # Switches weapon model when halfway through
            #self.sound_channel.stop()

        if self.ticks <= WeaponModel.switch_ticks / 2:
            self.display_y += int(self.size / WeaponModel.switch_ticks)
        elif self.ticks <= WeaponModel.switch_ticks:
            self.display_y -= int(self.size / WeaponModel.switch_ticks)
        else:
            self.ticks = 0
            self.switching = False

    def update(self):
        self.weapon = WEAPONS[PLAYER.weapon_nr]

        if self.shooting:
            self.shoot(self.weapon)

        elif self.switching:
            self.switch_weapons()

    def draw(self):
        #pygame.draw.line(DISPLAY, (0, 255, 0), (H_W - self.weapon.max_x_spread, H_H - 10),
        #                 (H_W - self.weapon.max_x_spread, H_H + 10), 2)
        #pygame.draw.line(DISPLAY, (0, 255, 0), (H_W + self.weapon.max_x_spread, H_H - 10),
        #                 (H_W + self.weapon.max_x_spread, H_H + 10), 2)
        weapon_image = self.weapon.weapon_sheet.subsurface(self.weapon.cell_size * self.column, 0,
                                                           self.weapon.cell_size, self.weapon.cell_size)
        weapon_image = pygame.transform.scale(weapon_image, (self.size, self.size))
        DISPLAY.blit(weapon_image, ((D_W - self.size) / 2, D_H - self.size + self.display_y))


class Effects:
    def __init__(self):
        self.alpha = 0

    def update(self, colour):
        self.colour = colour
        self.alpha = 128

    def draw(self):
        if self.alpha:
            effect = pygame.Surface((D_W, D_H))
            effect.set_alpha(self.alpha)
            effect.fill(self.colour)
            DISPLAY.blit(effect, (0, 0))
            self.alpha -= 16


class Message:
    font_size = 16
    start_y = 70  # y position that the top message appears at
    display_ticks = 150  # How many ticks message stays on screen
    fade_speed = 15  # Rate at which text alpha decreases after display_ticks has gone down to 0
    max_amount = 10  # Max amount of messages that can be on screen

    def __init__(self, text, colour=Colour.white):
        self.text = text
        self.colour = colour
        self.ticks = 0
        self.alpha = 255
        if len(MESSAGES) == Message.max_amount:
            del MESSAGES[0]

    def update(self):
        if self.ticks == Message.display_ticks:
            self.alpha -= Message.fade_speed
            if self.alpha <= 0:
                MESSAGES.remove(self)
        else:
            self.ticks += 1

    def draw(self):
        index = MESSAGES.index(self)
        draw_y = Message.start_y + abs(index - len(MESSAGES) + 1) * Message.font_size
        message = render_text(self.text, self.colour, self.alpha, Message.font_size)
        DISPLAY.blit(message, (HUD_SAFEZONE, draw_y))


class CameraPlane:
    def __init__(self, fov):
        # Creates a list of rayangle offsets which will be added to player's viewangle when sending rays every frame
        # Bc these offsets do not change during the game, they are calculated before the game starts
        # Offsets are calculated so that each ray will be equal distance away from previous ray on the camera plane
        # Of course in 2D rendering camera plane is actually a line
        # FOV has to be < pi (and not <= pi) for it to work properly
        # Also calculates camera plane's distance to later calculate sprite's display_pos

        self.rayangle_offsets = []

        camera_plane_len = 1
        camera_plane_start = -camera_plane_len / 2
        camera_plane_step = camera_plane_len / D_W

        self.dist = camera_plane_len / 2 / tan(fov / 2)
        for x in range(D_W):
            camera_plane_pos = camera_plane_start + x * camera_plane_step

            angle = atan2(camera_plane_pos, self.dist)
            self.rayangle_offsets.append(angle)

        if FLOOR_RES:
            # Calculates horizontal floorline's edge distance and step distance for every y position below H_H
            self.floor_lookup_table = []
            for y in range(H_H + 1, D_H):  # Starts at H_H + 1 bc H_H would be infinitely far away
                perp_dist = Drawable.constant / ((y - H_H) * 2)
                dist = perp_dist / cos(FOV / 2)
                step_dist = perp_dist * tan(FOV / 2) / H_W
                self.floor_lookup_table.append((y, dist, step_dist * FLOOR_RES))


class Drawable:
    def calc_cropping_height(self):
        if self.height > D_H:
            # Based on image height, get cropping_height
            # Adjust height if cropping_height < TEXTURE_SIZE

            # Calculate how much of height is needed
            # Calculate the ideal cropping height
            # Calculate the actual cropping height which will be the closest even number rounding up perfect_height
            amount_of_height_needed = D_H / self.height
            perfect_height = TEXTURE_SIZE * amount_of_height_needed
            self.cropping_height = ceil(perfect_height / 2) * 2
            if self.cropping_height < TEXTURE_SIZE:
                self.height = int(self.cropping_height / perfect_height * D_H)
        else:
            self.cropping_height = TEXTURE_SIZE


class WallColumn(Drawable):
    def __init__(self, texture, column, perp_dist, display_x):
        self.perp_dist = perp_dist
        self.height = int(Drawable.constant / self.perp_dist)
        self.calc_cropping_height()
        self.image = texture.subsurface((column, (TEXTURE_SIZE - self.cropping_height) / 2, 1, self.cropping_height))
        self.display_x = display_x
        self.display_y = int((D_H - self.height) / 2)

    def draw(self):
        DISPLAY.blit(pygame.transform.scale(self.image, (WALL_RES, self.height)), (self.display_x, self.display_y))


class Sprite(Drawable):
    animation_ticks = 5  # Enemy animation frames delay

    def update_for_drawing(self, angle_from_player=None):
        # Requires delta_(x/y), dist_squared
        self.visible_to_player = False
        if self.dist_squared < MAX_DRAW_DIST_SQUARED:
            self.perp_dist = self.delta_x * PLAYER.dir_x + self.delta_y * PLAYER.dir_y
            if self.perp_dist > 0:
                if not angle_from_player:
                    angle_from_player = atan2(self.delta_y, self.delta_x)
                self.display_pos = H_W + int(tan(angle_from_player - PLAYER.viewangle) * CAMERA_PLANE.dist * D_W)

                self.width = self.height = round(Drawable.constant / self.perp_dist / 2) * 2  # Needs to be even number
                self.calc_start_and_end_x()
                if self.start_x is not None and self.end_x is not None:
                    self.calc_cropping_height()
                    self.visible_to_player = True

    def calc_start_and_end_x(self):
        # Requires display_pos, width and perp_dist
        self.start_x = None
        self.end_x = None

        # Find start and end x if they exist
        left_side = int(self.display_pos - self.width / 2)
        right_side = left_side + self.width
        if left_side < D_W and right_side > 0:
            if left_side < 0:
                left_side = 0
            if right_side > D_W:
                right_side = D_W

            for w in WALLS[left_side:right_side]:  # Go from left to right
                if w and self.perp_dist < w.perp_dist:  # If sprite in front of wall
                    self.start_x = w.display_x
                    break
            for w in WALLS[right_side:left_side:-1]:  # Go from right to left
                if w and self.perp_dist < w.perp_dist:  # If sprite in front of wall
                    self.end_x = w.display_x
                    break


class Object(Sprite):
    def __init__(self, sprite, pos):
        self.x, self.y = pos
        self.sprite = sprite

    def update(self):
        self.delta_x = self.x - PLAYER.x
        self.delta_y = self.y - PLAYER.y
        self.dist_squared = self.delta_x**2 + self.delta_y**2
        self.update_for_drawing()

    def draw(self):
        cropping_rect = (
            ((self.start_x - self.display_pos) / self.width + 0.5) * TEXTURE_SIZE,
            (TEXTURE_SIZE - self.cropping_height) / 2,
            (self.end_x - self.start_x) / self.width * TEXTURE_SIZE,
            self.cropping_height
        )
        try:
            DISPLAY.blit(
                pygame.transform.scale(self.sprite.subsurface(cropping_rect), (self.end_x - self.start_x, self.height)),
                (self.start_x, (D_H - self.height) / 2)
            )
        except pygame.error as error:
            print('Error occurred scaling object: {}'.format(error))
            print('width: {}'.format(self.end_x - self.start_x))
            print('height: {}'.format(self.height))


class ExplodingBarrel(Object):
    damage = 100
    damage_frame = 2
    squared_range = 3**2

    def __init__(self, sprite, pos):
        self.x, self.y = pos
        self.full_sprite = sprite
        self.explosion_frames = int(sprite.get_width() / TEXTURE_SIZE)
        self.explosion_frame = 0
        self.anim_ticks = 0
        self.hp = 1  # Every shootable thing needs to have hp

    def hurt(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.explosion_frame += 1
            play_sound(self.sound, 0, (self.x, self.y), self.dist_squared)

    def do_damage(self):
        if self.dist_squared < ExplodingBarrel.squared_range:
            damage = int((1 - (self.dist_squared / ExplodingBarrel.squared_range)) * ExplodingBarrel.damage)
            PLAYER.hurt(damage, self)
        for hittable_object in ENEMIES + EXPLOSIVES:
            if hittable_object.hp:
                object_dist_squared = squared_dist((self.x, self.y), (hittable_object.x, hittable_object.y))
                if object_dist_squared < ExplodingBarrel.squared_range:
                    damage = int((1 - (object_dist_squared / ExplodingBarrel.squared_range)) * ExplodingBarrel.damage)
                    hittable_object.hurt(damage)

    def update(self):
        if self.explosion_frame:
            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0
                self.explosion_frame += 1
                if self.explosion_frame == ExplodingBarrel.damage_frame:
                    self.do_damage()
                if self.explosion_frame == self.explosion_frames:
                    for c, explosive in enumerate(EXPLOSIVES):
                        if (self.x, self.y) == (explosive.x, explosive.y):
                            del EXPLOSIVES[c]
                            TILEMAP[int(self.y)][int(self.x)] = 0
                            break
        super().update()

    def draw(self):
        self.sprite = self.full_sprite.subsurface((self.explosion_frame * TEXTURE_SIZE, 0, TEXTURE_SIZE, TEXTURE_SIZE))
        super().draw()


class Enemy(Sprite):
    looting_pulse_speed = 20
    looting_colour = Colour.yellow

    def __init__(self, spritesheet, pos):
        self.type = 'Normal'
        self.x, self.y = pos
        self.step_x = self.x
        self.step_y = self.y
        self.home = int(self.x), int(self.y)
        self.viewangle = 0

        self.sheet = spritesheet
        self.row = 0  # Spritesheet row
        self.column = 0  # Spritesheet column

        self.target_tile = self.home
        self.status = 'default'  # (default, shooting, hit, dead)
        self.chasing = False
        self.appeared = False

        # Take attributes from ENEMY_INFO based on spritesheet
        self.channel_id = ENEMY_INFO[self.sheet].channel_id
        self.channel = pygame.mixer.Channel(self.channel_id)
        self.sounds = ENEMY_INFO[self.sheet].sounds
        self.hp = ENEMY_INFO[self.sheet].hp
        self.speed = ENEMY_INFO[self.sheet].speed
        self.wandering_radius = ENEMY_INFO[self.sheet].wandering_radius
        self.shooting_range_squared = ENEMY_INFO[self.sheet].shooting_range_squared
        self.looting_ammo = ENEMY_INFO[self.sheet].looting_ammo
        self.damage_multiplier = ENEMY_INFO[self.sheet].damage_multiplier
        self.accuracy = ENEMY_INFO[self.sheet].accuracy
        self.pain_chance = ENEMY_INFO[self.sheet].pain_chance
        self.patience = ENEMY_INFO[self.sheet].patience
        self.running_rows = ENEMY_INFO[self.sheet].running_rows
        self.death_frames = ENEMY_INFO[self.sheet].death_frames
        self.hit_row = ENEMY_INFO[self.sheet].hit_row
        self.shooting_frames = ENEMY_INFO[self.sheet].shooting_frames
        self.shot_columns = ENEMY_INFO[self.sheet].shot_columns
        self.shooting_row = ENEMY_INFO[self.sheet].shooting_row

        # Timed events tick variables (frames passed since some action)
        self.stationary_ticks = 0
        self.anim_ticks = 0

        self.dead_image = self.sheet.subsurface(
            ((self.death_frames - 1) * TEXTURE_SIZE, self.hit_row * TEXTURE_SIZE, TEXTURE_SIZE, TEXTURE_SIZE)
        )
        if self.looting_ammo:
            self.looted = False
            self.outline_alpha = 0
            self.outline_image = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
            self.outline_image.set_colorkey(Colour.black)
            for point in pygame.mask.from_surface(self.dead_image).outline():
                self.outline_image.set_at(point, Enemy.looting_colour)
        else:
            self.looted = True

    def __eq__(self, other):
        return self.home == other.home

    def get_home_room(self):
        # Makes a self.home_room list which contains all the map points in his room

        def get_unvisited(pos):
            # Gets new unvisited points
            pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            for pos_offset in pos_offsets:
                pos_x = pos[0] + pos_offset[0]
                pos_y = pos[1] + pos_offset[1]
                if (pos_x, pos_y) not in visited + unvisited and self.map_empty(pos_x, pos_y):
                    unvisited.append((pos_x, pos_y))

        visited = [(self.home[0], self.home[1])]
        unvisited = []
        get_unvisited((self.home[0], self.home[1]))

        while unvisited:  # While there is unscanned/unvisited points
            current = unvisited[0]  # Get new point
            del unvisited[0]  # Delete it from unvisited bc it's about to get visited
            visited.append(current)  # Add point to visited
            get_unvisited(current)  # Scan new points from that location

        self.home_room = []
        for room_point in visited:
            if squared_dist(self.home, room_point) <= self.wandering_radius**2:
                self.home_room.append(room_point)

    def calc_row_and_column(self, moved):
        angle = fixed_angle(self.viewangle - self.angle_from_player)
        self.column = round(angle / (pi / 4)) + 4
        if self.column == 8:
            self.column = 0

        if moved:
            if self.row not in self.running_rows:
                self.row = 1

            # Cycle through running animations
            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0
                self.row += 1
                if self.row not in self.running_rows:
                    self.row = 1
        else:
            self.row = 0
            self.anim_ticks = 0

    def can_step(self, step_x, step_y):
        # If enemy with decent shooting_range really close to player - don't step
        if self.shooting_range_squared > 2 and (int(PLAYER.x), int(PLAYER.y)) == (int(step_x), int(step_y)):
            return False

        for e in ENEMIES:
            if not self == e and e.hp:  # Ignore self and dead enemies
                if (int(e.x), int(e.y)) == (int(step_x), int(step_y)):  # If enemy in way
                    return False
        return True

    def map_empty(self, x, y):
        if TILEMAP[int(y)][int(x)] <= 0:
            return True
        elif (int(x), int(x)) in DOOR_TILES and TILE_VALUES_INFO[TILEMAP[int(y)][int(x)]].desc == 'Dynamic':
            return True
        else:
            return False

    def get_nearby_alerted_enemy(self):
        for e in ENEMIES:
            if e.chasing and not self == e and can_see((self.x, self.y), (e.x, e.y)):
                    return e
        return None

    def can_see_player_sides(self):
        if PLAYER.ammo or len(PLAYER.weapon_loadout) > 1:
            angle = fixed_angle(self.angle_from_player + pi / 2)
            x = cos(angle) / 2
            y = sin(angle) / 2
            return can_see((PLAYER.x, PLAYER.y), (self.x - x, self.y - y)) or \
                   can_see((PLAYER.x, PLAYER.y), (self.x + x, self.y + y))
        else:
            return False

    def ready_to_shoot(self):
        return self.dist_squared < self.shooting_range_squared and can_see((self.x, self.y), (PLAYER.x, PLAYER.y))

    def start_shooting(self):
        self.status = 'shooting'
        self.row = self.shooting_row
        self.column = 0
        self.anim_ticks = 0

    def handle_death(self):
        self.status = 'dead'
        self.hp = 0
        self.row = self.hit_row
        self.column = 0
        self.anim_ticks = 0
        self.chasing = False
        play_sound(self.sounds.death, self.channel_id, (self.x, self.y), self.dist_squared)

    def shoot(self):
        # speed_factor ranges between 24 (when player's running) and 32 (when not)
        speed_factor = 24 + 8 * (1 - PLAYER.total_movement / PLAYER.speed)

        dist_from_player = sqrt(self.dist_squared)

        player_hit = random.randint(0, int(32 / self.accuracy)) < speed_factor - dist_from_player
        if player_hit:
            if dist_from_player < 2:
                damage = random.randint(15, 20)
            elif dist_from_player > 4:
                damage = random.randint(5, 10)
            else:
                damage = random.randint(10, 15)
            PLAYER.hurt(int(damage * self.damage_multiplier), self)

    def hurt(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.handle_death()
        elif self.pain_chance > random.random():
            self.status = 'hit'
            self.row = self.hit_row
            self.column = 7
            self.anim_ticks = 0

    def loot(self):
        if PLAYER.ammo < Player.max_ammo:
            play_sound(ITEM_PICKUP_SOUND, 0)
            MESSAGES.append(Message('Ammo +{}'.format(self.looting_ammo)))
            self.looted = True
            PLAYER.add_ammo(self.looting_ammo)

    def strafe(self):
        # Sets step_(x/y) to a random new empty neighbour tile (if there is one)
        available_steps = []
        pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for pos_offset in pos_offsets:
            step_x = int(self.x) + pos_offset[0] + 0.5
            step_y = int(self.y) + pos_offset[1] + 0.5
            if self.map_empty(step_x, step_y):  # If tile steppable
                available_steps.append((step_x, step_y))

        if available_steps:
            self.step_x, self.step_y = random.choice(available_steps)

    def find_next_step_x_y(self):
        x_diff = self.target_tile[0] + 0.5 - self.x
        y_diff = self.target_tile[1] + 0.5 - self.y

        if abs(x_diff) > abs(y_diff):
            if x_diff > 0:
                step_x = self.x + 1
            else:
                step_x = self.x - 1
            if self.map_empty(step_x, self.y):
                self.step_x = step_x
            else:
                if y_diff > 0:
                    step_y = self.y + 1
                else:
                    step_y = self.y - 1
                if self.map_empty(self.x, step_y):
                    self.step_y = step_y
        else:
            if y_diff > 0:
                step_y = self.y + 1
            else:
                step_y = self.y - 1
            if self.map_empty(self.x, step_y):
                self.step_y = step_y
            else:
                if x_diff > 0:
                    step_x = self.x + 1
                else:
                    step_x = self.x - 1
                if self.map_empty(step_x, self.y):
                    self.step_x = step_x

    def at(self, tile_pos):
        return (self.x - 0.5, self.y - 0.5) == tile_pos

    def handle_doors_underneath(self):
        # If door underneath enemy, create a door obj if it isn't there already and start opening it immediately
        if (int(self.x), int(self.y)) in DOOR_TILES:
            for d in DOORS:
                if (d.x, d.y) == (int(self.x), int(self.y)):
                    d.start_opening()
                    break

    def handle_dead_status(self):
        if not self.looted:
            if (int(self.x), int(self.y)) == (int(PLAYER.x), int(PLAYER.y)):
                self.loot()
            self.outline_alpha += Enemy.looting_pulse_speed
            if self.outline_alpha >= 255:
                self.outline_alpha = -255
        if self.column != self.death_frames - 1:
            self.outline_alpha = 0
            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0
                self.column += 1

    def update(self):
        moved = False
        self.handle_doors_underneath()

        self.delta_x = self.x - PLAYER.x
        self.delta_y = self.y - PLAYER.y
        self.angle_from_player = atan2(self.delta_y, self.delta_x)
        self.dist_squared = self.delta_x**2 + self.delta_y**2

        if self.status == 'dead':
            self.handle_dead_status()

        elif self.status == 'hit':
            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks - 2:  # -2 plays hit animation a little faster
                self.anim_ticks = 0
                self.status = 'default'

        elif self.status == 'shooting':
            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0

                self.column += 1
                if self.column in self.shot_columns:
                    if self.shooting_range_squared > 2 or self.column == self.shot_columns[0]:
                        play_sound(self.sounds.attack, self.channel_id, (self.x, self.y), self.dist_squared)
                    if self.ready_to_shoot():
                        self.shoot()

                elif self.column == self.shooting_frames:
                    if (int(self.x), int(self.y)) == (int(PLAYER.x), int(PLAYER.y)):
                        self.column = 0  # Continues shooting
                    else:
                        self.column -= 1
                        self.status = 'default'

        else:
            if self.can_see_player_sides():
                self.chasing = True
                if not self.appeared:
                    self.appeared = True
                    if self.sounds.appearance:
                        play_sound(self.sounds.appearance, self.channel_id, (self.x, self.y), self.dist_squared)
                self.target_tile = (int(PLAYER.x), int(PLAYER.y))

            if self.at(self.target_tile):
                self.chasing = False
                self.viewangle = fixed_angle(self.angle_from_player + pi)
                if self.target_tile == (int(PLAYER.x), int(PLAYER.y)):
                    self.start_shooting()
                else:
                    alerted_enemy = self.get_nearby_alerted_enemy()
                    if alerted_enemy:
                        self.chasing = True
                        self.target_tile = (int(alerted_enemy.x), int(alerted_enemy.y))
                    elif self.stationary_ticks >= self.patience:
                        self.appeared = False
                        if self.at(self.home):
                            self.target_tile = random.choice(self.home_room)
                        else:
                            self.target_tile = self.home

            else:
                moved = True  # Technically doesn't mean that enemy moved in all cases but it gets the job done
                if self.x == self.step_x and self.y == self.step_y:  # If finished step
                    if self.chasing and random.randint(0, 1) and self.ready_to_shoot():
                        self.start_shooting()
                    else:
                        self.find_next_step_x_y()

                elif not self.can_step(self.step_x, self.step_y):
                    if self.chasing and random.randint(0, 1) and self.ready_to_shoot():
                        self.start_shooting()
                    else:
                        self.strafe()
                else:
                    self.viewangle = atan2(self.step_y - self.y, self.step_x - self.x)
                    self.x += cos(self.viewangle) * self.speed
                    self.y += sin(self.viewangle) * self.speed

                    if abs(self.x - self.step_x) < self.speed and abs(self.y - self.step_y) < self.speed:
                        self.x = self.step_x
                        self.y = self.step_y

            if not self.status == 'shooting':
                self.calc_row_and_column(moved)

        if moved:
            self.stationary_ticks = 0
        else:
            self.stationary_ticks += 1
            if self.stationary_ticks > self.patience:
                self.stationary_ticks = self.patience

        self.update_for_drawing(self.angle_from_player)

    def draw(self):
        if not self.hp and self.column == self.death_frames - 1:
            cropping_rect = (
                ((self.start_x - self.display_pos) / self.width + 0.5) * TEXTURE_SIZE,
                (TEXTURE_SIZE - self.cropping_height) / 2,
                (self.end_x - self.start_x) / self.width * TEXTURE_SIZE,
                self.cropping_height
            )
            if not self.looted:
                self.outline_image.set_alpha(abs(self.outline_alpha))
                image = self.dead_image.copy()
                image.blit(self.outline_image, (0, 0))
            else:
                image = self.dead_image
            cropped_image = image.subsurface(cropping_rect)

        else:
            cropping_rect = (
                ((self.start_x - self.display_pos) / self.width + self.column + 0.5) * TEXTURE_SIZE,
                (TEXTURE_SIZE - self.cropping_height) / 2 + self.row * TEXTURE_SIZE,
                (self.end_x - self.start_x) / self.width * TEXTURE_SIZE,
                self.cropping_height
            )
            cropped_image = self.sheet.subsurface(cropping_rect)
        try:
            DISPLAY.blit(
                pygame.transform.scale(cropped_image, (self.end_x - self.start_x, self.height)),
                (self.start_x, (D_H - self.height) / 2)
            )
        except pygame.error as error:
            print('Error occurred scaling enemy: {}'.format(error))
            print('width: {}'.format(self.end_x - self.start_x))
            print('height: {}'.format(self.height))


class Boss(Enemy):
    def __init__(self, spritesheet, pos):
        self.type = 'Boss'
        self.x, self.y = pos
        self.step_x = self.x
        self.step_y = self.y
        self.home = (int(self.x), int(self.y))

        self.sheet = spritesheet
        self.row = 0
        self.column = 0

        self.status = 'default'  # (default, shooting, dead)
        self.chasing = False
        self.seen_player = False

        # Take attributes from ENEMY_INFO based on spritesheet
        self.name = ENEMY_INFO[self.sheet].name
        self.channel_id = ENEMY_INFO[self.sheet].channel_id
        self.channel = pygame.mixer.Channel(self.channel_id)
        self.sounds = ENEMY_INFO[self.sheet].sounds
        self.max_hp = self.hp = ENEMY_INFO[self.sheet].hp
        self.speed = ENEMY_INFO[self.sheet].speed
        self.shooting_range_squared = ENEMY_INFO[self.sheet].shooting_range_squared
        self.damage_multiplier = ENEMY_INFO[self.sheet].damage_multiplier
        self.accuracy = ENEMY_INFO[self.sheet].accuracy
        self.pain_chance = ENEMY_INFO[self.sheet].pain_chance
        self.running_frames = ENEMY_INFO[self.sheet].running_frames
        self.death_frames = ENEMY_INFO[self.sheet].death_frames
        self.hit_row = ENEMY_INFO[self.sheet].hit_row
        self.shooting_frames = ENEMY_INFO[self.sheet].shooting_frames
        self.shot_columns = ENEMY_INFO[self.sheet].shot_columns
        self.shooting_row = ENEMY_INFO[self.sheet].shooting_row

        self.appearance_ticks = 30  # Time duration in ticks that boss will not shoot when appearing
        self.anim_ticks = 0

        self.dead_image = self.sheet.subsurface(
            ((self.death_frames - 1) * TEXTURE_SIZE, self.hit_row * TEXTURE_SIZE, TEXTURE_SIZE, TEXTURE_SIZE)
        )
        self.looted = False
        self.outline_alpha = 0
        self.outline_image = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
        self.outline_image.set_colorkey(Colour.black)
        for point in pygame.mask.from_surface(self.dead_image).outline():
            self.outline_image.set_at(point, Enemy.looting_colour)

    def map_empty(self, x, y):
        return TILEMAP[int(y)][int(x)] <= 0 or (int(x), int(y)) in DOOR_TILES

    def hurt(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.handle_death()
            MESSAGES.append(Message('{} defeated'.format(self.name)))

    def loot(self):
        self.looted = True
        PLAYER.has_key = True

        MESSAGES.append(Message('Picked up a key'))
        play_sound(ITEM_PICKUP_SOUND, 0)

    def update(self):
        self.handle_doors_underneath()

        self.delta_x = self.x - PLAYER.x
        self.delta_y = self.y - PLAYER.y
        self.angle_from_player = atan2(self.delta_y, self.delta_x)
        self.dist_squared = self.delta_x**2 + self.delta_y**2

        if self.status == 'dead':
            self.handle_dead_status()

        elif self.status == 'shooting':
            self.anim_ticks += 1
            if self.anim_ticks == Sprite.animation_ticks:
                self.anim_ticks = 0
                self.column += 1
                if self.column in self.shot_columns:
                    play_sound(self.sounds.attack, self.channel_id, (self.x, self.y), self.dist_squared)
                    if self.ready_to_shoot():
                        self.shoot()

                elif self.column == self.shooting_frames:
                    self.column = 0
                    self.status = 'default'

        elif self.status == 'default':
            if self.chasing:
                if self.x == self.step_x and self.y == self.step_y:  # If finished step
                    if random.randint(0, 1) and not self.appearance_ticks and self.ready_to_shoot():
                        self.start_shooting()
                    else:
                        self.target_tile = (int(PLAYER.x), int(PLAYER.y))
                        self.find_next_step_x_y()
                    if not self.seen_player and can_see((self.x, self.y), (PLAYER.x, PLAYER.y)):
                        self.seen_player = True
                        play_sound(self.sounds.appearance, self.channel_id)

                elif not self.can_step(self.step_x, self.step_y):
                    if random.randint(0, 1) and not self.appearance_ticks and self.ready_to_shoot():
                        self.start_shooting()
                    else:
                        self.strafe()
                else:
                    self.viewangle = atan2(self.step_y - self.y, self.step_x - self.x)
                    self.x += cos(self.viewangle) * self.speed
                    self.y += sin(self.viewangle) * self.speed

                    if abs(self.x - self.step_x) < self.speed and abs(self.y - self.step_y) < self.speed:
                        self.x = self.step_x
                        self.y = self.step_y

                if self.appearance_ticks and self.seen_player:
                    self.appearance_ticks -= 1
                elif not self.channel.get_busy():
                    play_sound(self.sounds.step, self.channel_id, (self.x, self.y), self.dist_squared)

                if not self.status == 'shooting':
                    self.row = 0

                self.anim_ticks += 1
                if self.anim_ticks == Sprite.animation_ticks:
                    self.anim_ticks = 0
                    self.column += 1
                    if self.column == self.running_frames:
                        self.column = 0

        self.update_for_drawing(self.angle_from_player)


class BossHealthBar:
    def __init__(self):
        width = D_W * 0.6
        height = 20
        self.half_width = int(width / 2)
        self.half_height = int(height / 2)

        self.visible = False
        self.speed = 5  # Pixels the bar moves up/down per tick
        self.outline = 4  # Black outline width
        self.center_x = H_W
        self.center_y = 35
        self.current_y = -int(TEXTURE_SIZE / 2)  # The current healthbar y pos

    def start_showing(self, boss):
        self.visible = True
        self.boss = boss
        self.boss_image = self.boss.sheet.subsurface(0, 0, TEXTURE_SIZE, TEXTURE_SIZE)

    def draw(self):
        if self.visible:
            if self.boss.hp == 0:
                self.current_y -= self.speed
                if self.current_y <= -TEXTURE_SIZE:
                    self.visible = False
            elif self.current_y < self.center_y:
                self.current_y += self.speed
                if self.current_y > self.center_y:
                    self.current_y = self.center_y

            colour = dynamic_colour(self.boss.hp, self.boss.max_hp)
            health_amount = self.boss.hp / self.boss.max_hp

            # Outline
            pygame.draw.rect(DISPLAY, (0, 0, 0), (self.center_x - self.half_width - self.outline,
                                                  self.current_y - self.half_height - self.outline,
                                                  (self.half_width + self.outline) * 2,
                                                  (self.half_height + self.outline) * 2))
            # Health bar
            pygame.draw.rect(DISPLAY, colour, (self.center_x - self.half_width, self.current_y - self.half_height,
                                               self.half_width * 2 * health_amount, self.half_height * 2))
            # Boss name
            boss_name = render_text(str(self.boss.name), (0, 0, 0), size=16)
            DISPLAY.blit(boss_name, (self.center_x - self.half_width + TEXTURE_SIZE / 2,
                                     self.current_y - 8))
            # Boss image
            DISPLAY.blit(self.boss_image, (self.center_x - self.half_width - TEXTURE_SIZE / 2,
                                           self.current_y - TEXTURE_SIZE / 2))


class Level:
    def load(self, level_nr):
        self.nr = level_nr

        # Load level file
        with open('../levels/{}/tilemap.txt'.format(level_nr), 'r') as f:
            # Tilemap
            global TILEMAP
            TILEMAP = []
            lines = list(f)
            for line in lines[:-2]:
                row = line[1:-2]  # Get rid of '[' and ']'
                row = row.split(',')  # Split line into list
                row = [int(i) for i in row]  # Turn all number strings to an int
                TILEMAP.append(row)
            # Sky texture
            skytexture_value = int(lines[-2])
            skytexture_name = os.listdir('../textures/skies')[skytexture_value]
            try:
                raw_skytexture = pygame.image.load('../textures/skies/{}'.format(skytexture_name)).convert()
            except pygame.error as loading_error:
                sys.exit(loading_error)
            else:
                self.skytexture = pygame.Surface((D_W * 2, H_H))
                self.skytexture.blit(pygame.transform.scale(raw_skytexture, (D_W, H_H)), (0, 0))
                self.skytexture.blit(pygame.transform.scale(raw_skytexture, (D_W, H_H)), (D_W, 0))
            # Floor texture
            floor_texture_value = int(lines[-1])
            cropping_rect = (0, floor_texture_value * TEXTURE_SIZE, TEXTURE_SIZE, TEXTURE_SIZE)
            try:
                raw_floor_texture = pygame.image.load('../textures/walls/floor.png').convert().subsurface(cropping_rect)
            except pygame.error as loading_error:
                sys.exit(loading_error)
            else:
                self.floor_texture, self.big_floor_texture = graphics.get_floor_textures(raw_floor_texture)

        # Load player file
        with open('../levels/{}/player.txt'.format(level_nr), 'r') as f:
            player_pos = f.readline().replace('\n', '').split(',')
            player_pos = [float(i) for i in player_pos]
            player_angle = float(f.readline().replace('\n', ''))
            global PLAYER
            PLAYER.setup(player_pos, player_angle)

        # Load gameobjects
        global OBJECTS
        OBJECTS = []
        global EXPLOSIVES
        EXPLOSIVES = []
        global ENEMIES
        ENEMIES = []
        global DOORS
        DOORS = []
        global PUSH_WALLS
        PUSH_WALLS = []
        global THIN_WALLS
        THIN_WALLS = []
        for row in range(len(TILEMAP)):
            for column in range(len(TILEMAP[row])):
                tile_value = TILEMAP[row][column]
                tile = TILE_VALUES_INFO[tile_value]
                pos = (column + 0.5, row + 0.5)
                map_pos = (column, row)
                if tile.type == 'Object':
                    if tile.desc == 'Explosive':
                        EXPLOSIVES.append(ExplodingBarrel(tile.texture, pos))
                    else:
                        OBJECTS.append(Object(tile.texture, pos))
                        if tile.desc == 'Non-solid':
                            TILEMAP[row][column] = 0  # Clears tile
                elif tile.type == 'Enemy':
                    if tile.desc == 'Normal':
                        ENEMIES.append(Enemy(tile.texture, pos))
                    elif tile.desc == 'Boss':
                        ENEMIES.append(Boss(tile.texture, pos))
                    TILEMAP[row][column] = 0  # Clears tile

                elif tile.type == 'Door':
                    if tile.desc == 'Boss':
                        DOORS.append(BossDoor(map_pos, tile_value))
                    else:
                        DOORS.append(Door(map_pos, tile_value))
                elif tile.type == 'Wall':
                    if tile.desc == 'Secret':
                        PUSH_WALLS.append(PushWall(map_pos, tile_value))
                elif tile.type == 'Thin Wall':
                    THIN_WALLS.append(ThinWall(map_pos))

        # Tile sets
        global EMPTY_TILES  # Contains tiles that raycasting will ignore
        EMPTY_TILES = set()
        global DOOR_TILES
        DOOR_TILES = set()
        global PUSH_WALL_TILES
        PUSH_WALL_TILES = set()
        global THIN_WALL_TILES
        THIN_WALL_TILES = set()

        for row in range(len(TILEMAP)):
            for column in range(len(TILEMAP[row])):
                tile = TILE_VALUES_INFO[TILEMAP[row][column]]

                if tile.type == 'Door':
                    DOOR_TILES.add((column, row))
                elif tile.type == 'Wall':
                    if tile.desc == 'Secret':
                        PUSH_WALL_TILES.add((column, row))
                elif tile.type == 'Thin Wall':
                    THIN_WALL_TILES.add((column, row))
                else:
                    EMPTY_TILES.add((column, row))

        global FLOOR_TILES  # Tiles that need floor rendering, contains everything but normal wall tiles
        FLOOR_TILES = EMPTY_TILES | DOOR_TILES | PUSH_WALL_TILES | THIN_WALL_TILES

        # Get enemy home rooms after enemies have been cleared from the tilemap
        for e in ENEMIES:
            if e.type == 'Normal':
                e.get_home_room()

    def start(self, level_nr):
        self.load(level_nr)

        global BLUE_PORTAL
        BLUE_PORTAL = Portal(True)
        global RED_PORTAL
        RED_PORTAL = Portal(False)
        global TIME
        TIME = 0
        global MESSAGES
        MESSAGES = []
        global EFFECTS
        EFFECTS = Effects()
        global WEAPON_MODEL
        WEAPON_MODEL = WeaponModel()
        global BOSSHEALTHBAR
        BOSSHEALTHBAR = BossHealthBar()

        game_loop()

    def restart(self, enemy=None):
        def get_turn_radians():
            turn_speed = 0.05
            difference = fixed_angle(enemy.angle_from_player - PLAYER.viewangle)
            if difference > 0:
                return turn_speed
            else:
                return -turn_speed

        global QUIT
        text_alpha = 0
        overlay_alpha = 0

        # If enemy, turn towards it
        while enemy:
            enemy.angle_from_player = atan2(enemy.delta_y, enemy.delta_x)
            turn_radians = get_turn_radians()
            PLAYER.rotate(turn_radians)
            PLAYER.dir_x = cos(PLAYER.viewangle)
            PLAYER.dir_y = sin(PLAYER.viewangle)

            for sprite in ENEMIES + OBJECTS + EXPLOSIVES:
                sprite.update_for_drawing()

            if overlay_alpha != 128:
                overlay_alpha += 8

            send_rays()
            handle_objects_under_player()
            draw_frame(False)
            draw_black_overlay(overlay_alpha)

            pygame.display.flip()
            CLOCK.tick(30)

            if abs(PLAYER.viewangle - enemy.angle_from_player) <= abs(turn_radians):
                break

        # Wait for a button press
        continued = False
        while not continued:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        QUIT = True
                        continued = True
                    elif event.key == K_SPACE:
                        continued = True

            if overlay_alpha != 128:
                overlay_alpha += 8
            text_alpha -= 15
            if text_alpha <= -255:
                text_alpha = 255

            for sprite in ENEMIES + OBJECTS:
                sprite.update_for_drawing()
            send_rays()
            handle_objects_under_player()
            draw_frame(False)
            draw_black_overlay(overlay_alpha)

            you_died = render_text('YOU DIED', Colour.white, abs(text_alpha))
            display_text(1, 1, you_died)
            pygame.display.flip()
            CLOCK.tick(30)

        # Start new level
        pygame.mouse.get_rel()
        pygame.event.clear()
        self.start(self.nr)

    def finish(self):
        PLAYER.save_weapon_loadout()

        seconds = int(TIME / 30)  # Rounds time spent down, 45.8 seconds will display 45
        minutes = 0
        while seconds >= 60:
            minutes += 1
            seconds -= 60
        dead = 0
        for e in ENEMIES:
            if not e.hp:
                dead += 1

        global QUIT
        overlay_alpha = 0
        text_alpha = 0

        continued = False
        while not continued:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        QUIT = True
                        continued = True
                    elif event.key == K_SPACE:
                        continued = True

            text_alpha -= 15
            if text_alpha <= -255:
                text_alpha = 255
            if overlay_alpha != 128:
                overlay_alpha += 8

            send_rays()
            handle_objects_under_player()
            draw_frame(False)
            draw_black_overlay(overlay_alpha)

            level_finished = render_text('LEVEL FINISHED', Colour.white)
            time_spent = render_text('TIME: {}m {}s'.format(minutes, seconds), Colour.white)
            kills = render_text('KILLS: {}/{}'.format(dead, len(ENEMIES)), Colour.white)
            press_space_to_continue = render_text('Press SPACE to continue', Colour.white, abs(text_alpha))
            display_text(1, 1, level_finished, time_spent, kills, press_space_to_continue)

            pygame.display.flip()
            CLOCK.tick(30)

        self.start(self.nr + 1)


def squared_dist(from_, to):
    return (from_[0] - to[0])**2 + (from_[1] - to[1])**2


def fixed_angle(angle):
    while angle > pi:
        angle -= 2 * pi
    while angle <= -pi:
        angle += 2 * pi
    return angle


def can_see(from_, to):
    # Universal function for checking if it's possible to see from one point to another in tilemap

    start_x, start_y = from_
    end_x, end_y = to
    angle_to_end = atan2(end_y - start_y, end_x - start_x)

    # Raycast a ray to end postition
    collision_x, collision_y = raycast(from_, angle_to_end)
    # If collision further than end point, it's possible to see
    return squared_dist(from_, (collision_x, collision_y)) > squared_dist(from_, to)


def dynamic_colour(current, maximum):
    ratio = current / maximum  # 1 is completely green, 0 completely red
    if ratio < 0.5:
        r = 255
        g = int(ratio * 2 * 255)
    else:
        ratio = 1 - ratio
        g = 255
        r = int(ratio * 2 * 255)
    return r, g, 0


def render_text(text, colour, alpha=255, size=32):
    if size == 32:
        image = GAME_FONT_32.render(text, False, colour)
    elif size == 24:
        image = GAME_FONT_24.render(text, False, colour)
    elif size == 16:
        image = GAME_FONT_16.render(text, False, colour)
    else:
        return
    if alpha != 255:
        image.set_alpha(alpha)
    return image


def join_texts(rendered_texts):
    # Add all given texts into one image
    # Allows for different colour or alpha valued texts to be drawn together on one line
    # Estimates that the space key width will be approximately half of text's height
    text_h = rendered_texts[0].get_height()
    text_gap_w = int(text_h / 2)
    total_w = (len(rendered_texts) - 1) * text_gap_w
    for rendered_text in rendered_texts:
        total_w += rendered_text.get_width()
    new_surface = pygame.Surface((total_w, text_h), SRCALPHA)
    x = 0
    for rendered_text in rendered_texts:
        new_surface.blit(rendered_text, (x, 0))
        x += rendered_text.get_width() + text_gap_w
    return new_surface


def display_text(horizontal_pos, vertical_pos, *rendered_texts):
    #    horizontal pos
    #  0--------1--------2
    # |                   0
    # |      DISPLAY      | vertical
    # |         +         1   pos
    # |                   |
    # |                   2
    #  -------------------
    # If given multiple texts, they will be drawn on top of each other
    x = horizontal_pos * H_W
    if x == 0:
        x += HUD_SAFEZONE
    elif x == D_W:
        x -= HUD_SAFEZONE
    y = vertical_pos * H_H
    if y == 0:
        y += HUD_SAFEZONE
    elif y == D_H:
        y -= HUD_SAFEZONE
    text_h = rendered_texts[0].get_height()
    y -= len(rendered_texts) * int(text_h / 2) * vertical_pos
    for rendered_text in rendered_texts:
        text_w = rendered_text.get_width()
        DISPLAY.blit(rendered_text, (x - int(text_w / 2) * horizontal_pos, y))
        y += text_h


def send_rays():
    # MAX_DRAW_DIST_SQUARED is used in drawing enemies and objects
    global MAX_DRAW_DIST_SQUARED
    MAX_DRAW_DIST_SQUARED = 0

    # Deletes previous walls
    global WALLS
    WALLS = []
    global SEETHROUGH_WALLS
    SEETHROUGH_WALLS = []
    global DISPLAY_X

    # Send rays
    for DISPLAY_X, rayangle_offset in enumerate(CAMERA_PLANE.rayangle_offsets):
        ray_start = (PLAYER.x, PLAYER.y)
        if not DISPLAY_X % WALL_RES:
            # Get values from raycast()
            delta_x, delta_y, texture, column = \
                raycast(ray_start, PLAYER.viewangle + rayangle_offset, extra_values=True, can_go_through_portal=True)

            # Calculate perpendicular distance (needed to avoid fisheye effect)
            perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y

            new_dist = delta_x**2 + delta_y**2
            if new_dist > MAX_DRAW_DIST_SQUARED:
                MAX_DRAW_DIST_SQUARED = new_dist

            # Create Wall object
            WALLS.append(WallColumn(texture, column, perp_dist, DISPLAY_X))
        else:
            WALLS.append(None)


def raycast(start_pos, rayangle, extra_values=False,
            can_go_through_portal=False, previous_rayangle_diff=0.0, previous_delta_x=0.0, previous_delta_y=0.0):
    def check_collision(collision_x, collision_y, x_step, y_step):
        # x_step is the distance needed to move in x to get to the next similar type interception
        # y_step is the distance needed to move in y to get to the next similar type interception

        def get_delta_x_and_y():
            current_delta_x = collision_x - start_pos[0]
            current_delta_y = collision_y - start_pos[1]
            if previous_rayangle_diff:
                if previous_rayangle_diff == pi:
                    delta_x = previous_delta_x - current_delta_x
                    delta_y = previous_delta_y - current_delta_y
                elif previous_rayangle_diff > 0:
                    delta_x = previous_delta_x + current_delta_y
                    delta_y = previous_delta_y - current_delta_x
                else:
                    delta_x = previous_delta_x - current_delta_y
                    delta_y = previous_delta_y + current_delta_x
            else:
                delta_x = previous_delta_x + current_delta_x
                delta_y = previous_delta_y + current_delta_y
            return delta_x, delta_y

        if (map_x, map_y) in DOOR_TILES:
            # Get the door that ray hits
            for d in DOORS:
                if (d.x, d.y) == (map_x, map_y):
                    door = d
                    break

            collision_x += x_step / 2
            collision_y += y_step / 2
            if (int(collision_x), int(collision_y)) == (map_x, map_y):
                if abs(x_step) == 1:
                    surface_offset = collision_y - int(collision_y)
                    column = TEXTURE_SIZE
                else:
                    surface_offset = collision_x - int(collision_x)
                    column = 0
                if surface_offset < door.closed_state:
                    if extra_values:
                        texture = TILE_VALUES_INFO[TILEMAP[map_y][map_x]].texture
                        column += int(TEXTURE_SIZE * abs(surface_offset - door.closed_state))
                        delta_x, delta_y = get_delta_x_and_y()
                        return delta_x, delta_y, texture, column
                    else:
                        return collision_x, collision_y

        elif (map_x, map_y) in THIN_WALL_TILES:
            if extra_values:
                for thin_wall in THIN_WALLS:
                    if (thin_wall.x, thin_wall.y) == (map_x, map_y):

                        if abs(x_step) == 1:
                            if thin_wall.vertical:
                                collision_x += x_step / 2
                                collision_y += y_step / 2
                            else:
                                y_offset = collision_y - int(collision_y)
                                y_dist_from_wall = abs(b - y_offset) - 0.5
                                if y_dist_from_wall > 0:
                                    step_dist = abs(y_dist_from_wall / y_step)
                                    collision_x += x_step * step_dist
                                    collision_y = int(collision_y) + 0.5
                                else:
                                    return
                            column = TEXTURE_SIZE

                        else:
                            if thin_wall.vertical:
                                x_offset = collision_x - int(collision_x)
                                x_dist_from_wall = abs(a - x_offset) - 0.5
                                if x_dist_from_wall > 0:
                                    step_dist = abs(x_dist_from_wall / x_step)
                                    collision_y += y_step * step_dist
                                    collision_x = int(collision_x) + 0.5
                                else:
                                    return
                            else:
                                collision_x += x_step / 2
                                collision_y += y_step / 2
                            column = 0

                        if (int(collision_x), int(collision_y)) == (map_x, map_y):
                            if thin_wall.vertical:
                                surface_offset = collision_y - int(collision_y)
                            else:
                                surface_offset = collision_x - int(collision_x)
                            texture = TILE_VALUES_INFO[TILEMAP[map_y][map_x]].texture
                            column += int(TEXTURE_SIZE * surface_offset)
                            delta_x, delta_y = get_delta_x_and_y()

                            perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y
                            SEETHROUGH_WALLS.append(WallColumn(texture, column, perp_dist, DISPLAY_X))
                        break

        else:
            if (map_x, map_y) in PUSH_WALL_TILES:
                for push_wall in PUSH_WALLS:
                    if (push_wall.x, push_wall.y) == (map_x, map_y):
                        if push_wall.tile_offset > 0:
                            collision_x += x_step * push_wall.tile_offset
                            collision_y += y_step * push_wall.tile_offset
                            if (int(collision_x), int(collision_y)) != (map_x, map_y):
                                return  # Ray misses the pushwall
                        break

            if extra_values:
                if abs(x_step) == 1:
                    surface_offset = abs((1 - a) - (collision_y - int(collision_y)))
                    column = int(TEXTURE_SIZE * surface_offset)
                    column += TEXTURE_SIZE
                else:
                    surface_offset = abs(b - (collision_x - int(collision_x)))
                    column = int(TEXTURE_SIZE * surface_offset)
                delta_x, delta_y = get_delta_x_and_y()

                portal = False
                if BLUE_PORTAL.created and (map_x, map_y) == (BLUE_PORTAL.map_x, BLUE_PORTAL.map_y):
                    portal = BLUE_PORTAL
                    other_portal = RED_PORTAL
                elif RED_PORTAL.created and (map_x, map_y) == (RED_PORTAL.map_x, RED_PORTAL.map_y):
                    portal = RED_PORTAL
                    other_portal = BLUE_PORTAL
                if portal:
                    # Ray hits block portal is attached to
                    if (abs(x_step) == 1 and portal.vertical and portal.side == (1 - a)) or \
                            (abs(x_step) != 1 and not portal.vertical and portal.side == (1 - b)):
                        # Ray hits portal

                        # Draw a seethrough wall - portal edges
                        texture = portal.texture
                        perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y
                        SEETHROUGH_WALLS.append(WallColumn(texture, column, perp_dist, DISPLAY_X))

                        if can_go_through_portal and other_portal.created:
                            if portal.vertical:
                                if other_portal.vertical:
                                    if portal.side == other_portal.side:
                                        rayangle_diff = pi
                                    else:
                                        rayangle_diff = 0
                                else:
                                    if portal.side == 0:
                                        rayangle_diff = -(0.5 - other_portal.side) * pi
                                    else:
                                        rayangle_diff = (0.5 - other_portal.side) * pi
                            else:
                                if not other_portal.vertical:
                                    if portal.side == other_portal.side:
                                        rayangle_diff = pi
                                    else:
                                        rayangle_diff = 0
                                else:
                                    if portal.side == 0:
                                        rayangle_diff = (0.5 - other_portal.side) * pi
                                    else:
                                        rayangle_diff = -(0.5 - other_portal.side) * pi

                            if other_portal.vertical:
                                start_x = other_portal.map_x + other_portal.side
                                if other_portal.side == 1:
                                    start_y = other_portal.map_y + surface_offset
                                else:
                                    start_y = other_portal.map_y + (1 - surface_offset)
                            else:
                                start_y = other_portal.map_y + other_portal.side
                                if other_portal.side == 1:
                                    start_x = other_portal.map_x + (1 - surface_offset)
                                else:
                                    start_x = other_portal.map_x + surface_offset

                            return raycast((start_x, start_y), rayangle + rayangle_diff, extra_values=True,
                                           can_go_through_portal=False, previous_rayangle_diff=rayangle_diff,
                                           previous_delta_x=delta_x, previous_delta_y=delta_y)

                if (x - a, y - b) in DOOR_TILES:
                    texture = Door.side_texture
                else:
                    texture = TILE_VALUES_INFO[TILEMAP[map_y][map_x]].texture

                return delta_x, delta_y, texture, column
            else:
                return collision_x, collision_y

    def interception_horizontal():
        if a:
            return x_intercept < x
        else:
            return x_intercept > x

    def interception_vertical():
        if b:
            return y_intercept < y
        else:
            return y_intercept > y

    # https://www.youtube.com/watch?v=eOCQfxRQ2pY

    #      a = 0 | a = 1
    # -pi  b = 0 | b = 0  -
    #     -------|------- 0 radians
    #  pi  a = 0 | a = 1  +
    #      b = 1 | b = 1
    rayangle = fixed_angle(rayangle + 0.0000001)
    tan_rayangle = tan(rayangle)

    if abs(rayangle) < pi / 2:
        a = 1
        start_x = start_pos[0] + 0.0000001
        tile_step_x = 1
        y_step = tan_rayangle
    else:
        a = 0
        start_x = start_pos[0] - 0.0000001
        tile_step_x = -1
        y_step = -tan_rayangle
    if rayangle > 0:
        b = 1
        start_y = start_pos[1] + 0.0000001
        tile_step_y = 1
        x_step = 1 / tan_rayangle
    else:
        b = 0
        start_y = start_pos[1] - 0.0000001
        tile_step_y = -1
        x_step = 1 / -tan_rayangle

    x = int(start_x)
    y = int(start_y)
    dx = start_x - x
    dy = start_y - y
    x_intercept = x + dx + (b - dy) / tan_rayangle
    y_intercept = y + dy + (a - dx) * tan_rayangle
    x += a
    y += b

    while True:
        while interception_horizontal():
            map_x = int(x_intercept)
            map_y = y - (1 - b)
            if (map_x, map_y) not in EMPTY_TILES:
                collision = check_collision(x_intercept, y, x_step, tile_step_y)
                if collision:
                    return collision
            y += tile_step_y
            x_intercept += x_step
        while interception_vertical():
            map_x = x - (1 - a)
            map_y = int(y_intercept)
            if (map_x, map_y) not in EMPTY_TILES:
                collision = check_collision(x, y_intercept, tile_step_x, y_step)
                if collision:
                    return collision
            x += tile_step_x
            y_intercept += y_step


def events():
    global PAUSED
    global SHOW_FPS
    global QUIT

    if PAUSED:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    PAUSED = False
                    update_sound_channels()
                elif event.key == K_F1:
                    SHOW_FPS = not SHOW_FPS
                elif event.key == K_RETURN:
                    QUIT = True
        pygame.mouse.get_rel()

    else:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    PAUSED = True
                    update_sound_channels()
                elif event.key == K_F1:
                    SHOW_FPS = not SHOW_FPS

                if event.key == K_e:
                    action_x = int(PLAYER.x + PLAYER.dir_x)
                    action_y = int(PLAYER.y + PLAYER.dir_y)
                    tile = TILE_VALUES_INFO[TILEMAP[action_y][action_x]]
                    if (action_x, action_y) in DOOR_TILES:
                        if tile.type == 'Locked' and not PLAYER.has_key:
                            MESSAGES.append(Message('Opening this door requires a key'))
                        else:
                            for d in DOORS:
                                if (d.x, d.y) == (action_x, action_y):
                                    if not d.locked:
                                        d.start_opening()
                                    else:
                                        MESSAGES.append(Message('This door is locked'))
                                    break
                    if (action_x, action_y) in PUSH_WALL_TILES:
                        for push_wall in PUSH_WALLS:
                            if (push_wall.x, push_wall.y) == (action_x, action_y):
                                if not push_wall.activated:
                                    push_wall.start_moving()
                                break

                    elif tile.desc == 'End-trigger':
                        play_sound(SWITCH_SOUND, 0, (action_x + 0.5, action_y + 0.5))
                        TILEMAP[action_y][action_x] += 1  # Change trigger block texture
                        LEVEL.finish()

                else:
                    key = pygame.key.name(event.key)
                    numbers = (str(x) for x in range(1, 10))
                    if key in numbers:
                        number = int(key)
                        if number in PLAYER.weapon_loadout and number != PLAYER.weapon_nr:
                            WEAPON_MODEL.switching = number

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    BLUE_PORTAL.create_portal()
                    #if not WEAPON_MODEL.switching:
                    #    if PLAYER.ammo >= WEAPON_MODEL.weapon.ammo_consumption:
                    #        WEAPON_MODEL.shooting = True
                    #    elif not pygame.mixer.Channel(WeaponModel.channel_id).get_busy():
                    #        play_sound(WEAPON_MODEL.weapon.sounds.no_ammo, WeaponModel.channel_id)
                elif event.button == 3:
                    RED_PORTAL.create_portal()


def update_gameobjects():
    for d in DOORS:
        d.move()
    for p in PUSH_WALLS:
        p.move()
    for o in OBJECTS:
        o.update()
    for e in EXPLOSIVES:
        e.update()
    for e in ENEMIES:
        e.update()
    for m in MESSAGES:
        m.update()
    WEAPON_MODEL.update()


def handle_objects_under_player():
    # Checking if player is standing on an object which can be picked up

    tile_value = TILEMAP[int(PLAYER.y)][int(PLAYER.x)]
    if tile_value < 0:
        pickup_type = 0

        # First handle all now-weapon pickups
        if tile_value == -len(WEAPONS) + 1:
            PLAYER.has_key = True
            MESSAGES.append(Message('Picked up a key'))
            pickup_type = 1
        elif tile_value == -len(WEAPONS):
            if PLAYER.hp < PLAYER.max_hp:
                PLAYER.add_hp(10)
                MESSAGES.append(Message('Health +10'))
                pickup_type = 2
        elif tile_value == -len(WEAPONS) - 1:
            if PLAYER.hp < PLAYER.max_hp:
                PLAYER.add_hp(25)
                MESSAGES.append(Message('Health +25'))
                pickup_type = 2

        # Then handle weapon pickups
        elif not WEAPON_MODEL.shooting and not WEAPON_MODEL.switching:
            if abs(tile_value) < len(WEAPONS) - 1:
                pickup_type = 3

        if pickup_type:
            if pickup_type == 1:  # Key
                colour = Colour.yellow
                play_sound(ITEM_PICKUP_SOUND, 0)
            elif pickup_type == 2:  # Health
                colour = Colour.green
                play_sound(ITEM_PICKUP_SOUND, 0)
            else:  # Weapon
                colour = Colour.blue
                play_sound(WEAPON_PICKUP_SOUND, 0)
                weapon_nr = abs(tile_value)
                if weapon_nr not in PLAYER.weapon_loadout:
                    PLAYER.weapon_loadout.append(weapon_nr)
                    WEAPON_MODEL.switching = weapon_nr
                PLAYER.add_ammo(10)
                MESSAGES.append(Message('Ammo +10'))
                MESSAGES.append(Message('Picked up {}'.format(WEAPONS[weapon_nr].name)))

            EFFECTS.update(colour)
            # Delete object
            TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0
            for c, o in enumerate(OBJECTS):
                if (int(o.x), int(o.y)) == (int(PLAYER.x), int(PLAYER.y)):
                    del OBJECTS[c]
                    break


def draw_hud():
    font_size = 24

    # Messages
    for m in reversed(MESSAGES):
        m.draw()

    # FPS counter
    if SHOW_FPS:
        fps_counter = render_text(str(ceil(CLOCK.get_fps())), Colour.green, size=font_size)
        display_text(2, 0, fps_counter)

    # Weapon HUD
    WEAPON_MODEL.draw()

    # Player hp and ammo HUD
    hp_text = render_text('Hp:', Colour.black, size=font_size)
    hp_amount = render_text(str(PLAYER.hp), dynamic_colour(PLAYER.hp, Player.max_hp), size=font_size)
    ammo_text = render_text('Ammo:', Colour.black, size=font_size)
    ammo_amount = render_text(str(PLAYER.ammo), dynamic_colour(PLAYER.ammo, Player.max_ammo), size=font_size)
    display_text(0, 2, hp_text, hp_amount, ammo_text, ammo_amount)

    # Weapon name and loadout HUD
    current_weapon = WEAPON_MODEL.weapon
    weapon_name = render_text(str(current_weapon.name), Colour.black, size=font_size)

    weapon_nrs = []
    for weapon_nr, w in enumerate(WEAPONS[1:], 1):
        if w == WEAPON_MODEL.weapon:  # If equipped
            colour = Colour.green
        elif weapon_nr in PLAYER.weapon_loadout:  # If picked up
            colour = Colour.dark_green
        else:  # If not picked up
            colour = Colour.black
        weapon_nrs.append(render_text(str(weapon_nr), colour, size=font_size))
    weapon_loadout = join_texts(weapon_nrs)

    display_text(2, 2, weapon_name, weapon_loadout)

    BOSSHEALTHBAR.draw()
    EFFECTS.draw()


def draw_background():
    # Sky texture
    angle = PLAYER.viewangle + pi
    while angle > pi / 2:
        angle -= pi / 2
    texture_offset = angle / (pi / 2)  # ranges from 0 to 1
    DISPLAY.blit(LEVEL.skytexture, (0, 0), (D_W * texture_offset, 0, D_W, H_H))

    if FLOOR_RES:
        # Textured floor is drawn poorly to keep the framerate as high as possible (still drops by a lot)
        pygame.draw.rect(DISPLAY, Colour.dark_grey, (0, H_H, D_W, H_H))
        start_angle = PLAYER.viewangle - FOV / 2
        sin_start_angle = sin(start_angle)
        cos_start_angle = cos(start_angle)
        step_angle = PLAYER.viewangle + pi / 2
        sin_step_angle = sin(step_angle)
        cos_step_angle = cos(step_angle)

        for (y, dist, step_dist) in CAMERA_PLANE.floor_lookup_table[8:40:2]:
            floor_x = PLAYER.x + dist * cos_start_angle
            floor_y = PLAYER.y + dist * sin_start_angle
            step_x = step_dist * cos_step_angle
            step_y = step_dist * sin_step_angle
            for x in range(0, D_W, FLOOR_RES):
                if (int(floor_x), int(floor_y)) in FLOOR_TILES:
                    texture_x = int((floor_x - int(floor_x)) * TEXTURE_SIZE)
                    texture_y = int((floor_y - int(floor_y)) * TEXTURE_SIZE)
                    DISPLAY.blit(LEVEL.floor_texture, (x, y), (texture_x, texture_y, FLOOR_RES, 2))
                floor_x += step_x
                floor_y += step_y

        for (y, dist, step_dist) in CAMERA_PLANE.floor_lookup_table[40::2]:
            floor_x = PLAYER.x + dist * cos_start_angle
            floor_y = PLAYER.y + dist * sin_start_angle
            step_x = step_dist * cos_step_angle * 2
            step_y = step_dist * sin_step_angle * 2
            for x in range(0, D_W, FLOOR_RES * 2):
                if (int(floor_x), int(floor_y)) in FLOOR_TILES:
                    texture_x = int((floor_x - int(floor_x)) * TEXTURE_SIZE * 2)
                    texture_y = int((floor_y - int(floor_y)) * TEXTURE_SIZE * 2)
                    DISPLAY.blit(LEVEL.big_floor_texture, (x, y), (texture_x, texture_y, FLOOR_RES * 2, 2))
                floor_x += step_x
                floor_y += step_y
    else:
        pygame.draw.rect(DISPLAY, Colour.grey, (0, H_H, D_W, H_H))


def draw_frame(hud=True):
    # Draw background
    draw_background()

    # Draw walls
    for w in WALLS:
        if w:
            w.draw()

    # Get things to draw
    to_draw = SEETHROUGH_WALLS
    for sprite in ENEMIES + OBJECTS + EXPLOSIVES:
        if sprite.visible_to_player:
            to_draw.append(sprite)

    # Sort things by perp_dist
    to_draw.sort(key=lambda x: x.perp_dist, reverse=True)

    # Draw things
    for sprite in to_draw:
        sprite.draw()

    if hud:
        draw_hud()


def update_sound_channels():
    for channel_id in range(8):
        if PAUSED:
            pygame.mixer.Channel(channel_id).pause()
        else:
            pygame.mixer.Channel(channel_id).unpause()


def play_sound(sound, channel_id, source_pos=(0.0, 0.0), source_dist_squared=0.0):
    def set_channel_stereo_volume(angle):
        if abs(angle) < pi / 2:
            volume = 1 - abs(angle) / (pi / 2)
        else:
            volume = 1 - (pi - abs(angle)) / (pi / 2)

        if angle < 0:  # Sound comes from right
            channel.set_volume(volume, 1)
        else:  # Sound comes from left
            channel.set_volume(1, volume)

    channel = pygame.mixer.Channel(channel_id)

    if source_pos[0] and source_pos[1]:
        if not source_dist_squared:
            source_dist_squared = squared_dist((PLAYER.x, PLAYER.y), source_pos)

        max_hearing_dist_squared = 400
        sound_volume = 1 - source_dist_squared / max_hearing_dist_squared
        if sound_volume > 0:
            sound.set_volume(sound_volume)

            angle_to_source = atan2(source_pos[1] - PLAYER.y, source_pos[0] - PLAYER.x)
            source_angle = fixed_angle(PLAYER.viewangle - angle_to_source)
            set_channel_stereo_volume(source_angle)

            channel.play(sound)
    else:
        channel.play(sound)


def draw_pause_overlay():
    draw_black_overlay(128)
    paused = render_text('PAUSED', Colour.white)
    display_text(1, 1, paused)


def draw_black_overlay(alpha):
    black_overlay = pygame.Surface((D_W, D_H))
    black_overlay.set_alpha(alpha)
    black_overlay.fill(Colour.black)
    DISPLAY.blit(black_overlay, (0, 0))


def game_loop():
    global TIME
    while not QUIT:
        if not PAUSED:
            TIME += 1
            PLAYER.rotate(pygame.mouse.get_rel()[0] * SENSITIVITY)
            PLAYER.handle_movement()

        events()
        send_rays()
        if not PAUSED:
            update_gameobjects()
        handle_objects_under_player()
        draw_frame()
        if PAUSED:
            draw_pause_overlay()

        pygame.display.flip()
        CLOCK.tick(30)


if __name__ == '__main__':
    import sys
    import os
    import random
    from math import sin, cos, tan, atan2, sqrt, pi, ceil

    import pygame
    from pygame.locals import *

    from game.settings import *
    import game.graphics as graphics
    import game.sounds as sounds
    import game.enemies as enemies
    import game.weapons as weapons

    H_W = int(D_W / 2)  # Display half width
    H_H = int(D_H / 2)  # Display half height

    # Set drawable constant
    Drawable.constant = int(0.65 * D_H)

    # Pygame stuff
    pygame.mixer.init(11025, -16, 2, 256)
    pygame.init()
    pygame.display.set_caption('Raycaster')
    DISPLAY = pygame.display.set_mode((D_W, D_H))
    CLOCK = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    pygame.event.set_allowed([KEYDOWN, MOUSEBUTTONDOWN])

    CAMERA_PLANE = CameraPlane(FOV)
    GAME_FONT_16 = pygame.font.Font('../font/LCD_Solid.ttf', 16)
    GAME_FONT_24 = pygame.font.Font('../font/LCD_Solid.ttf', 24)
    GAME_FONT_32 = pygame.font.Font('../font/LCD_Solid.ttf', 32)

    ENEMY_INFO = enemies.get_enemy_info()
    TILE_VALUES_INFO = graphics.get_tile_values_info(ENEMY_INFO)
    WEAPONS = weapons.get()

    # Sounds
    Door.open_sound,\
    Door.close_sound,\
    PushWall.sound,\
    ExplodingBarrel.sound,\
    ITEM_PICKUP_SOUND,\
    WEAPON_PICKUP_SOUND,\
    SWITCH_SOUND = sounds.get()

    # Textures
    Door.side_texture,\
    Portal.blue_texture,\
    Portal.red_texture = graphics.get_door_side_and_portal_textures()

    QUIT = False
    PAUSED = False
    SHOW_FPS = False

    PLAYER = Player()
    LEVEL = Level()
    LEVEL.start(1)
    pygame.quit()
