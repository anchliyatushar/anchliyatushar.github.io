from pathlib import Path
from textwrap import wrap

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/Disha-Jain-Jewellery-CAD-Portfolio.pdf"
PUBLIC_COPY = ROOT / "public/disha-jain-jewellery-cad-portfolio.pdf"
CACHE_DIR = ROOT / "tmp/pdfs/portfolio-images"

W, H = A4
MARGIN = 40

BG = HexColor("#070908")
SURFACE = HexColor("#0D100F")
TEXT = HexColor("#EFECE2")
MUTED = HexColor("#9C9D94")
GOLD = HexColor("#D8B251")
GOLD_BRIGHT = HexColor("#F0D47B")
BLUE = HexColor("#B8E6F5")
LINE = HexColor("#2A302C")


def register_fonts():
    pdfmetrics.registerFont(TTFont("PortfolioSerif", "/System/Library/Fonts/Supplemental/Georgia.ttf"))
    pdfmetrics.registerFont(TTFont("PortfolioSerifItalic", "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"))


def set_fill(canvas_obj, color):
    canvas_obj.setFillColor(color)


def draw_rule(canvas_obj, y, x=MARGIN, width=W - MARGIN * 2, color=LINE):
    canvas_obj.setStrokeColor(color)
    canvas_obj.setLineWidth(0.6)
    canvas_obj.line(x, y, x + width, y)


def draw_label(canvas_obj, text, x, y, color=BLUE):
    set_fill(canvas_obj, color)
    canvas_obj.setFont("Helvetica-Bold", 7.4)
    canvas_obj.drawString(x, y, text.upper())


def draw_wrapped(canvas_obj, text, x, y, width, font="Helvetica", size=10, leading=14, color=MUTED):
    set_fill(canvas_obj, color)
    canvas_obj.setFont(font, size)
    max_chars = max(18, int(width / (size * 0.52)))
    lines = []
    for paragraph in text.split("\n"):
        lines.extend(wrap(paragraph, width=max_chars) or [""])
    text_obj = canvas_obj.beginText(x, y)
    text_obj.setFont(font, size)
    text_obj.setLeading(leading)
    text_obj.setFillColor(color)
    for line in lines:
        text_obj.textLine(line)
    canvas_obj.drawText(text_obj)
    return y - leading * len(lines)


def image_cover(canvas_obj, path, x, y, width, height, focus_x=0.5, focus_y=0.5):
    source = ImageReader(str(prepare_image(path)))
    image_width, image_height = source.getSize()
    scale = max(width / image_width, height / image_height)
    scaled_width = image_width * scale
    scaled_height = image_height * scale
    draw_x = x - (scaled_width - width) * focus_x
    draw_y = y - (scaled_height - height) * focus_y
    canvas_obj.saveState()
    clip = canvas_obj.beginPath()
    clip.rect(x, y, width, height)
    canvas_obj.clipPath(clip, stroke=0, fill=0)
    canvas_obj.drawImage(source, draw_x, draw_y, width=scaled_width, height=scaled_height, mask="auto")
    canvas_obj.restoreState()


def prepare_image(path):
    path = Path(path)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    output = CACHE_DIR / f"{path.stem}.jpg"
    if not output.exists() or output.stat().st_mtime < path.stat().st_mtime:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((1200, 1800), Image.Resampling.LANCZOS)
            image.save(output, "JPEG", quality=86, optimize=True, progressive=True)
    return output


def page_background(canvas_obj, number):
    canvas_obj.setFillColor(BG)
    canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)
    canvas_obj.setStrokeColor(LINE)
    canvas_obj.setLineWidth(0.45)
    canvas_obj.line(MARGIN, H - 28, W - MARGIN, H - 28)
    set_fill(canvas_obj, MUTED)
    canvas_obj.setFont("Helvetica", 7.4)
    canvas_obj.drawRightString(W - MARGIN, 16, f"DISHA JAIN / {number:02d}")
    canvas_obj.drawString(MARGIN, 16, "JEWELLERY CAD PORTFOLIO")


