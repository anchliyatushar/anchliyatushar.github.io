from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SOURCE = ROOT / "src/assets/editorial/final/final-stone-choker-worn.png"
BRAND_SOURCE = ROOT / "src/assets/brand/dj-linework-options/dj-linework-03-diamond-clean.png"

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


def extract_linework(image):
    """Convert the approved black-backed PNG into an anti-aliased transparent mark."""
    linework = image.convert("RGBA")
    luminance = image.convert("L")
    alpha = luminance.point(lambda value: 0 if value < 8 else min(255, (value - 8) * 4))
    linework.putalpha(alpha)
    return linework


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


def make_brand_assets():
    """Export the approved linework mark for the site and device icons."""
    with Image.open(BRAND_SOURCE) as source:
        logo = extract_linework(ImageOps.exif_transpose(source))

    # Keep the approved source as a true transparent, browser-ready PNG.
    logo.save(PUBLIC / "disha-jain-logo.png", optimize=True)

    # A square crop preserves the full DJ monogram at a legible size in the header.
    mark = logo.crop((140, 120, 900, 880))
    mark_canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    mark_canvas.alpha_composite(ImageOps.contain(mark, (440, 440), Image.Resampling.LANCZOS), (36, 36))
    mark_canvas.save(PUBLIC / "brand-mark.png", optimize=True)

    # Installed app icons use the same logo on a deliberate dark ground.
    apple_icon = Image.new("RGB", (512, 512), BG)
    apple_icon.paste(mark_canvas, mask=mark_canvas.getchannel("A"))
    apple_icon.save(PUBLIC / "apple-touch-icon.png", optimize=True)

    # Browser tabs need a distilled version of the logo: its central princess-cut diamond.
    # The full linework mark is too fine to remain legible at 16px.
    tab_icon = Image.new("RGB", (512, 512), BG)
    tab_draw = ImageDraw.Draw(tab_icon)
    tab_draw.polygon([(256, 56), (456, 256), (256, 456), (56, 256)], fill=GOLD)
    tab_draw.polygon([(256, 132), (380, 256), (256, 380), (132, 256)], fill=BG)
    tab_draw.line((256, 56, 256, 456), fill=GOLD_BRIGHT, width=12)
    tab_draw.line((56, 256, 456, 256), fill=GOLD_BRIGHT, width=12)
    tab_icon.save(PUBLIC / "favicon.png", optimize=True)
    tab_icon.save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == "__main__":
    make_social_card()
    make_brand_assets()
    print(PUBLIC / "og-default.jpg")
    print(PUBLIC / "disha-jain-logo.png")
    print(PUBLIC / "brand-mark.png")
    print(PUBLIC / "favicon.png")
    print(PUBLIC / "apple-touch-icon.png")
    print(PUBLIC / "favicon.ico")
