"""Generator znaku wodnego dla zdjęć ogłoszeń.

Nakłada w prawym dolnym rogu kompaktowy poziomy pasek: mały kod QR oraz
adres ogłoszenia (upadlosciowe.pl + kod). Czysty Pillow + qrcode.
"""
import io

import qrcode
from PIL import Image, ImageDraw, ImageFont


MIN_SZEROKOSC = 400  # zdjęcia węższe pomijamy - watermark byłby nieczytelny

_SCIEZKI_FONTU = (
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',         # Linux / Docker
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'DejaVuSans.ttf',
    'arial.ttf',                                               # Windows (dev)
)


def _font(rozmiar, bold=False):
    sciezki = _SCIEZKI_FONTU
    if bold:
        sciezki = ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                   'arialbd.ttf') + _SCIEZKI_FONTU
    for sciezka in sciezki:
        try:
            return ImageFont.truetype(sciezka, rozmiar)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def generuj_watermark(image_file, short_url):
    """Zwraca BytesIO ze zwatermarkowanym JPEG, albo None gdy obraz za wąski."""
    image_file.seek(0)
    img = Image.open(image_file).convert('RGBA')

    if img.width < MIN_SZEROKOSC:
        return None

    czysty = short_url.replace('https://', '').replace('http://', '').rstrip('/')
    if '/' in czysty:
        domena, kod = czysty.rsplit('/', 1)
    else:
        domena, kod = czysty, ''

    qr_size = max(int(img.width * 0.075), 54)
    padding = max(int(qr_size * 0.16), 7)
    f_dom = _font(max(int(qr_size * 0.26), 11))
    f_kod = _font(max(int(qr_size * 0.40), 15), bold=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(short_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='white', back_color='transparent').convert('RGBA')
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    dom_box = tmp.textbbox((0, 0), domena, font=f_dom)
    kod_box = tmp.textbbox((0, 0), kod, font=f_kod)
    dom_w, dom_h = dom_box[2] - dom_box[0], dom_box[3] - dom_box[1]
    kod_w, kod_h = kod_box[2] - kod_box[0], kod_box[3] - kod_box[1]
    text_w = max(dom_w, kod_w)

    bar_h = qr_size + padding * 2
    bar_w = padding * 3 + qr_size + text_w

    overlay = Image.new('RGBA', (bar_w, bar_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        [0, 0, bar_w - 1, bar_h - 1],
        radius=max(int(bar_h * 0.14), 6),
        fill=(15, 23, 42, 165),
    )
    overlay.paste(qr_img, (padding, padding), qr_img)

    tekst_x = padding * 2 + qr_size
    odstep = max(int(qr_size * 0.10), 4)
    blok_h = dom_h + odstep + kod_h
    ty = (bar_h - blok_h) // 2
    draw.text((tekst_x, ty - dom_box[1]), domena, fill=(255, 255, 255, 235), font=f_dom)
    draw.text((tekst_x, ty + dom_h + odstep - kod_box[1]), kod, fill=(255, 255, 255, 255), font=f_kod)

    margin = max(int(img.width * 0.018), 10)
    img.paste(overlay, (img.width - bar_w - margin, img.height - bar_h - margin), overlay)

    rgb = Image.new('RGB', img.size, (255, 255, 255))
    rgb.paste(img, mask=img.split()[3])
    output = io.BytesIO()
    rgb.save(output, format='JPEG', quality=92)
    output.seek(0)
    return output