def draw_cover(canvas_obj):
    canvas_obj.setFillColor(BG)
    canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)
    image_path = ROOT / "src/assets/editorial/final/final-panther-bloom-male-natural-scale.png"
    image_cover(canvas_obj, image_path, W * 0.55, 0, W * 0.45, H, focus_x=0.52, focus_y=0.45)
    canvas_obj.setFillColor(BG)
    canvas_obj.rect(0, 0, W * 0.62, H, fill=1, stroke=0)
    canvas_obj.setFillColor(SURFACE)
    canvas_obj.rect(0, 0, 6, H, fill=1, stroke=0)
    draw_label(canvas_obj, "Jewellery CAD / Selected Work", MARGIN, H - 90)
    set_fill(canvas_obj, TEXT)
    canvas_obj.setFont("Helvetica-Bold", 35)
    canvas_obj.drawString(MARGIN, H - 160, "Disha Jain")
    canvas_obj.setFont("PortfolioSerifItalic", 32)
    canvas_obj.drawString(MARGIN, H - 205, "Creative intent.")
    canvas_obj.drawString(MARGIN, H - 244, "Production precision.")
    draw_wrapped(
        canvas_obj,
        "Selected jewellery CAD projects, from concept and stone plan to considered 3D geometry and final visualisation.",
        MARGIN,
        H - 308,
        255,
        size=11,
        leading=16,
    )
    draw_rule(canvas_obj, 112, width=255)
    set_fill(canvas_obj, TEXT)
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawString(MARGIN, 82, "Disha Jain")
    set_fill(canvas_obj, MUTED)
    canvas_obj.setFont("Helvetica", 8.5)
    canvas_obj.drawString(MARGIN, 62, "Jewellery CAD designer / Bangalore, India")
    canvas_obj.drawString(MARGIN, 45, "solankidisha123@gmail.com / +91 70204 60962")
    canvas_obj.showPage()


def draw_practice_page(canvas_obj):
    page_background(canvas_obj, 2)
    draw_label(canvas_obj, "Practice / 01-04", MARGIN, H - 74)
    set_fill(canvas_obj, TEXT)
    canvas_obj.setFont("Helvetica-Bold", 30)
    canvas_obj.drawString(MARGIN, H - 126, "From brief to")
    canvas_obj.setFont("PortfolioSerifItalic", 31)
    canvas_obj.drawString(MARGIN, H - 164, "build-ready.")
    draw_wrapped(
        canvas_obj,
        "Disha Jain is a jewellery CAD designer, educator and technical consultant. Her process turns sketches and specifications into precise jewellery models made with manufacture in mind.",
        MARGIN,
        H - 218,
        328,
        size=11,
        leading=16,
    )
    steps = [
        ("01", "Interpret", "Sketches, stone plans and references become a clear CAD brief."),
        ("02", "Model", "Rhino, Matrix 9 and MatrixGold turn the concept into accurate 3D geometry."),
        ("03", "Refine", "Proportion, settings, wall thickness and joins are resolved for wearability and manufacture."),
        ("04", "Visualise", "Worn and close-detail imagery makes scale, material and craft easy to judge."),
    ]
    top = H - 338
    row_height = 87
    for index, (number, title, body) in enumerate(steps):
        y = top - index * row_height
        canvas_obj.setFillColor(SURFACE if index % 2 else BG)
        canvas_obj.rect(MARGIN, y - row_height + 7, W - MARGIN * 2, row_height - 7, fill=1, stroke=0)
        draw_rule(canvas_obj, y, width=W - MARGIN * 2)
        draw_label(canvas_obj, number, MARGIN + 10, y - 23, GOLD)
        set_fill(canvas_obj, TEXT)
        canvas_obj.setFont("Helvetica-Bold", 15)
        canvas_obj.drawString(MARGIN + 65, y - 23, title)
        draw_wrapped(canvas_obj, body, MARGIN + 65, y - 44, 385, size=9.5, leading=13)
    draw_rule(canvas_obj, top - 4 * row_height + 7, width=W - MARGIN * 2)
    draw_label(canvas_obj, "Tools", MARGIN, 96, GOLD)
    set_fill(canvas_obj, TEXT)
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.drawString(MARGIN, 72, "Rhino 3D / Matrix 9 / MatrixGold / Jewellery visualisation / 3D printing")
    canvas_obj.showPage()


