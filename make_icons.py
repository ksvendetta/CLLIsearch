#!/usr/bin/env python3
"""Generate the app icons: a realistic magnifying glass with "CLLI" inside the
lens, the text spherically magnified (fish-eye bulge) like a real convex lens.

Pillow + numpy + scipy. Draws at high resolution then downsamples, and exports
the PNG sizes iOS (apple-touch-icon) and Android (manifest) need plus a favicon.

Usage:
    python make_icons.py
"""
import math
import numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image, ImageDraw, ImageFilter, ImageFont

M = 1024
CX, CY = 462, 442          # lens centre
RG = 352                   # glass radius
RO = 412                   # rim outer radius
BULGE = 0.55               # lens centre magnification = 1 / BULGE
TEXT_W = 1.5 * RG          # rendered width of "CLLI" before distortion

BG_TL = (15, 118, 110)   # teal-700 (background, top-left)
BG_BR = (3, 105, 161)    # blue-700 (background, bottom-right)
TEXT_COL = (12, 74, 110, 255)    # sky-900 — coloured text on the glass
GLASS_TOP = (224, 242, 254)      # light cyan glass (top)
GLASS_BOT = (165, 222, 247)      # light cyan glass (bottom)

FONTS = [r"C:\Windows\Fonts\ariblk.ttf", r"C:\Windows\Fonts\seguibl.ttf",
         r"C:\Windows\Fonts\arialbd.ttf"]


def load_font(size):
    for p in FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def vgrad(top, bot):
    """Vertical RGB gradient as an (M, M, 3) uint8 array."""
    t = np.linspace(0, 1, M).reshape(M, 1)
    out = np.zeros((M, M, 3), np.float32)
    for i in range(3):
        out[..., i] = top[i] * (1 - t) + bot[i] * t
    return out.astype(np.uint8)


def dgrad(c1, c2):
    """Diagonal RGB gradient (top-left c1 -> bottom-right c2)."""
    yy, xx = np.mgrid[0:M, 0:M].astype(np.float32)
    t = (xx + yy) / (2 * (M - 1))
    out = np.zeros((M, M, 3), np.float32)
    for i in range(3):
        out[..., i] = c1[i] * (1 - t) + c2[i] * t
    return out.astype(np.uint8)


def chrome_gradient():
    """Banded silver gradient (top-light, dark middle, light bottom)."""
    stops_t = [0.0, 0.30, 0.50, 0.72, 1.0]
    stops_c = [(240, 243, 247), (171, 181, 192), (104, 113, 124),
               (151, 160, 171), (210, 216, 223)]
    t = np.linspace(0, 1, M)
    out = np.zeros((M, M, 3), np.uint8)
    for i in range(3):
        col = np.interp(t, stops_t, [c[i] for c in stops_c])
        out[..., i] = np.repeat(col.reshape(M, 1), M, axis=1).astype(np.uint8)
    return out


