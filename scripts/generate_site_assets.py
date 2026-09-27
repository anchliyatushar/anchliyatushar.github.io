from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SOURCE = ROOT / "src/assets/editorial/final/final-stone-choker-worn.png"

BG = "#070908"
TEXT = "#EFECE2"
MUTED = "#A9AAA1"
GOLD = "#D8B251"
GOLD_BRIGHT = "#F0D47B"
BLUE = "#B8E6F5"

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_SERIF_ITALIC = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def crop_cover(image, size, focus=(0.5, 0.34)):
    width, height = size
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = round((resized.width - width) * focus[0])
    top = round((resized.height - height) * focus[1])
    return resized.crop((left, top, left + width, top + height))


def make_social_card():
    canvas = Image.new("RGB", (1200, 630), BG)
    with Image.open(SOURCE) as source:
        photo = crop_cover(ImageOps.exif_transpose(source).convert("RGB"), (600, 630))
    canvas.paste(photo, (600, 0))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for x in range(440, 830):
        alpha = int(255 * (1 - (x - 440) / 390))
        overlay_draw.line((x, 0, x, 630), fill=(7, 9, 8, max(0, alpha)), width=1)
    overlay_draw.rectangle((0, 0, 600, 630), fill=(7, 9, 8, 255))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas)

    draw.line((72, 67, 1128, 67), fill="#303630", width=1)
    draw.text((72, 98), "JEWELLERY CAD / SELECTED WORK", font=font(FONT_BOLD, 17), fill=BLUE)
    draw.text((72, 186), "Disha Jain", font=font(FONT_BOLD, 66), fill=TEXT)
    draw.text((72, 270), "Creative intent.", font=font(FONT_SERIF_ITALIC, 53), fill=TEXT)
    draw.text((72, 334), "Production precision.", font=font(FONT_SERIF_ITALIC, 53), fill=TEXT)
    draw.line((72, 438, 422, 438), fill=GOLD, width=2)
    draw.text((72, 468), "Jewellery CAD portfolio", font=font(FONT_BOLD, 22), fill=TEXT)
    draw.text((72, 507), "Rhino 3D / Matrix 9 / MatrixGold", font=font(FONT_REGULAR, 18), fill=MUTED)
    draw.text((72, 561), "anchliyatushar.github.io", font=font(FONT_BOLD, 15), fill=GOLD_BRIGHT)
    draw.rectangle((0, 0, 1199, 629), outline="#2F352F", width=2)
    canvas.convert("RGB").save(PUBLIC / "og-default.jpg", quality=90, optimize=True, progressive=True)


def make_app_icon():
    icon = Image.new("RGB", (512, 512), BG)
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((8, 8, 504, 504), radius=112, fill=BG)
    # A deliberately simple DJ monogram retains its identity at 16px.
    draw.polygon(
        [(104, 112), (210, 112), (280, 148), (305, 207), (280, 266), (210, 302), (104, 302)],
        fill=GOLD,
    )
    draw.polygon(
        [(160, 166), (202, 166), (236, 187), (247, 207), (236, 227), (202, 248), (160, 248)],
        fill=BG,
    )
    draw.line((387, 124, 387, 324), fill=GOLD_BRIGHT, width=48)
    draw.arc((225, 252, 411, 431), start=0, end=160, fill=GOLD_BRIGHT, width=48)
    draw.polygon([(364, 69), (390, 95), (364, 121), (338, 95)], fill=BLUE)
    draw.line((364, 69, 390, 95, 364, 121, 338, 95, 364, 69), fill=GOLD_BRIGHT, width=9, joint="curve")
    icon.save(PUBLIC / "apple-touch-icon.png", optimize=True)
    icon.save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == "__main__":
    make_social_card()
    make_app_icon()
    print(PUBLIC / "og-default.jpg")
    print(PUBLIC / "apple-touch-icon.png")
    print(PUBLIC / "favicon.ico")