PROJECTS = [
    {
        "number": "01",
        "title": "Emerald Stone Choker",
        "type": "NECKLACE / 2026",
        "summary": "A close-fitting gold choker in graduated emerald-green stones, arranged in a balanced collar line.",
        "metal": "Gold",
        "stones": "Emerald-green rectangular stones",
        "hero": "src/assets/editorial/final/final-stone-choker-worn.png",
        "detail": "src/assets/editorial/final/final-stone-choker-detail.png",
        "focus": (0.5, 0.46),
    },
    {
        "number": "02",
        "title": "Panther Bloom Brooch",
        "type": "STATEMENT BROOCH / 2026",
        "summary": "A sculptural statement brooch combining a panther head, botanical forms and blue stone accents.",
        "metal": "Gold",
        "stones": "Blue and pale-blue stones",
        "hero": "src/assets/editorial/final/final-panther-bloom-male-natural-scale.png",
        "detail": "src/assets/editorial/final/final-panther-bloom-male-detail.png",
        "focus": (0.5, 0.48),
    },
    {
        "number": "03",
        "title": "Sculptural Serpent Kada",
        "type": "MEN'S OPEN KADA / 2026",
        "summary": "A twin-serpent gold kada with a fluid curve and concentrated red-eye details.",
        "metal": "Gold",
        "stones": "Red accent stones",
        "hero": "src/assets/editorial/final/final-serpent-bangle-mens-wrist.png",
        "detail": "src/assets/editorial/final/final-serpent-bangle-mens-detail-extreme-macro-left.png",
        "focus": (0.5, 0.5),
    },
    {
        "number": "04",
        "title": "Rose Petal Bridal Suite",
        "type": "BRIDAL NECKLACE / 2026",
        "summary": "A yellow-gold bridal necklace with blush-pink morganite petals and white-diamond accents.",
        "metal": "Yellow gold",
        "stones": "Blush-pink morganite and white diamonds",
        "hero": "src/assets/editorial/final/final-rose-petal-suite-model-retouched-detail.png",
        "detail": "src/assets/editorial/final/final-rose-petal-suite-jewellery-box-detail.png",
        "focus": (0.5, 0.38),
    },
    {
        "number": "05",
        "title": "Ruby Halo Ring",
        "type": "RING / 2026",
        "summary": "A ruby centre-stone ring framed by a white-diamond halo and a refined split-shoulder band.",
        "metal": "Gold",
        "stones": "Ruby centre stone with white diamond halo accents",
        "hero": "src/assets/editorial/final/final-ruby-halo-ring-worn.png",
        "detail": "src/assets/editorial/final/final-ruby-halo-ring-detail-ruby.png",
        "focus": (0.5, 0.54),
    },
    {
        "number": "06",
        "title": "Emerald Tip Bracelet",
        "type": "OPEN BRACELET / 2026",
        "summary": "A rose-gold open bracelet defined by a beaded line and emerald-green end stones.",
        "metal": "Rose gold",
        "stones": "Emerald-green accent stones",
        "hero": "src/assets/editorial/final/final-emerald-tip-bracelet-worn.png",
        "detail": "src/assets/editorial/final/final-emerald-tip-bracelet-detail.png",
        "focus": (0.5, 0.5),
    },
]


def draw_project_page(canvas_obj, project, page_number):
    page_background(canvas_obj, page_number)
    draw_label(canvas_obj, f"Featured project / {project['number']} of 06", MARGIN, H - 74)
    set_fill(canvas_obj, TEXT)
    canvas_obj.setFont("Helvetica-Bold", 25)
    canvas_obj.drawString(MARGIN, H - 116, project["title"])
    draw_label(canvas_obj, project["type"], MARGIN, H - 139, GOLD)
    large_x, large_y, large_w, large_h = MARGIN, 151, 288, 486
    small_x, small_y, small_w, small_h = 350, 421, 205, 216
    image_cover(canvas_obj, ROOT / project["hero"], large_x, large_y, large_w, large_h, *project["focus"])
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(0.6)
    canvas_obj.rect(large_x, large_y, large_w, large_h, fill=0, stroke=1)
    image_cover(canvas_obj, ROOT / project["detail"], small_x, small_y, small_w, small_h, 0.5, 0.5)
    canvas_obj.setStrokeColor(LINE)
    canvas_obj.rect(small_x, small_y, small_w, small_h, fill=0, stroke=1)
    draw_label(canvas_obj, "Close detail", small_x, small_y - 17, GOLD)
    text_x = small_x
    set_fill(canvas_obj, TEXT)
    canvas_obj.setFont("PortfolioSerifItalic", 17)
    canvas_obj.drawString(text_x, 357, "Design intent")
    draw_wrapped(canvas_obj, project["summary"], text_x, 331, small_w, size=9.6, leading=13.5)
    draw_rule(canvas_obj, 269, x=text_x, width=small_w)
    draw_label(canvas_obj, "Material", text_x, 248, GOLD)
    set_fill(canvas_obj, TEXT)
    canvas_obj.setFont("Helvetica-Bold", 10.5)
    canvas_obj.drawString(text_x, 228, project["metal"])
    draw_label(canvas_obj, "Stone detail", text_x, 194, GOLD)
    draw_wrapped(canvas_obj, project["stones"], text_x, 174, small_w, size=9.5, leading=13)
    canvas_obj.showPage()


def create_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_COPY.parent.mkdir(parents=True, exist_ok=True)
    register_fonts()
    pdf = canvas.Canvas(str(OUTPUT), pagesize=A4, pageCompression=1, title="Disha Jain - Jewellery CAD Portfolio")
    pdf.setTitle("Disha Jain - Jewellery CAD Portfolio")
    pdf.setAuthor("Disha Jain")
    pdf.setSubject("Selected jewellery CAD portfolio")
    pdf.setCreator("Disha Jain portfolio")
    draw_cover(pdf)
    draw_practice_page(pdf)
    for offset, project in enumerate(PROJECTS, start=3):
        draw_project_page(pdf, project, offset)
    pdf.save()
    PUBLIC_COPY.write_bytes(OUTPUT.read_bytes())
    print(OUTPUT)
    print(PUBLIC_COPY)


if __name__ == "__main__":
    create_pdf()