def circle_mask(cx, cy, r):
    m = Image.new("L", (M, M), 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    return m


def text_layer():
    probe = ImageDraw.Draw(Image.new("RGBA", (M, M)))
    size = 320
    font = load_font(size)
    bb = probe.textbbox((0, 0), "CLLI", font=font)
    size = int(size * TEXT_W / (bb[2] - bb[0]))
    font = load_font(size)
    bb = probe.textbbox((0, 0), "CLLI", font=font)
    layer = Image.new("RGBA", (M, M), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(
        (CX - (bb[2] - bb[0]) / 2 - bb[0], CY - (bb[3] - bb[1]) / 2 - bb[1]),
        "CLLI", font=font, fill=TEXT_COL)
    return layer


def fisheye(layer):
    """Spherically magnify `layer` about the lens centre (convex-lens bulge)."""
    arr = np.asarray(layer).astype(np.float32)
    ys, xs = np.mgrid[0:M, 0:M].astype(np.float32)
    u, v = (xs - CX) / RG, (ys - CY) / RG
    rd = np.sqrt(u * u + v * v)
    rd_safe = np.where(rd < 1e-6, 1e-6, rd)
    rs = rd * (BULGE + (1 - BULGE) * rd)          # source radius for dest radius
    scale = np.where(rd <= 1.0, rs / rd_safe, 1.0)
    coords = np.array([CY + v * scale * RG, CX + u * scale * RG])
    out = np.zeros_like(arr)
    for c in range(4):
        out[..., c] = map_coordinates(arr[..., c], coords, order=1, mode="constant")
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def build_master():
    base = Image.fromarray(
        np.dstack([dgrad(BG_TL, BG_BR), np.full((M, M), 255, np.uint8)]), "RGBA")

    # Soft drop shadow under the whole magnifier.
    shadow = Image.new("RGBA", (M, M), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(
        [CX - RO + 16, CY - RO + 26, CX + RO + 16, CY + RO + 26], fill=(0, 0, 0, 130))
    base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(30)))

    # Wood handle (drawn before the rim so it tucks underneath).
    a = math.radians(48)
    x1, y1 = CX + (RO - 8) * math.cos(a), CY + (RO - 8) * math.sin(a)
    x2, y2 = CX + (RO + 250) * math.cos(a), CY + (RO + 250) * math.sin(a)
    hd = ImageDraw.Draw(base)
    hd.line([(x1, y1), (x2, y2)], fill=(150, 98, 51, 255), width=104)
    hd.ellipse([x2 - 52, y2 - 52, x2 + 52, y2 + 52], fill=(150, 98, 51, 255))
    # handle highlight stripe + dark edge
    ox, oy = -22 * math.sin(a), 22 * math.cos(a)
    hd.line([(x1 + ox, y1 + oy), (x2 + ox, y2 + oy)], fill=(196, 138, 79, 255), width=30)
    hd.line([(x1 - 1.6 * ox, y1 - 1.6 * oy), (x2 - 1.6 * ox, y2 - 1.6 * oy)],
            fill=(110, 68, 35, 255), width=18)

    # Lens contents: light glass + fish-eye text + glossy highlight, clipped.
    gmask = circle_mask(CX, CY, RG)
    glass = Image.fromarray(
        np.dstack([vgrad(GLASS_TOP, GLASS_BOT), np.full((M, M), 255, np.uint8)]), "RGBA")
    glass = Image.alpha_composite(glass, fisheye(text_layer()))
    shine = Image.new("RGBA", (M, M), (0, 0, 0, 0))
    ImageDraw.Draw(shine).ellipse(
        [CX - 0.8 * RG, CY - 0.95 * RG, CX + 0.35 * RG, CY - 0.1 * RG],
        fill=(255, 255, 255, 80))
    glass = Image.alpha_composite(glass, shine.filter(ImageFilter.GaussianBlur(34)))
    base = Image.composite(glass, base, gmask)

    # Chrome rim (annulus) + thin bright inner/outer edge lines.
    ring = Image.new("L", (M, M), 0)
    rd = ImageDraw.Draw(ring)
    rd.ellipse([CX - RO, CY - RO, CX + RO, CY + RO], fill=255)
    rd.ellipse([CX - RG, CY - RG, CX + RG, CY + RG], fill=0)
    chrome = Image.fromarray(
        np.dstack([chrome_gradient(), np.full((M, M), 255, np.uint8)]), "RGBA")
    base = Image.composite(chrome, base, ring)
    ed = ImageDraw.Draw(base)
    ed.ellipse([CX - RO, CY - RO, CX + RO, CY + RO], outline=(247, 250, 252, 230), width=5)
    ed.ellipse([CX - RG, CY - RG, CX + RG, CY + RG], outline=(40, 48, 58, 230), width=6)

    return base.convert("RGB")


def main():
    master = build_master()
    for size, name in [(180, "apple-touch-icon.png"), (192, "icon-192.png"),
                       (512, "icon-512.png"), (32, "favicon-32.png")]:
        master.resize((size, size), Image.LANCZOS).save(name)
        print(f"wrote {name} ({size}x{size})")


if __name__ == "__main__":
    main()
