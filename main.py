#!/usr/bin/env python3
"""
Havana Ride - Un regalo de amor
Side-scrolling jump game through a Havana street.
"""

import math
import os
import random
import sys

import pygame

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None
    ImageOps = None


pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass


SCREEN_W, SCREEN_H = 900, 600
FPS = 60

SKY_TOP = (118, 179, 224)
SKY_BOT = (204, 229, 246)
ROAD_Y = 392
GROUND_Y = 506
SIDEWALK_Y = 348

# Ajustes de camara/composicion: protagonistas grandes y edificios amplios.
PLAYER_SPRITE_W = 200
PLAYER_SPRITE_H = 140
PLAYER_START_X = 250

# El sprite del jugador ahora se carga desde sprites/drivers.png.
# Este valor alinea la zona de las ruedas/base del sprite con LANE_WHEEL_Y.
# Si lo ves flotando, sube el numero. Si lo ves hundido, bajalo.
PLAYER_WHEEL_OFFSET_Y = 130
PLAYER_WHEEL_OFFSET_RATIO = PLAYER_WHEEL_OFFSET_Y / PLAYER_SPRITE_H

# Tres sendas de la calle: 0 = arriba, 1 = centro, 2 = abajo.
# Los valores son la posicion vertical aproximada de las ruedas sobre la carretera.
LANE_WHEEL_Y = [432, 480, 552]
LANE_TOP = 0
LANE_CENTER = 1
LANE_BOTTOM = 2

# El triciclo ahora se carga desde sprites/tricicle-driver.png.
# Este valor alinea las ruedas del sprite con LANE_WHEEL_Y.
# Si lo ves flotando, sube el numero. Si lo ves hundido, bajalo.
TRICICLO_WHEEL_OFFSET_Y = 145
TRICICLO_SPRITE_W = 300

LANE_CHANGE_LERP = 0.28
BUILDING_MIN_W = 365
BUILDING_MAX_W = 500
BUILDING_MIN_H = 245
BUILDING_MAX_H = 330
BUILDING_GAP_MIN = 18
BUILDING_GAP_MAX = 36
BILLBOARD_W = 270
BILLBOARD_H = 116
# Las fotos usan vallas dinamicas mas grandes. Asi no se deforman ni se ven diminutas.
PHOTO_BILLBOARD_MAX_W = 390
PHOTO_BILLBOARD_MAX_H = 230
PHOTO_FRAME_PAD = 12
PHOTO_MAX_SIZE = (PHOTO_BILLBOARD_MAX_W - PHOTO_FRAME_PAD * 2, PHOTO_BILLBOARD_MAX_H - PHOTO_FRAME_PAD * 2)

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAMEOVER = "gameover"
STATE_WIN = "win"  # Conservado por compatibilidad; el juego ahora no termina al completar los recuerdos.

BILLBOARD_MESSAGES = [
    ("Solo quiero,", "3 besitos", "para que queden", "impares"),
    ("Te quiero,", "Maryan"),
    ("Yo me puedo frenar,", "siempre que %$$%"),
    ("Contigo", "todo es mejor"),
    ("Me gustas", "FULA!"),
    ("Quiero todo", "CONTIGO"),
    ("Tu y yo,", "contra todos los triciclos", "de La Habana"),
    ("Me gustas demasiado"),
    ("MI vida"),
    ("YO? CONTIGO?", "A donde tu quieras"),
    ("LOQUITO", "Me traes"),
    ("MARYANNN, ACABO DE ENTRAR A LA GALERIA", "Y VI TUS VIDEOS", "TE QUIERO MUCHO MUCHO")
]

BUILDING_COLORS = [
    (228, 190, 128),
    (213, 146, 111),
    (242, 210, 147),
    (151, 187, 184),
    (180, 154, 137),
    (238, 174, 129),
    (188, 202, 165),
    (210, 178, 203),
]

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def clamp(value, low, high):
    return max(low, min(high, value))


