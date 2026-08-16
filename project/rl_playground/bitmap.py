"""Tiny 5x7 bitmap font so we never need pygame.font (broken on some Python 3.14 wheels)."""

from __future__ import annotations

import pygame

# Each glyph is 5 columns of 7 bits (bit 0 = top). Space is empty.
_GLYPHS: dict[str, tuple[int, int, int, int, int]] = {}


def _g(*cols: int) -> tuple[int, int, int, int, int]:
    return (cols[0], cols[1], cols[2], cols[3], cols[4])


def _build() -> None:
    d = {
        " ": _g(0, 0, 0, 0, 0),
        "!": _g(0, 0, 95, 0, 0),
        "#": _g(20, 62, 20, 62, 20),
        "%": _g(70, 73, 22, 37, 81),
        "(": _g(0, 28, 34, 65, 0),
        ")": _g(0, 65, 34, 28, 0),
        "+": _g(8, 8, 62, 8, 8),
        "-": _g(8, 8, 8, 8, 8),
        ".": _g(0, 0, 64, 0, 0),
        "/": _g(64, 32, 16, 8, 4),
        "0": _g(62, 81, 73, 69, 62),
        "1": _g(0, 66, 127, 64, 0),
        "2": _g(98, 81, 73, 73, 70),
        "3": _g(34, 65, 73, 73, 54),
        "4": _g(24, 20, 18, 127, 16),
        "5": _g(39, 69, 69, 69, 57),
        "6": _g(62, 73, 73, 73, 48),
        "7": _g(1, 113, 9, 5, 3),
        "8": _g(54, 73, 73, 73, 54),
        "9": _g(6, 73, 73, 73, 62),
        ":": _g(0, 0, 36, 0, 0),
        "<": _g(8, 20, 34, 65, 0),
        "=": _g(20, 20, 20, 20, 20),
        ">": _g(0, 65, 34, 20, 8),
        "?": _g(2, 1, 81, 9, 6),
        "A": _g(126, 17, 17, 17, 126),
        "B": _g(127, 73, 73, 73, 54),
        "C": _g(62, 65, 65, 65, 34),
        "D": _g(127, 65, 65, 34, 28),
        "E": _g(127, 73, 73, 73, 65),
        "F": _g(127, 9, 9, 9, 1),
        "G": _g(62, 65, 73, 73, 122),
        "H": _g(127, 8, 8, 8, 127),
        "I": _g(0, 65, 127, 65, 0),
        "J": _g(32, 64, 65, 63, 1),
        "K": _g(127, 8, 20, 34, 65),
        "L": _g(127, 64, 64, 64, 64),
        "M": _g(127, 2, 12, 2, 127),
        "N": _g(127, 4, 8, 16, 127),
        "O": _g(62, 65, 65, 65, 62),
        "P": _g(127, 9, 9, 9, 6),
        "Q": _g(62, 65, 81, 33, 94),
        "R": _g(127, 9, 25, 41, 70),
        "S": _g(38, 73, 73, 73, 50),
        "T": _g(1, 1, 127, 1, 1),
        "U": _g(63, 64, 64, 64, 63),
        "V": _g(31, 32, 64, 32, 31),
        "W": _g(127, 32, 24, 32, 127),
        "X": _g(99, 20, 8, 20, 99),
        "Y": _g(7, 8, 112, 8, 7),
        "Z": _g(97, 81, 73, 69, 67),
        "_": _g(64, 64, 64, 64, 64),
    }
    extra = {
        "a": d["A"],
        "b": d["B"],
        "c": d["C"],
        "d": d["D"],
        "e": d["E"],
        "f": d["F"],
        "g": d["G"],
        "h": d["H"],
        "i": d["I"],
        "j": d["J"],
        "k": d["K"],
        "l": d["L"],
        "m": d["M"],
        "n": d["N"],
        "o": d["O"],
        "p": d["P"],
        "q": d["Q"],
        "r": d["R"],
        "s": d["S"],
        "t": d["T"],
        "u": d["U"],
        "v": d["V"],
        "w": d["W"],
        "x": d["X"],
        "y": d["Y"],
        "z": d["Z"],
    }
    _GLYPHS.update(d)
    _GLYPHS.update(extra)


_build()


class BitmapFont:
    """Drop-in for the pygame Font bits we use: .render(text, antialias, color)."""

    def __init__(self, scale: int = 2):
        self.scale = scale

    def render(self, text: str, _aa: bool, color: tuple[int, int, int]) -> pygame.Surface:
        scale = self.scale
        w = max(1, len(text) * (5 * scale + scale))
        h = 7 * scale
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        x = 0
        for ch in text:
            cols = _GLYPHS.get(ch, _GLYPHS["?"])
            for cx, bits in enumerate(cols):
                for row in range(7):
                    if bits & (1 << row):
                        pygame.draw.rect(
                            surf,
                            color,
                            (x + cx * scale, row * scale, scale, scale),
                        )
            x += 5 * scale + scale
        return surf


FONT = BitmapFont(2)
SMALL = BitmapFont(1)
