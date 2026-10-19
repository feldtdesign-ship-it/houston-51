"""prep_screens.py: still frames for the 15 screens in the Cycles renders, cut from PJ's ORIGINAL clips (not the shrunk web copies), cropped like object-fit: cover.
Writes build/screens/<MON_SCR name>.jpg.  Run: python3 build/prep_screens.py"""
import os, subprocess
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'screens'); os.makedirs(OUT, exist_ok=True)
PJ = os.path.expanduser("~/Documents/2026/PJ O'Rourke"); RAW = os.path.join(OUT, '_raw'); os.makedirs(RAW, exist_ok=True)
CL = {'hornets': (PJ + '/Animation/Murder Hornets Loop.mp4', 3.0), 'fatgumbit': (PJ + '/Fat Gumbit/Fat_Gumbit_turnaround_0001-0150.mp4', 1.2),
      'pizzarat': (PJ + '/Fat Gumbit/Pizza_Rat_red_turnaround_0001-0150.mp4', 2.2), 'breakdance': (PJ + '/Fat Gumbit/suit_guy/SuitGuy_breakdance_loop.mp4', 4.6),
      'headspin': (PJ + '/Fat Gumbit/suit_guy/SuitGuy_headspin_ink_0001-0350.mp4', 5.0), 'suitpink': (PJ + '/Fat Gumbit/suit_guy/suit_guy_4view_pink_loop_0001-0150.mp4', 1.8),
      'ontheblock': (PJ + '/Fat Gumbit/suit_guy/SuitGuy_on_the_block.mp4', 5.5), 'nyloop': (PJ + '/Animation/Fuckery_1080_loop/newyorkfuckery_1080_loop.mp4', 2.0)}
for k, (p, t) in CL.items():
    dst = os.path.join(RAW, k + '.jpg')
    if not os.path.exists(dst): subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', p, '-frames:v', '1', '-q:v', '2', dst])
def cover(im, asp):
    w, h = im.size
    if w / h > asp: nw = int(h * asp); x = (w - nw) // 2; return im.crop((x, 0, x + nw, h))
    nh = int(w / asp); y = (h - nh) // 2; return im.crop((0, y, w, y + nh))
ART = os.path.join(os.path.dirname(HERE), 'assets', 'art')
PA, LA = 1.75 / 3.1, 3.1 / 1.75
from PIL import ImageOps, ImageEnhance, ImageStat
TINTS = {'B': (255, 176, 118), 'H': (140, 232, 236), 'W': (255, 150, 90)}
def save(name, im):
    im = im.convert('RGB'); hsv = im.convert('HSV'); sat = ImageStat.Stat(hsv).mean[1] / 255
    if sat < 0.06:      # line art on white: flip to light lines on a dark ground and tint it, so the screens glow in a dark room
        g = ImageOps.autocontrast(im.convert('L'), cutoff=1).point(lambda v: 255 if v > 214 else v); g = ImageOps.invert(g); im = ImageOps.colorize(g, black=(5, 7, 13), white=TINTS.get(name[8], (255, 200, 150)))
    else:
        im = ImageEnhance.Brightness(im).enhance(0.92)
    im.save(os.path.join(OUT, name + '.jpg'), quality=92); print(name, 'night' if sat < 0.06 else 'colour', round(sat, 2))
save('MON_SCR_W1', cover(Image.open(os.path.join(ART, 'gumbit_citibike.jpg')), PA)); save('MON_SCR_W3', cover(Image.open(os.path.join(ART, 'gumbit_bubbles.jpg')), PA))
save('MON_SCR_W2', cover(Image.open(os.path.join(RAW, 'breakdance.jpg')), PA))
WA = (3 * 3.1 + 2 * .05) / (2 * 1.75 + .05); big = cover(Image.open(os.path.join(RAW, 'ontheblock.jpg')), WA); W, H = big.size
for i in range(6):
    r, c = divmod(i, 3); save('MON_SCR_B%d' % (i + 1), big.crop((c * W // 3, r * H // 2, (c + 1) * W // 3, (r + 1) * H // 2)))
for n, k in (('H1a', 'fatgumbit'), ('H1b', 'pizzarat'), ('H2a', 'headspin'), ('H2b', 'nyloop'), ('H3a', 'hornets'), ('H3b', 'suitpink')): save('MON_SCR_' + n, cover(Image.open(os.path.join(RAW, k + '.jpg')), LA))
print(sorted(os.listdir(OUT)))