def draw_text_center(surf, font, text, color, x, y):
    img = font.render(text, True, color)
    surf.blit(img, (x - img.get_width() // 2, y))
    return img


def draw_fit_text_center(surf, font, text, color, x, y, max_width):
    img = font.render(text, True, color)
    if img.get_width() > max_width:
        scale = max_width / img.get_width()
        new_size = (max_width, max(8, int(img.get_height() * scale)))
        img = pygame.transform.smoothscale(img, new_size)
    surf.blit(img, (x - img.get_width() // 2, y))
    return img


def draw_heart_sprite(size=18):
    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    cx, cy = size, size
    r = size // 2
    color = (255, 68, 112)
    pygame.draw.circle(surf, color, (cx - r // 2, cy - r // 4), r)
    pygame.draw.circle(surf, color, (cx + r // 2, cy - r // 4), r)
    pygame.draw.polygon(surf, color, [(cx - r, cy), (cx, cy + r + r // 2), (cx + r, cy)])
    pygame.draw.circle(surf, (255, 170, 195), (cx - r // 2, cy - r // 2), max(2, r // 3))
    return surf


def draw_moto_sprite(width=PLAYER_SPRITE_W, height=PLAYER_SPRITE_H, hair_phase=0.0):
    """
    Fallback dibujado por codigo.

    Normalmente NO se usa: el juego carga sprites/drivers.png.
    Se conserva para que el juego no se caiga si falta el archivo PNG.
    """
    quality = 3
    draw_w, draw_h = width * quality, height * quality
    surf = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
    s = draw_w / 300.0

    def sw(value):
        return max(1, int(value * s))

    def pt(x, y):
        return (sw(x), sw(y))

    base_y = sw(171)
    rear_x = sw(76)
    front_x = sw(225)
    wheel_r = sw(28)

    black = (24, 27, 32)
    dark = (18, 20, 24)
    red = (205, 35, 58)
    red_light = (242, 73, 96)
    chrome = (190, 197, 205)

    def draw_wheel(cx, cy, r):
        pygame.draw.circle(surf, (20, 22, 26), (cx, cy), r)
        pygame.draw.circle(surf, (184, 191, 200), (cx, cy), r, sw(4))
        pygame.draw.circle(surf, (55, 62, 70), (cx, cy), sw(9))
        for ang in range(0, 360, 45):
            x2 = int(cx + math.cos(math.radians(ang)) * r * 0.72)
            y2 = int(cy + math.sin(math.radians(ang)) * r * 0.72)
            pygame.draw.line(surf, (130, 138, 148), (cx, cy), (x2, y2), sw(2))

    def draw_passenger():
        head = pt(106, 72)
        torso = pygame.Rect(sw(88), sw(96), sw(36), sw(49))
        hip = pt(108, 144)

        skin = (236, 190, 152)
        hair_dark = (87, 47, 31)
        hair_mid = (126, 77, 48)
        pink = (223, 73, 142)
        pants = (43, 49, 80)
        shoe = (18, 20, 24)
        outline = (74, 50, 42)

        pygame.draw.ellipse(surf, hair_dark, (head[0] - sw(20), head[1] - sw(13), sw(30), sw(38)))
        pygame.draw.ellipse(surf, hair_mid, (head[0] - sw(15), head[1] - sw(9), sw(20), sw(28)))
        pygame.draw.polygon(surf, hair_dark, [pt(94, 83), pt(80, 100), pt(84, 121), pt(98, 129), pt(107, 114), pt(104, 92)])
        pygame.draw.polygon(surf, hair_mid, [pt(96, 88), pt(88, 101), pt(90, 117), pt(99, 122), pt(104, 111), pt(102, 95)])

        pygame.draw.line(surf, pants, hip, pt(92, 170), sw(8))
        pygame.draw.line(surf, pants, pt(92, 170), pt(75, 188), sw(6))
        pygame.draw.line(surf, pants, pt(113, 144), pt(134, 168), sw(7))
        pygame.draw.line(surf, pants, pt(134, 168), pt(149, 187), sw(5))
        pygame.draw.ellipse(surf, shoe, (sw(64), sw(184), sw(21), sw(8)))
        pygame.draw.ellipse(surf, shoe, (sw(145), sw(184), sw(21), sw(8)))

        pygame.draw.rect(surf, pink, torso, border_radius=sw(10))
        pygame.draw.rect(surf, (161, 42, 96), torso, sw(2), border_radius=sw(10))
        pygame.draw.rect(surf, skin, (head[0] - sw(4), head[1] + sw(15), sw(8), sw(14)), border_radius=sw(3))
        pygame.draw.line(surf, skin, (torso.right - sw(2), torso.y + sw(18)), pt(149, 109), sw(6))
        pygame.draw.circle(surf, skin, pt(149, 109), sw(4))

        face = [pt(97, 56), pt(108, 55), pt(116, 61), pt(118, 69), pt(121, 74), pt(118, 79), pt(112, 87), pt(102, 90), pt(95, 84), pt(93, 72), pt(94, 62)]
        pygame.draw.polygon(surf, skin, face)
        pygame.draw.polygon(surf, outline, face, sw(1))
        pygame.draw.circle(surf, skin, pt(95, 72), sw(4))
        pygame.draw.circle(surf, outline, pt(95, 72), sw(4), sw(1))
        pygame.draw.line(surf, (65, 39, 33), pt(105, 65), pt(111, 65), sw(1))
        pygame.draw.circle(surf, (45, 33, 30), pt(108, 67), sw(2))
        pygame.draw.line(surf, (120, 80, 66), pt(117, 70), pt(121, 74), sw(1))
        pygame.draw.line(surf, (138, 78, 98), pt(112, 80), pt(118, 80), sw(1))

        pygame.draw.ellipse(surf, hair_dark, (head[0] - sw(17), head[1] - sw(19), sw(28), sw(16)))
        pygame.draw.ellipse(surf, hair_mid, (head[0] - sw(11), head[1] - sw(16), sw(17), sw(9)))
        pygame.draw.polygon(surf, hair_dark, [pt(98, 59), pt(106, 58), pt(112, 61), pt(110, 67), pt(101, 66)])
        pygame.draw.polygon(surf, hair_dark, [pt(97, 63), pt(94, 75), pt(98, 80), pt(102, 68)])

    def draw_driver():
        head = pt(169, 66)
        torso = pygame.Rect(sw(151), sw(92), sw(37), sw(53))
        hip = pt(169, 145)

        skin = (223, 172, 132)
        hair_dark = (60, 40, 30)
        hair_mid = (93, 66, 49)
        blue = (37, 97, 182)
        pants = (43, 49, 80)
        shoe = (18, 20, 24)
        outline = (74, 50, 42)

        pygame.draw.ellipse(surf, hair_dark, (head[0] - sw(17), head[1] - sw(13), sw(26), sw(24)))
        pygame.draw.ellipse(surf, hair_mid, (head[0] - sw(9), head[1] - sw(10), sw(14), sw(10)))
        pygame.draw.polygon(surf, hair_dark, [pt(160, 71), pt(156, 84), pt(163, 89), pt(170, 81), pt(169, 71)])

        pygame.draw.line(surf, pants, hip, pt(188, 169), sw(8))
        pygame.draw.line(surf, pants, pt(188, 169), pt(214, 188), sw(6))
        pygame.draw.line(surf, pants, pt(160, 145), pt(143, 169), sw(7))
        pygame.draw.line(surf, pants, pt(143, 169), pt(133, 188), sw(5))
        pygame.draw.ellipse(surf, shoe, (sw(210), sw(184), sw(21), sw(8)))
        pygame.draw.ellipse(surf, shoe, (sw(123), sw(184), sw(21), sw(8)))

        pygame.draw.rect(surf, blue, torso, border_radius=sw(10))
        pygame.draw.rect(surf, (21, 66, 128), torso, sw(2), border_radius=sw(10))
        pygame.draw.rect(surf, skin, (head[0] - sw(4), head[1] + sw(15), sw(8), sw(15)), border_radius=sw(3))

        elbow = pt(201, 108)
        handle_tip = pt(258, 104)
        pygame.draw.line(surf, skin, (torso.right - sw(2), torso.y + sw(18)), elbow, sw(6))
        pygame.draw.line(surf, skin, elbow, handle_tip, sw(5))
        pygame.draw.circle(surf, skin, handle_tip, sw(4))

        face = [pt(160, 52), pt(170, 51), pt(178, 56), pt(181, 63), pt(183, 68), pt(180, 73), pt(175, 79), pt(166, 82), pt(158, 78), pt(156, 69), pt(157, 59)]
        pygame.draw.polygon(surf, skin, face)
        pygame.draw.polygon(surf, outline, face, sw(1))
        pygame.draw.circle(surf, skin, pt(158, 66), sw(4))
        pygame.draw.circle(surf, outline, pt(158, 66), sw(4), sw(1))
        pygame.draw.line(surf, (65, 39, 33), pt(168, 60), pt(173, 60), sw(1))
        pygame.draw.circle(surf, (45, 33, 30), pt(171, 62), sw(2))
        pygame.draw.line(surf, (116, 76, 61), pt(179, 64), pt(183, 68), sw(1))
        pygame.draw.line(surf, (120, 70, 58), pt(172, 73), pt(178, 73), sw(1))

        pygame.draw.ellipse(surf, hair_dark, (head[0] - sw(16), head[1] - sw(18), sw(25), sw(14)))
        pygame.draw.ellipse(surf, hair_mid, (head[0] - sw(9), head[1] - sw(15), sw(12), sw(7)))
        pygame.draw.polygon(surf, hair_dark, [pt(161, 56), pt(168, 54), pt(176, 56), pt(174, 61), pt(165, 61)])
        pygame.draw.polygon(surf, hair_dark, [pt(160, 61), pt(158, 72), pt(162, 75), pt(165, 65)])

    pygame.draw.ellipse(surf, (0, 0, 0, 55), (sw(28), sw(181), sw(244), sw(16)))
    draw_wheel(rear_x, base_y, wheel_r)
    draw_wheel(front_x, base_y, wheel_r)

    pygame.draw.line(surf, chrome, pt(76, 171), pt(136, 142), sw(5))
    pygame.draw.line(surf, chrome, pt(136, 142), pt(225, 171), sw(5))
    pygame.draw.line(surf, chrome, pt(80, 171), pt(168, 137), sw(4))
    pygame.draw.line(surf, chrome, pt(168, 137), pt(225, 171), sw(4))
    pygame.draw.line(surf, (84, 87, 92), pt(88, 177), pt(199, 176), sw(7))
    pygame.draw.line(surf, (220, 222, 226), pt(110, 186), pt(205, 184), sw(4))

    pygame.draw.rect(surf, black, (sw(43), sw(104), sw(56), sw(34)), border_radius=sw(8))
    pygame.draw.rect(surf, (61, 65, 72), (sw(45), sw(106), sw(52), sw(14)), border_radius=sw(6))
    pygame.draw.rect(surf, (205, 45, 55), (sw(47), sw(119), sw(8), sw(8)), border_radius=sw(2))
    pygame.draw.line(surf, chrome, pt(91, 129), pt(106, 139), sw(3))

    pygame.draw.rect(surf, black, (sw(98), sw(123), sw(112), sw(18)), border_radius=sw(8))
    pygame.draw.polygon(surf, red, [pt(150, 105), pt(211, 103), pt(231, 129), pt(212, 155), pt(155, 147), pt(133, 125)])
    pygame.draw.polygon(surf, red_light, [pt(164, 112), pt(207, 109), pt(216, 121), pt(173, 126)])
    pygame.draw.arc(surf, red, (rear_x - wheel_r, base_y - wheel_r, wheel_r * 2, wheel_r * 2), math.radians(190), math.radians(345), sw(5))
    pygame.draw.arc(surf, red, (front_x - wheel_r, base_y - wheel_r, wheel_r * 2, wheel_r * 2), math.radians(200), math.radians(350), sw(5))

    pygame.draw.line(surf, chrome, pt(218, 115), pt(258, 104), sw(4))
    pygame.draw.line(surf, dark, pt(258, 104), pt(275, 103), sw(4))
    pygame.draw.line(surf, chrome, pt(216, 129), pt(227, 163), sw(4))

    draw_passenger()
    draw_driver()

    return pygame.transform.smoothscale(surf, (width, height))


def draw_devil_emoji(surf, cx, cy, r):
    """Cara de diablito simple, legible incluso en sprite pequeno."""
    red = (198, 32, 58)
    red_dark = (132, 20, 41)
    red_light = (234, 79, 104)
    black = (23, 17, 20)
    yellow = (255, 235, 167)

    left_horn = [(cx - int(r * 0.85), cy - int(r * 0.78)), (cx - int(r * 1.18), cy - int(r * 1.40)), (cx - int(r * 0.54), cy - int(r * 1.05))]
    right_horn = [(cx + int(r * 0.85), cy - int(r * 0.78)), (cx + int(r * 1.18), cy - int(r * 1.40)), (cx + int(r * 0.54), cy - int(r * 1.05))]
    pygame.draw.polygon(surf, red_dark, left_horn)
    pygame.draw.polygon(surf, red_dark, right_horn)

    pygame.draw.circle(surf, red, (cx, cy), r)
    pygame.draw.circle(surf, red_dark, (cx, cy), r, max(1, r // 7))
    pygame.draw.circle(surf, red_light, (cx - r // 3, cy - r // 3), max(2, r // 4))

    pygame.draw.line(surf, black, (cx - int(r * 0.60), cy - int(r * 0.20)), (cx - int(r * 0.18), cy - int(r * 0.04)), max(1, r // 7))
    pygame.draw.line(surf, black, (cx + int(r * 0.60), cy - int(r * 0.20)), (cx + int(r * 0.18), cy - int(r * 0.04)), max(1, r // 7))
    pygame.draw.circle(surf, black, (cx - int(r * 0.33), cy + int(r * 0.02)), max(1, r // 10 + 1))
    pygame.draw.circle(surf, black, (cx + int(r * 0.33), cy + int(r * 0.02)), max(1, r // 10 + 1))

    mouth_rect = pygame.Rect(cx - int(r * 0.58), cy + int(r * 0.05), int(r * 1.16), int(r * 0.72))
    pygame.draw.arc(surf, black, mouth_rect, math.radians(12), math.radians(168), max(1, r // 7))
    pygame.draw.polygon(surf, yellow, [(cx - int(r * 0.18), cy + int(r * 0.48)), (cx - int(r * 0.05), cy + int(r * 0.20)), (cx + int(r * 0.08), cy + int(r * 0.48))])
    pygame.draw.polygon(surf, yellow, [(cx + int(r * 0.05), cy + int(r * 0.48)), (cx + int(r * 0.18), cy + int(r * 0.20)), (cx + int(r * 0.31), cy + int(r * 0.48))])


def draw_triciclo_sprite(width=300, height=190):
    """
    Fallback dibujado por codigo.

    Normalmente NO se usa: el juego carga sprites/tricicle-driver.png.
    Se conserva para que el juego no se caiga si falta el archivo PNG.
    """
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    s = width / 300.0

    def sw(v):
        return max(1, int(v * s))

    def pt(x, y):
        return (sw(x), sw(y))

    teal = (58, 205, 205)
    teal_dark = (19, 128, 138)
    teal_mid = (41, 175, 185)
    teal_light = (126, 235, 232)
    glass = (188, 232, 238)
    glass_line = (104, 158, 170)
    metal = (54, 59, 67)
    metal_light = (113, 122, 132)
    tire = (22, 24, 28)
    rim = (238, 241, 244)
    seat_red = (179, 57, 79)
    shadow = (0, 0, 0, 48)
    ad_panel = (244, 234, 201)
    ad_line = (214, 96, 114)

    ground_y = height - sw(28)
    front_wheel = (sw(58), ground_y)
    rear_wheel1 = (sw(194), ground_y)
    rear_wheel2 = (sw(264), ground_y)

    pygame.draw.ellipse(surf, shadow, (sw(12), height - sw(18), width - sw(24), sw(14)))

    body = pygame.Rect(sw(74), sw(44), sw(195), sw(84))
    pygame.draw.rect(surf, teal, body, border_radius=sw(11))
    pygame.draw.rect(surf, teal_dark, body, sw(3), border_radius=sw(11))

    roof = pygame.Rect(sw(62), sw(31), sw(215), sw(17))
    pygame.draw.rect(surf, teal_light, roof, border_radius=sw(6))
    pygame.draw.rect(surf, teal_dark, roof, sw(2), border_radius=sw(6))
    pygame.draw.line(surf, teal_dark, pt(84, 47), pt(84, 123), sw(3))
    pygame.draw.line(surf, teal_dark, pt(269, 47), pt(269, 122), sw(3))

    front_poly = [pt(30, 64), pt(62, 43), pt(97, 43), pt(113, 63), pt(113, 118), pt(86, 130), pt(47, 129), pt(28, 101)]
    pygame.draw.polygon(surf, teal, front_poly)
    pygame.draw.polygon(surf, teal_dark, front_poly, sw(3))

    windshield = [pt(41, 54), pt(65, 46), pt(89, 46), pt(92, 77), pt(48, 80)]
    side_driver_window = [pt(93, 46), pt(108, 62), pt(108, 84), pt(91, 77), pt(89, 46)]
    pygame.draw.polygon(surf, glass, windshield)
    pygame.draw.polygon(surf, glass, side_driver_window)
    pygame.draw.polygon(surf, teal_dark, windshield, sw(2))
    pygame.draw.polygon(surf, teal_dark, side_driver_window, sw(2))
    pygame.draw.line(surf, glass_line, pt(53, 51), pt(60, 78), sw(2))
    pygame.draw.line(surf, glass_line, pt(72, 47), pt(75, 77), sw(2))

    doorway = pygame.Rect(sw(101), sw(64), sw(29), sw(58))
    pygame.draw.line(surf, teal_dark, (doorway.x, doorway.y), (doorway.x, doorway.bottom), sw(3))
    pygame.draw.line(surf, teal_dark, (doorway.right, doorway.y), (doorway.right, doorway.bottom), sw(2))
    pygame.draw.line(surf, teal_dark, (doorway.x, doorway.y), (doorway.right, doorway.y), sw(2))

    open_side = pygame.Rect(sw(127), sw(56), sw(121), sw(43))
    pygame.draw.rect(surf, teal_mid, open_side, border_radius=sw(5))
    pygame.draw.rect(surf, teal_dark, open_side, sw(2), border_radius=sw(5))
    for x in (sw(142), sw(166), sw(190), sw(214), sw(238)):
        pygame.draw.line(surf, teal_dark, (x, open_side.y + sw(2)), (x, open_side.bottom - sw(3)), sw(2))
    for y in (open_side.y + sw(13), open_side.y + sw(27)):
        pygame.draw.line(surf, teal_dark, (open_side.x + sw(3), y), (open_side.right - sw(3), y), sw(2))

    passenger_heads = [pt(148, 61), pt(172, 58), pt(196, 59), pt(221, 62)]
    for hx, hy in passenger_heads:
        pygame.draw.circle(surf, (34, 38, 45), (hx, hy), sw(6))
        pygame.draw.ellipse(surf, (42, 48, 56), (hx - sw(8), hy + sw(5), sw(16), sw(12)))

    sign = pygame.Rect(sw(126), sw(74), sw(82), sw(21))
    pygame.draw.rect(surf, ad_panel, sign, border_radius=sw(3))
    pygame.draw.rect(surf, ad_line, sign, sw(2), border_radius=sw(3))
    pygame.draw.line(surf, ad_line, (sign.x + sw(8), sign.y + sw(6)), (sign.right - sw(8), sign.y + sw(6)), sw(2))
    pygame.draw.line(surf, ad_line, (sign.x + sw(12), sign.y + sw(13)), (sign.right - sw(16), sign.y + sw(13)), sw(2))

    draw_devil_emoji(surf, sw(73), sw(68), sw(12))

    pygame.draw.line(surf, metal, pt(23, 106), pt(38, 66), sw(5))
    pygame.draw.line(surf, metal, pt(23, 106), pt(28, 122), sw(4))
    pygame.draw.line(surf, metal, pt(38, 66), pt(52, 64), sw(4))
    pygame.draw.ellipse(surf, (44, 49, 56), (sw(30), sw(84), sw(22), sw(17)))
    pygame.draw.ellipse(surf, (250, 222, 100), (sw(35), sw(89), sw(10), sw(8)))

    pygame.draw.line(surf, metal, pt(45, 122), pt(120, 122), sw(5))
    pygame.draw.line(surf, metal, pt(120, 122), pt(270, 118), sw(5))
    pygame.draw.line(surf, metal_light, pt(129, 110), pt(257, 110), sw(2))

    pygame.draw.arc(surf, teal_dark, (front_wheel[0] - sw(26), front_wheel[1] - sw(26), sw(52), sw(24)), math.radians(190), math.radians(348), sw(4))
    pygame.draw.arc(surf, teal_dark, (rear_wheel1[0] - sw(21), rear_wheel1[1] - sw(23), sw(42), sw(22)), math.radians(190), math.radians(350), sw(3))
    pygame.draw.arc(surf, teal_dark, (rear_wheel2[0] - sw(21), rear_wheel2[1] - sw(23), sw(42), sw(22)), math.radians(190), math.radians(350), sw(3))
    pygame.draw.line(surf, teal_dark, pt(126, 126), pt(252, 126), sw(3))

    pygame.draw.rect(surf, seat_red, (sw(154), sw(101), sw(24), sw(13)), border_radius=sw(2))
    pygame.draw.rect(surf, seat_red, (sw(183), sw(101), sw(22), sw(13)), border_radius=sw(2))

    for center, radius in ((front_wheel, sw(21)), (rear_wheel1, sw(18)), (rear_wheel2, sw(18))):
        pygame.draw.circle(surf, tire, center, radius)
        pygame.draw.circle(surf, rim, center, radius, sw(3))
        pygame.draw.circle(surf, (116, 124, 135), center, sw(5))

    return surf


def load_oriented_image(path):
    if Image is not None and ImageOps is not None:
        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img).convert("RGBA")
            mode = img.mode
            size = img.size
            data = img.tobytes()
            return pygame.image.fromstring(data, size, mode).convert_alpha()
        except Exception:
            pass
    return pygame.image.load(path).convert_alpha()


def trim_transparent_borders(sprite):
    """Recorta bordes transparentes de un sprite PNG sin romper la transparencia."""
    try:
        crop = sprite.get_bounding_rect(min_alpha=1)
        if crop.width > 0 and crop.height > 0:
            return sprite.subsurface(crop).copy()
    except Exception:
        pass
    return sprite


def load_player_sprite(width=PLAYER_SPRITE_W):
    """
    Carga el sprite externo de los protagonistas en la moto.

    Ruta esperada:
        sprites/drivers.png

    Mantiene transparencia, recorta bordes vacios si existen y escala proporcionalmente.
    Si el archivo falta, usa la moto dibujada por codigo como fallback.
    """
    path = resource_path(os.path.join("sprites", "drivers.png"))

    try:
        sprite = load_oriented_image(path)
    except Exception as exc:
        print(f"No se pudo cargar {path}: {exc}")
        print("Usando fallback draw_moto_sprite().")
        return draw_moto_sprite(PLAYER_SPRITE_W, PLAYER_SPRITE_H)

    sprite = trim_transparent_borders(sprite)

    ratio = width / sprite.get_width()
    height = max(1, int(sprite.get_height() * ratio))
    return pygame.transform.smoothscale(sprite, (width, height))


def load_triciclo_sprite(width=TRICICLO_SPRITE_W):
    """
    Carga el sprite externo del triciclo con conductor.

    Ruta esperada:
        sprites/tricicle-driver.png

    Mantiene transparencia, recorta bordes vacios si existen y escala proporcionalmente.
    Si el archivo falta, usa el triciclo dibujado por codigo como fallback.
    """
    path = resource_path(os.path.join("sprites", "tricicle-driver.png"))

    try:
        sprite = load_oriented_image(path)
    except Exception as exc:
        print(f"No se pudo cargar {path}: {exc}")
        print("Usando fallback draw_triciclo_sprite().")
        return draw_triciclo_sprite(300, 190)

    sprite = trim_transparent_borders(sprite)

    ratio = width / sprite.get_width()
    height = max(1, int(sprite.get_height() * ratio))
    return pygame.transform.smoothscale(sprite, (width, height))


def split_phrase_for_billboard(text):
    text = " ".join(str(text).strip().split())
    if not text:
        return "", ""
    words = text.split()
    if len(words) == 1:
        return words[0], ""
    total = sum(len(w) for w in words) + len(words) - 1
    best_i = 1
    best_score = 10**9
    left_len = 0
    for i, word in enumerate(words[:-1], start=1):
        left_len += len(word)
        if i > 1:
            left_len += 1
        score = abs(left_len - total / 2)
        if score < best_score:
            best_score = score
            best_i = i
    return " ".join(words[:best_i]), " ".join(words[best_i:])


def normalize_billboard_lines(message):
    if isinstance(message, str):
        parts = [message]
    elif isinstance(message, (tuple, list)):
        parts = list(message)
    else:
        parts = [str(message)]

    lines = []
    for part in parts:
        if part is None:
            continue
        text = " ".join(str(part).strip().split())
        if text:
            lines.append(text)

    if not lines:
        return ["", ""]

    if len(lines) == 1:
        a, b = split_phrase_for_billboard(lines[0])
        return [line for line in (a, b) if line]

    return lines


def load_billboard_messages():
    path = resource_path(os.path.join("assets", "frases.txt"))
    if not os.path.exists(path):
        return [normalize_billboard_lines(item) for item in BILLBOARD_MESSAGES]

    loaded = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "|" in line:
                    loaded.append(normalize_billboard_lines(line.split("|")))
                else:
                    loaded.append(normalize_billboard_lines(line))
    except OSError:
        return [normalize_billboard_lines(item) for item in BILLBOARD_MESSAGES]

    return loaded or [normalize_billboard_lines(item) for item in BILLBOARD_MESSAGES]


def draw_billboard_text(width, height, *args):
    if len(args) == 4:
        text1, text2, font_big, font_small = args
        lines = normalize_billboard_lines((text1, text2))
    elif len(args) == 3:
        raw_lines, font_big, font_small = args
        lines = normalize_billboard_lines(raw_lines)
    else:
        raise TypeError("draw_billboard_text espera texto y fuentes")

    max_font_w = 0
    for i, line in enumerate(lines):
        font = font_big if i == 0 and len(lines) <= 2 else font_small
        max_font_w = max(max_font_w, font.size(line)[0])

    dynamic_w = max(width, min(520, max_font_w + 72))
    dynamic_h = max(height, 48 + len(lines) * (font_small.get_height() + 7))
    width, height = dynamic_w, dynamic_h

    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (249, 236, 204), (0, 0, width, height), border_radius=8)
    pygame.draw.rect(surf, (109, 72, 60), (0, 0, width, height), 5, border_radius=8)
    pygame.draw.rect(surf, (228, 73, 118), (10, 10, width - 20, height - 20), 4, border_radius=6)

    if len(lines) <= 2:
        y1 = max(12, height // 2 - font_big.get_height() - 6)
        y2 = min(height - font_small.get_height() - 16, height // 2 + 8)
        draw_fit_text_center(surf, font_big, lines[0], (86, 38, 55), width // 2, y1, width - 34)
        if len(lines) > 1 and lines[1]:
            draw_fit_text_center(surf, font_small, lines[1], (129, 55, 73), width // 2, y2, width - 34)
    else:
        line_h = font_small.get_height() + 7
        total_h = len(lines) * line_h - 7
        y = max(18, height // 2 - total_h // 2)
        for i, line in enumerate(lines):
            color = (86, 38, 55) if i == 0 else (129, 55, 73)
            draw_fit_text_center(surf, font_small, line, color, width // 2, y, width - 38)
            y += line_h

    heart = draw_heart_sprite(10)
    surf.blit(heart, (17, height - 36))
    surf.blit(heart, (width - 39, height - 36))
    return surf


def load_couple_photos(max_size=PHOTO_MAX_SIZE):
    assets_dir = resource_path("assets")
    photos = []
    if not os.path.isdir(assets_dir):
        return photos

    for root, _, files in os.walk(assets_dir):
        for name in sorted(files):
            if not name.lower().endswith(IMAGE_EXTS):
                continue
            path = os.path.join(root, name)
            try:
                img = load_oriented_image(path)
            except pygame.error:
                continue

            rect = img.get_rect()
            if rect.width <= 0 or rect.height <= 0:
                continue

            scale = min(max_size[0] / rect.width, max_size[1] / rect.height, 1.0)
            size = (max(1, int(rect.width * scale)), max(1, int(rect.height * scale)))
            scaled = pygame.transform.smoothscale(img, size) if size != rect.size else img.copy()

            frame_w = size[0] + PHOTO_FRAME_PAD * 2
            frame_h = size[1] + PHOTO_FRAME_PAD * 2
            framed = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            pygame.draw.rect(framed, (255, 245, 219), framed.get_rect(), border_radius=8)
            pygame.draw.rect(framed, (111, 72, 61), framed.get_rect(), 4, border_radius=8)
            framed.blit(scaled, (PHOTO_FRAME_PAD, PHOTO_FRAME_PAD))
            photos.append(framed)
    return photos


class Triciclo:
    def __init__(self, x, sprite, lane=LANE_CENTER):
        self.x = x
        self.sprite = sprite
        self.lane = int(clamp(lane, LANE_TOP, LANE_BOTTOM))
        self.y = LANE_WHEEL_Y[self.lane] - TRICICLO_WHEEL_OFFSET_Y
        self.passed = False

    @property
    def rect(self):
        # Hitbox proporcional para no chocar con aire transparente del PNG.
        return pygame.Rect(
            int(self.x + self.sprite.get_width() * 0.08),
            int(self.y + self.sprite.get_height() * 0.18),
            int(self.sprite.get_width() * 0.84),
            int(self.sprite.get_height() * 0.66),
        )

    def update(self, speed):
        self.x -= speed

    def draw(self, surf):
        surf.blit(self.sprite, (int(self.x), int(self.y)))


class FloatingHeart:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = 60

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= 1


class LoveShot:
    def __init__(self, x, y, lane=LANE_CENTER):
        self.x = x
        self.y = y
        self.lane = int(clamp(lane, LANE_TOP, LANE_BOTTOM))
        self.vx = 12.5
        self.life = 86
        self.pulse = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 6, int(self.y) - 6, 34, 30)

    def update(self):
        self.x += self.vx
        self.pulse += 0.24
        self.y += math.sin(self.pulse) * 0.45
        self.life -= 1


class HavanaRide:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Havana Ride ❤️ — El Regalo")
        self.clock = pygame.time.Clock()
        self.state = STATE_MENU

        self.font_big = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_sm = pygame.font.SysFont("Arial", 20)
        self.font_tiny = pygame.font.SysFont("Arial", 15)
        self.font_billboard_big = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_billboard_sm = pygame.font.SysFont("Arial", 22)

        # Antes:
        # self.moto_sprite = draw_moto_sprite(PLAYER_SPRITE_W, PLAYER_SPRITE_H)
        #
        # Ahora se usa el PNG externo:
        self.moto_sprite = load_player_sprite(PLAYER_SPRITE_W)

        # Ajuste dinamico: si drivers.png tiene otra proporcion, la base se mantiene alineada.
        self.player_wheel_offset_y = max(1, int(self.moto_sprite.get_height() * PLAYER_WHEEL_OFFSET_RATIO))

        # Antes:
        # self.triciclo_sprite = draw_triciclo_sprite(300, 190)
        #
        # Ahora se usa el PNG externo:
        self.triciclo_sprite = load_triciclo_sprite(TRICICLO_SPRITE_W)

        self.heart_sprite = draw_heart_sprite(12)
        self.shot_sprite = draw_heart_sprite(15)
        self.photos = load_couple_photos()
        self.billboards = self._build_billboards()
        self.buildings = self._build_city()

        self.menu_t = 0.0
        self._reset_game()

    def _build_billboards(self):
        text_billboards = [
            draw_billboard_text(BILLBOARD_W, BILLBOARD_H, lines, self.font_billboard_big, self.font_billboard_sm)
            for lines in load_billboard_messages()
        ]
        mixed = []
        photo_i = 0
        text_i = 0
        while photo_i < len(self.photos) or text_i < len(text_billboards):
            if photo_i < len(self.photos):
                mixed.append(self.photos[photo_i])
                photo_i += 1
            if text_i < len(text_billboards):
                mixed.append(text_billboards[text_i])
                text_i += 1
        return mixed or text_billboards

    def _build_city(self):
        rng = random.Random(12)
        buildings = []
        x = -80

        for billboard in self.billboards:
            w = rng.randint(BUILDING_MIN_W, BUILDING_MAX_W)
            h = rng.randint(BUILDING_MIN_H, BUILDING_MAX_H)
            if billboard is not None:
                bw, bh = billboard.get_size()
                w = max(w, bw + 70)
                h = max(h, bh + 105)
            color = rng.choice(BUILDING_COLORS)
            buildings.append({
                "x": x,
                "w": w,
                "h": h,
                "color": color,
                "roof": rng.choice(["flat", "arch", "water", "balcony"]),
                "billboard": billboard,
                "seed": rng.randint(1, 99999),
            })
            x += w + rng.randint(BUILDING_GAP_MIN, BUILDING_GAP_MAX)

        for _ in range(4):
            w = rng.randint(BUILDING_MIN_W, BUILDING_MAX_W)
            h = rng.randint(BUILDING_MIN_H, BUILDING_MAX_H)
            color = rng.choice(BUILDING_COLORS)
            buildings.append({
                "x": x,
                "w": w,
                "h": h,
                "color": color,
                "roof": rng.choice(["flat", "arch", "water", "balcony"]),
                "billboard": None,
                "seed": rng.randint(1, 99999),
            })
            x += w + rng.randint(BUILDING_GAP_MIN, BUILDING_GAP_MAX)

        self.city_width = x + 260
        return buildings

    def _reset_game(self):
        self.player_x = PLAYER_START_X
        self.lane = LANE_CENTER
        self.target_lane = LANE_CENTER
        self.player_y = self._player_y_for_lane(self.lane)
        self.vel_y = 0.0
        self.on_ground = True
        self.world_speed = 5.2
        self.distance = 0.0
        self.score = 0
        self.bonus_score = 0
        self.lives = 3
        self.memory_complete_distance = max(11800, int((getattr(self, "city_width", 9000) - SCREEN_W + 260) / 0.30))
        self.win_distance = self.memory_complete_distance
        self.competitive_mode = False
        self.competitive_distance = 0.0
        self.spawn_timer = 92
        self.spawn_interval = 128
        self.invincible = 0
        self.flash_timer = 0
        self.feedback_text = ""
        self.feedback_timer = 0
        self.memory_mode = False
        self.obstacles = []
        self.hearts = []
        self.shots = []
        self.shoot_cooldown = 0
        self.road_scroll = 0.0
        self.city_scroll = 0.0
        self.shake = 0

    def _player_y_for_lane(self, lane):
        lane = int(clamp(lane, LANE_TOP, LANE_BOTTOM))
        return LANE_WHEEL_Y[lane] - self.player_wheel_offset_y

    def _change_lane(self, direction):
        if self.state != STATE_PLAYING or self.memory_mode:
            return
        new_lane = int(clamp(self.target_lane + direction, LANE_TOP, LANE_BOTTOM))
        if new_lane == self.target_lane:
            return
        self.target_lane = new_lane
        self.feedback_text = "Cambio de senda"
        self.feedback_timer = 28
        self._burst(
            self.player_x + self.moto_sprite.get_width() // 2,
            self.player_y + int(self.moto_sprite.get_height() * 0.62),
            10,
        )

    def _jump(self):
        self._change_lane(-1)

    def _toggle_memory_mode(self):
        self.memory_mode = not self.memory_mode
        if self.memory_mode:
            self.obstacles.clear()
            self.shots.clear()
            self.vel_y = 0.0
            self.target_lane = self.lane
            self.player_y = self._player_y_for_lane(self.lane)
            self.on_ground = True
            self.shake = 0
            self.flash_timer = 0
            self.feedback_text = "Modo recuerdo: lee con calma"
            self.feedback_timer = 100
        else:
            self.feedback_text = "Seguimos juntos"
            self.feedback_timer = 55

    def _shoot(self):
        if self.state != STATE_PLAYING or self.memory_mode or self.shoot_cooldown > 0:
            return
        shot_lane = self.target_lane
        x = self.player_x + self.moto_sprite.get_width() - 32
        y = self._player_y_for_lane(shot_lane) + int(self.moto_sprite.get_height() * 0.60)
        self.shots.append(LoveShot(x, y, shot_lane))
        self.shoot_cooldown = 15
        self._burst(x, y, 3)

    def _hurt(self):
        if self.invincible > 0:
            return
        self.lives -= 1
        self.invincible = 115
        self.flash_timer = 16
        self.shake = 16
        self.feedback_text = "¡Esquiva o dispara corazones!"
        self.feedback_timer = 70
        self._burst(
            self.player_x + int(self.moto_sprite.get_width() * 0.27),
            self.player_y + int(self.moto_sprite.get_height() * 0.28),
            12,
        )
        if self.lives <= 0:
            self.state = STATE_GAMEOVER

    def _burst(self, x, y, amount=10):
        for _ in range(amount):
            self.hearts.append(FloatingHeart(
                x + random.randint(-14, 14),
                y + random.randint(-10, 10),
                random.uniform(-2.2, 2.2),
                random.uniform(-4.2, -1.2),
            ))

    def update(self):
        self.menu_t += 0.03
        if self.state != STATE_PLAYING:
            for heart in self.hearts:
                heart.update()
            self.hearts = [h for h in self.hearts if h.life > 0]
            return

        if self.memory_mode:
            self.obstacles.clear()
            self.shots.clear()
            self.vel_y = 0.0
            self.target_lane = self.lane
            self.player_y = self._player_y_for_lane(self.lane)
            self.on_ground = True
            self.shake = 0
            self.flash_timer = 0
            for heart in self.hearts:
                heart.update()
            self.hearts = [h for h in self.hearts if h.life > 0]
            self.invincible = max(0, self.invincible - 1)
            self.feedback_timer = max(0, self.feedback_timer - 1)
            return

        keys = pygame.key.get_pressed()
        move = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move += 1
        self.player_x += move * 6.2
        self.player_x = clamp(self.player_x, 22, SCREEN_W - self.moto_sprite.get_width() - 24)

        if keys[pygame.K_j] or keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            self._shoot()

        target_y = self._player_y_for_lane(self.target_lane)
        self.player_y += (target_y - self.player_y) * LANE_CHANGE_LERP
        if abs(self.player_y - target_y) < 0.5:
            self.player_y = target_y
            self.lane = self.target_lane
        self.vel_y = 0.0
        self.on_ground = True

        self.distance += self.world_speed
        if (not self.competitive_mode) and self.distance >= self.memory_complete_distance:
            self.competitive_mode = True
            self.competitive_distance = 0.0
            self.spawn_interval = min(self.spawn_interval, 76)
            self.spawn_timer = min(self.spawn_timer, 35)
            self.feedback_text = "¡Modo competitivo! Mas triciclos y mas velocidad"
            self.feedback_timer = 150
            self._burst(SCREEN_W // 2, 210, 42)

        if self.competitive_mode:
            self.competitive_distance += self.world_speed
            self.score = int(self.distance / 12) + int(self.competitive_distance / 8) + self.bonus_score
            self.world_speed = min(12.4, 7.35 + self.competitive_distance / 6200)
        else:
            self.score = int(self.distance / 14) + self.bonus_score
            self.world_speed = min(7.2, 5.2 + self.distance / 9000)
        self.road_scroll = (self.road_scroll + self.world_speed) % 92
        self.city_scroll = (self.city_scroll + self.world_speed * 0.30) % getattr(self, "city_width", 9000)

        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            first_lane = random.randint(LANE_TOP, LANE_BOTTOM)
            self.obstacles.append(Triciclo(SCREEN_W + random.randint(15, 110), self.triciclo_sprite, first_lane))
            if self.competitive_mode:
                if random.random() < min(0.62, 0.28 + self.competitive_distance / 26000):
                    lanes = [LANE_TOP, LANE_CENTER, LANE_BOTTOM]
                    lanes.remove(first_lane)
                    self.obstacles.append(Triciclo(SCREEN_W + random.randint(175, 285), self.triciclo_sprite, random.choice(lanes)))
                self.spawn_interval = max(42, self.spawn_interval - 2)
                self.spawn_timer = self.spawn_interval + random.randint(-14, 18)
            else:
                self.spawn_interval = max(86, self.spawn_interval - 3)
                self.spawn_timer = self.spawn_interval + random.randint(-16, 28)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        for shot in self.shots:
            shot.update()

        player_rect = pygame.Rect(
            int(self.player_x + self.moto_sprite.get_width() * 0.16),
            int(self.player_y + self.moto_sprite.get_height() * 0.28),
            int(self.moto_sprite.get_width() * 0.68),
            int(self.moto_sprite.get_height() * 0.60),
        )

        kept_obstacles = []
        for obs in self.obstacles:
            obs.update(self.world_speed)
            destroyed = False
            for shot in self.shots:
                same_shot_lane = getattr(shot, "lane", LANE_CENTER) == getattr(obs, "lane", LANE_CENTER)
                if shot.life > 0 and same_shot_lane and shot.rect.colliderect(obs.rect):
                    shot.life = 0
                    destroyed = True
                    self.bonus_score += 75
                    self.score = int(self.distance / 14) + self.bonus_score
                    self.feedback_text = "¡Corazonazo!"
                    self.feedback_timer = 48
                    self._burst(obs.x + obs.sprite.get_width() // 2, obs.y + 28, 16)
                    break

            if destroyed:
                continue

            if not obs.passed and obs.x + obs.sprite.get_width() < self.player_x:
                obs.passed = True
                self.bonus_score += 35
                self.score = int(self.distance / 14) + self.bonus_score
                self.feedback_text = "¡Bien esquivado!"
                self.feedback_timer = 38
                self._burst(
                    self.player_x + int(self.moto_sprite.get_width() * 0.46),
                    self.player_y + int(self.moto_sprite.get_height() * 0.28),
                    4,
                )

            same_lane = abs((self.player_y + self.player_wheel_offset_y) - LANE_WHEEL_Y[getattr(obs, "lane", LANE_CENTER)]) < 46
            if same_lane and player_rect.colliderect(obs.rect):
                self._hurt()
                continue

            if obs.x > -360:
                kept_obstacles.append(obs)

        self.obstacles = kept_obstacles
        self.shots = [s for s in self.shots if s.life > 0 and s.x < SCREEN_W + 90]

        for heart in self.hearts:
            heart.update()
        self.hearts = [h for h in self.hearts if h.life > 0]

        self.invincible = max(0, self.invincible - 1)
        self.flash_timer = max(0, self.flash_timer - 1)
        self.feedback_timer = max(0, self.feedback_timer - 1)
        self.shake = max(0, self.shake - 1)

    def _draw_sky(self, surf):
        for y in range(SIDEWALK_Y):
            t = y / SIDEWALK_Y
            c = tuple(int(SKY_TOP[i] + (SKY_BOT[i] - SKY_TOP[i]) * t) for i in range(3))
            pygame.draw.line(surf, c, (0, y), (SCREEN_W, y))
        pygame.draw.circle(surf, (255, 231, 142), (92, 86), 34)
        pygame.draw.circle(surf, (255, 242, 184), (92, 86), 24)

    def _draw_building(self, surf, building, screen_x):
        w, h = building["w"], building["h"]
        y = SIDEWALK_Y - h
        color = building["color"]
        rng = random.Random(building["seed"])

        pygame.draw.rect(surf, color, (screen_x, y, w, h))
        pygame.draw.rect(surf, (96, 83, 75), (screen_x, y, w, h), 3)

        if building["roof"] == "arch":
            pygame.draw.arc(surf, (105, 87, 74), (screen_x + 30, y - 28, w - 60, 54), math.pi, math.tau, 7)
            pygame.draw.line(surf, (80, 68, 61), (screen_x + 24, y), (screen_x + w - 24, y), 4)
        elif building["roof"] == "water":
            pygame.draw.rect(surf, (86, 96, 108), (screen_x + w - 74, y - 31, 50, 28), border_radius=6)
            pygame.draw.line(surf, (55, 63, 73), (screen_x + w - 84, y), (screen_x + w - 12, y), 4)
        elif building["roof"] == "balcony":
            pygame.draw.rect(surf, (126, 100, 79), (screen_x - 4, y - 9, w + 8, 10))
            pygame.draw.line(surf, (80, 65, 58), (screen_x + 42, y - 8), (screen_x + w - 42, y - 8), 4)
        else:
            pygame.draw.rect(surf, (121, 96, 76), (screen_x - 5, y - 9, w + 10, 10))

        win_w, win_h = 20, 30
        for wy in range(y + 145, SIDEWALK_Y - 62, 60):
            for wx in range(screen_x + 42, screen_x + w - 58, 78):
                if rng.random() < 0.86:
                    lit = rng.random() < 0.50
                    wc = (255, 231, 146) if lit else (66, 88, 119)
                    pygame.draw.rect(surf, wc, (wx, wy, win_w, win_h), border_radius=3)
                    pygame.draw.line(surf, (73, 70, 73), (wx + win_w // 2, wy), (wx + win_w // 2, wy + win_h), 2)
                    if rng.random() < 0.35:
                        pygame.draw.line(surf, (98, 86, 78), (wx - 8, wy + win_h + 5), (wx + win_w + 8, wy + win_h + 5), 3)

        door_w, door_h = 45, 65
        pygame.draw.rect(surf, (88, 57, 43), (screen_x + w // 2 - door_w // 2, SIDEWALK_Y - door_h, door_w, door_h), border_radius=6)
        pygame.draw.circle(surf, (237, 198, 92), (screen_x + w // 2 + door_w // 2 - 10, SIDEWALK_Y - 31), 3)

        billboard = building["billboard"]
        if billboard:
            bw, bh = billboard.get_size()
            max_bw = w - 48
            draw_board = billboard
            if bw > max_bw:
                ratio = max_bw / bw
                draw_board = pygame.transform.smoothscale(billboard, (int(bw * ratio), int(bh * ratio)))
                bw, bh = draw_board.get_size()
            bx = screen_x + w // 2 - bw // 2
            by = y + 24
            if by + bh > SIDEWALK_Y - 48:
                by = max(y + 12, SIDEWALK_Y - 48 - bh)
            pole_h = max(0, SIDEWALK_Y - by - bh)
            if pole_h > 0:
                pygame.draw.rect(surf, (75, 64, 57), (bx + 24, by + bh, 7, pole_h))
                pygame.draw.rect(surf, (75, 64, 57), (bx + bw - 31, by + bh, 7, pole_h))
            surf.blit(draw_board, (bx, by))

    def _draw_city(self, surf):
        width = getattr(self, "city_width", SCREEN_W + 900)
        offset = int(self.city_scroll % width)
        for loop in range(-1, 2):
            base = loop * width - offset
            for building in self.buildings:
                sx = base + building["x"]
                if sx < -building["w"] - 20 or sx > SCREEN_W + 20:
                    continue
                self._draw_building(surf, building, int(sx))

    def _draw_street(self, surf):
        pygame.draw.rect(surf, (173, 165, 151), (0, SIDEWALK_Y, SCREEN_W, ROAD_Y - SIDEWALK_Y))
        for x in range(-80, SCREEN_W + 80, 82):
            pygame.draw.line(surf, (143, 134, 123), (x - int(self.road_scroll * 0.35), SIDEWALK_Y), (x + 58 - int(self.road_scroll * 0.35), ROAD_Y), 2)
        pygame.draw.rect(surf, (232, 215, 120), (0, ROAD_Y - 8, SCREEN_W, 8))
        pygame.draw.rect(surf, (118, 116, 113), (0, ROAD_Y - 2, SCREEN_W, 8))

        pygame.draw.rect(surf, (50, 52, 56), (0, ROAD_Y, SCREEN_W, SCREEN_H - ROAD_Y))
        pygame.draw.rect(surf, (39, 41, 45), (0, GROUND_Y + 18, SCREEN_W, SCREEN_H - GROUND_Y - 18))
        for y in (440, 532):
            for x in range(-120, SCREEN_W + 120, 92):
                dx = x - int(self.road_scroll)
                pygame.draw.rect(surf, (224, 216, 172), (dx, y, 48, 5), border_radius=2)
        for _ in range(70):
            rng = random.Random(_)
            x = (rng.randint(0, SCREEN_W) - int(self.road_scroll * (1 + rng.random()))) % SCREEN_W
            y = rng.randint(ROAD_Y + 16, SCREEN_H - 18)
            shade = rng.randint(61, 75)
            surf.set_at((x, y), (shade, shade, shade))

    def _draw_hud(self, surf):
        for i in range(self.lives):
            surf.blit(self.heart_sprite, (20 + i * 34, 18))

        score = self.font_sm.render(f"PUNTOS: {self.score}", True, (255, 255, 210))
        surf.blit(score, (20, 54))

        prog = clamp(self.distance / self.memory_complete_distance, 0, 1)
        pygame.draw.rect(surf, (43, 43, 49), (SCREEN_W // 2 - 120, 20, 240, 14), border_radius=4)
        pygame.draw.rect(surf, (248, 87, 142), (SCREEN_W // 2 - 120, 20, int(240 * prog), 14), border_radius=4)
        progress_label = "COMPETITIVO" if self.competitive_mode else "RECUERDOS"
        draw_text_center(surf, self.font_tiny, progress_label, (255, 255, 230), SCREEN_W // 2, 39)

        display_speed = 0 if self.memory_mode else self.world_speed
        speed_pct = clamp((display_speed - 5.2) / 7.2, 0, 1)
        pygame.draw.rect(surf, (43, 43, 49), (SCREEN_W - 166, 20, 140, 14), border_radius=4)
        pygame.draw.rect(surf, (88, 203, 226), (SCREEN_W - 166, 20, int(140 * speed_pct), 14), border_radius=4)
        label = self.font_tiny.render("VELOCIDAD", True, (255, 255, 230))
        surf.blit(label, (SCREEN_W - 166, 39))
        if self.competitive_mode:
            mode = self.font_tiny.render("SIN FINAL: SOBREVIVE", True, (255, 223, 122))
            surf.blit(mode, (SCREEN_W - 190, 58))

        hint_text = "[←/→] Moverse   [↑/↓] Cambiar senda   [J/CTRL] Corazones por senda   [P/ENTER] Modo recuerdo"
        hint = self.font_tiny.render(hint_text, True, (255, 232, 242))
        surf.blit(hint, (20, SCREEN_H - 25))

        if self.feedback_timer > 0 and self.feedback_text:
            txt = self.font_sm.render(self.feedback_text, True, (255, 235, 178))
            txt.set_alpha(clamp(self.feedback_timer * 6, 55, 255))
            surf.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 82))

        if self.memory_mode:
            self._draw_memory_overlay(surf)

    def _draw_memory_overlay(self, surf):
        box = pygame.Rect(165, SCREEN_H - 90, 570, 58)
        panel = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (255, 244, 224, 235), panel.get_rect(), border_radius=18)
        pygame.draw.rect(panel, (224, 67, 105), panel.get_rect(), 3, border_radius=18)
        surf.blit(panel, box)
        title = self.font_sm.render("MODO RECUERDO: la moto esta parada", True, (116, 45, 70))
        subtitle = self.font_tiny.render("Los triciclos no aparecen. Lee los carteles y mira las fotos con calma.", True, (82, 70, 70))
        surf.blit(title, (box.centerx - title.get_width() // 2, box.y + 9))
        surf.blit(subtitle, (box.centerx - subtitle.get_width() // 2, box.y + 35))

    def _draw_player(self, surf):
        if self.invincible > 0 and (self.invincible // 7) % 2 == 0:
            return

        # Importante: no redibujar la moto por codigo aqui.
        # Se usa self.moto_sprite, que viene de sprites/drivers.png.
        surf.blit(self.moto_sprite, (int(self.player_x), int(self.player_y)))

    def _draw_shots(self, surf):
        for shot in self.shots:
            sprite = self.shot_sprite.copy()
            sprite.set_alpha(clamp(shot.life * 5, 0, 255))
            surf.blit(sprite, (int(shot.x), int(shot.y)))

    def _draw_hearts(self, surf):
        for heart in self.hearts:
            sprite = self.heart_sprite.copy()
            sprite.set_alpha(clamp(heart.life * 5, 0, 255))
            surf.blit(sprite, (int(heart.x), int(heart.y)))

    def draw_world(self):
        surf = self.screen
        shake_x = random.randint(-self.shake, self.shake) if self.shake else 0
        world = pygame.Surface((SCREEN_W, SCREEN_H))
        self._draw_sky(world)
        self._draw_city(world)
        self._draw_street(world)
        self._draw_shots(world)
        drawables = [(getattr(obs, "lane", LANE_CENTER), obs) for obs in self.obstacles]
        drawables.append((self.target_lane, "player"))
        for _, item in sorted(drawables, key=lambda pair: pair[0]):
            if item == "player":
                self._draw_player(world)
            else:
                item.draw(world)
        self._draw_hearts(world)
        surf.blit(world, (shake_x, 0))

        if self.flash_timer > 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((255, 71, 89, int(85 * self.flash_timer / 16)))
            surf.blit(overlay, (0, 0))

    def draw_menu(self):
        self.draw_world()
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((12, 16, 25, 92))
        self.screen.blit(overlay, (0, 0))
        draw_text_center(self.screen, self.font_big, "HAVANA RIDE", (255, 93, 138), SCREEN_W // 2, 112)
        draw_text_center(self.screen, self.font_med, "Ibamos por la carretera abrazaditos,pero llegaron triciclos", (255, 229, 236), SCREEN_W // 2, 176)

        controls = [
            ("← / →  A / D", "Mover la moto"),
            ("↑ / ↓", "Cambiar de senda"),
            ("J / CTRL", "Lanzar corazones por senda"),
            ("P / ENTER", "Modo recuerdo"),
            ("ENTER", "Comenzar"),
        ]
        y = 258
        for key, action in controls:
            k = self.font_sm.render(key, True, (255, 223, 122))
            a = self.font_sm.render(action, True, (245, 245, 238))
            self.screen.blit(k, (SCREEN_W // 2 - 185, y))
            self.screen.blit(a, (SCREEN_W // 2 + 10, y))
            y += 38

        if int(self.menu_t * 2) % 2 == 0:
            draw_text_center(self.screen, self.font_med, "Presiona ENTER para comenzar", (255, 255, 196), SCREEN_W // 2, 482)

    def draw_gameover(self):
        self.draw_world()
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((40, 0, 10, 178))
        self.screen.blit(overlay, (0, 0))
        draw_text_center(self.screen, self.font_big, "GAME OVER", (255, 83, 96), SCREEN_W // 2, 178)
        draw_text_center(self.screen, self.font_med, "Los triciclos ganaron, fuck triciclos", (255, 224, 224), SCREEN_W // 2, 252)
        draw_text_center(self.screen, self.font_sm, f"Puntos: {self.score}", (255, 242, 194), SCREEN_W // 2, 318)
        if int(self.menu_t * 2) % 2 == 0:
            draw_text_center(self.screen, self.font_sm, "ENTER para reintentar  |  ESC para salir", (255, 255, 210), SCREEN_W // 2, 404)

    def draw_win(self):
        self.draw_world()
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((5, 18, 35, 154))
        self.screen.blit(overlay, (0, 0))
        draw_text_center(self.screen, self.font_big, "¡RECUERDOS COMPLETOS!", (255, 224, 94), SCREEN_W // 2, 148)
        draw_text_center(self.screen, self.font_med, "Ahora empieza el modo competitivo infinito", (255, 211, 234), SCREEN_W // 2, 224)
        draw_text_center(self.screen, self.font_sm, "Ganamos maryan, pero ahora se pone bueno", (232, 241, 255), SCREEN_W // 2, 280)
        draw_text_center(self.screen, self.font_sm, f"Puntuacion final: {self.score}", (255, 244, 194), SCREEN_W // 2, 348)
        if int(self.menu_t * 2) % 2 == 0:
            draw_text_center(self.screen, self.font_sm, "ENTER para jugar de nuevo  |  ESC para salir", (255, 255, 210), SCREEN_W // 2, 426)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_world()
            self._draw_hud(self.screen)
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover()
        elif self.state == STATE_WIN:
            self.draw_win()
        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == STATE_PLAYING:
                    self.state = STATE_MENU
                else:
                    return False
            elif event.key == pygame.K_RETURN:
                if self.state == STATE_MENU:
                    self._reset_game()
                    self.state = STATE_PLAYING
                elif self.state in (STATE_GAMEOVER, STATE_WIN):
                    self._reset_game()
                    self.state = STATE_PLAYING
                elif self.state == STATE_PLAYING:
                    self._toggle_memory_mode()
            elif event.key == pygame.K_p and self.state == STATE_PLAYING:
                self._toggle_memory_mode()
            elif event.key in (pygame.K_UP, pygame.K_w) and self.state == STATE_PLAYING:
                self._change_lane(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s) and self.state == STATE_PLAYING:
                self._change_lane(1)
            elif event.key in (pygame.K_j, pygame.K_LCTRL, pygame.K_RCTRL) and self.state == STATE_PLAYING:
                self._shoot()
        return True

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    HavanaRide().run()