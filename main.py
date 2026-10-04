import json
import math
import os
import random
import sys
from dataclasses import dataclass, field
import pygame
from pygame.math import Vector2

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
    for i in range (layers, 0, -1):
        alpha = int(60 / i)
        pygame.draw.circle(surf, (*color, alpha), center, radius + i * radius // 2)
        pygame.draw.circle(surf, color, center, radius)
        return surf


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


