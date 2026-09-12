r"""Build SongManager\favicon.ico (16/24/32/48/64/128/256) and icon-256.png from the same
geometry as SongManager\icon.svg, using Pillow. Run:  py -3 scripts\make-icon.py

The pick outline is the SVG path's four cubic Beziers sampled into a polygon; the three
list lines are drawn as rounded strokes. Everything is drawn at 1024 px and downsampled,
so the small sizes stay smooth."""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "SongManager")

# same control points as icon.svg (64-unit box)
CURVES = [((32, 60), (24, 52), (6, 36), (6, 21)),
          ((6, 21), (6, 9), (17, 4), (32, 4)),
          ((32, 4), (47, 4), (58, 9), (58, 21)),
          ((58, 21), (58, 36), (40, 52), (32, 60))]
LINES = [((21, 21), (43, 21)), ((23, 30), (41, 30)), ((26, 39), (38, 39))]
TOP, BOTTOM = (0x3D, 0xBC, 0xFF), (0x0B, 0x6F, 0xA8)


def bezier(p0, p1, p2, p3, n=48):
    for i in range(n):
        t = i / n
        u = 1 - t
        yield (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
               u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def render(size):
    S = size / 64
    mask = Image.new("L", (size, size), 0)
    poly = [(x * S, y * S) for c in CURVES for (x, y) in bezier(*c)]
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    # vertical gradient clipped to the pick
    grad = Image.new("RGBA", (size, size))
    gp = grad.load()
    for y in range(size):
        t = y / (size - 1)
        col = tuple(round(TOP[k] + (BOTTOM[k] - TOP[k]) * t) for k in range(3)) + (255,)
        for x in range(size):
            gp[x, y] = col
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    w = 4 * S
    for (x1, y1), (x2, y2) in LINES:
        d.line([(x1 * S, y1 * S), (x2 * S, y2 * S)], fill=(255, 255, 255, 255), width=round(w))
        for (x, y) in ((x1, y1), (x2, y2)):
            d.ellipse([x * S - w / 2, y * S - w / 2, x * S + w / 2, y * S + w / 2], fill=(255, 255, 255, 255))
    return img


big = render(1024)
sizes = [256, 128, 64, 48, 32, 24, 16]
frames = [big.resize((s, s), Image.LANCZOS) for s in sizes]
ico = os.path.join(OUT, "favicon.ico")
frames[0].save(ico, format="ICO", sizes=[(s, s) for s in sizes], append_images=frames[1:])
frames[0].save(os.path.join(OUT, "icon-256.png"))
print("wrote", os.path.relpath(ico), "with sizes", sizes, "and icon-256.png")
