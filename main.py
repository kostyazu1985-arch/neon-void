import json
import math
import os
import random
import sys
from dataclasses import (
    dataclass,
    field,
)
import pygame
from pygame.math import Vector2

#--- КОНСТАНТЫ НАСТРОЕК И ИГРОВОГО ОКНА ---
WIDTH, HEIGHT = 1280, 720
FPS = 60
HIGHSCORES_FILE = (
    "highscores.json"
)
BG_COLOR = (8, 8, 20)
CYAN = (0, 240, 255)
MAGENTA = (255, 40, 200)
YELLOW = (255, 220, 60)
WHITE = (240, 240, 255)

#--- ФУНКЦИИ РАБОТЫ С ДАННЫМИ И ГРАФИКОЙ ---
def load_high_scores():
    if os.path.exists(HIGHSCORES_FILE):
        try:
            with open(HIGHSCORES_FILE, "r", encoding="utf-8") as f:
                scores = json.load(f)
                return sorted(scores, key=lambda x: x["score"], reverse=True)[:5]
        except (json.JSONDecodeError, KeyError):
            return []


def save_high_scores(scores):
    try:
        with open(HIGHSCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Ошибка записи таблицы рекордов: {e}")


def glow_circle(radius, color, layers=4):
    size = radius * 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        alpha = int(60 / i)
        pygame.draw.circle(surf, (*color, alpha), center, radius + i * radius // 2)
        pygame.draw.circle(surf, color, center, radius)
        return surf

#--- КЛАССЫ ИГРОВЫХ ОБЪЕКТОВ ---
@dataclass
class Particle:
    pos: Vector2
    vel: Vector2
    color: tuple
    life: float
    max_life: float = field(init=False)

    def __post_init__(self):
        self.max_life = (self.life)

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel *= 0.92
        self.life -= dt
        return self.life > 0

    def draw(self, screen, offset):
        k = self.life / self.max_life
        radius = max(1, int(4 * k))
        color = tuple(int(c * k) for c in self.color)
        pygame.draw.circle(screen, color, self.pos + offset, radius)


@dataclass
class Bullet:
    pos: Vector2
    vel: Vector2
    radius: int = 4

    def update(self, dt):
        self.pos += self.vel * dt
        return 0 <= self.pos.x <= WIDTH and 0 <= self.pos.y <= HEIGHT


class Player:
    SPEED = 380
    DASH_SPEED = 1400
    DASH_TIME = 0.12
    DASH_COOLDOWN = 0.9
    FIRE_RATE = 0.11

    def __init__(self):
        self.pos = Vector2(WIDTH / 2, HEIGHT / 2)
        self.vel = Vector2()
        self.radius = 14
        self.hp = 3
        self.fire_timer = 0.0
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.invulnerable = 0.0
        self.sprite = glow_circle(self.radius, CYAN)

    def update(self, dt, keys):
        direction = Vector2(
            keys[pygame.K_d] - keys[pygame.K_a],
            keys[pygame.K_s] - keys[pygame.K_w],
        )
        if direction.length_squared() > 0:
            direction = (direction.normalize())
            self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
            self.invulnerable = max(0.0, self.invulnerable - dt)
            self.fire_timer = max(0.0, self.fire_timer - dt)

            if self.dash_timer > 0:
                self.dash_timer -= (dt)
            else:
                target = direction * self.SPEED
                self.vel += (target - self.vel) * min(1.0, 12 * dt)

            self.pos += self.vel * dt
            self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
            self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))

    def dash(self):
        if (self.dash_cooldown > 0 or self.vel.length_squared() < 1):
            return False
        self.vel = (self.vel.normalize() * self.DASH_SPEED)
        self.dash_timer = self.DASH_TIME
        self.dash_cooldown = (self.DASH_COOLDOWN)
        self.invulnerable = max(self.invulnerable, self.DASH_TIME + 0.05)
        return True

    def try_fire(self, target):
        if self.fire_timer > 0:
            return None
        self.fire_timer = self.FIRE_RATE
        aim = target - self.pos
        if aim.length_squared() == 0:
            aim = Vector2(0, -1)
        aim = aim.normalize()
        spread = random.uniform(-0.04, 0.04)
        return Bullet(self.pos + aim * 20, aim.rotate_rad(spread) * 900)

    def draw(self, screen, offset):
        if self.invulnerable > 0 and int (self.invulnerable * 20) % 2 == 0:
            return
        rect = self.sprite.get_rect(center=self.pos + offset)
        screen.blit(self.sprite, rect, special_flags=pygame.BLEND_ADD)


class Enemy:
    def __init__(self, pos, speed, hp, radius, color):
        self.pos = Vector2(pos)
        self.speed = speed
        self.hp = hp
        self.radius = radius
        self.color = color
        self.sprite = glow_circle(radius, color)
        self.hit_flash = 0.0

    def update(self, dt, player_pos):
        to_player = player_pos - self.pos
        if to_player.length_squared() > 0:
            self.pos += (to_player.normalize() * self.speed * dt)
            self.hit_flash = max(0.0, self.hit_flash - dt)

    def draw(self, screen, offset):
        rect = self.sprite.get_rect(center=self.pos + offset)
        screen.blit(self.sprite, rect, special_flags=pygame.BLEND_ADD)
        if self.hit_flash > 0:
            pygame.draw.circle(screen, WHITE, self.pos + offset, self.radius)

def spawn_enemy(wave):
    side = random.choice(("top", "bottom", "left", "right"))
    margin = 40
    if side == "top":
        pos = (random.uniform(0, WIDTH), -margin)
    elif side == "bottom":
        pos = (random.uniform(0, WIDTH), HEIGHT + margin)
    elif side == "left":
        pos = (-margin, random.uniform(0, HEIGHT))
    else:
        pos = (WIDTH + margin, random.uniform(0, HEIGHT))

    if wave >= 3and random.random() < 0.2:
        return Enemy(pos, speed=70 + wave * 4, hp=6, radius=26, color=YELLOW)
    return Enemy(pos, speed=120 + wave * 10, hp=1, radius=12, color=MAGENTA)

#--- ОСНОВНОЙ КЛАСС УПРАВЛЕНИЯ ИГРОЙ ---
class Game:
    def __init__(self):



