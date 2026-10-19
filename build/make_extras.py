"""make_extras.py: the small files the page needs that are not the model.
  data/pins.json   neighbours the Meridian brochure names, geocoded from their street addresses (NYC Planning GeoSearch), local metres
  data/lines.json  street centrelines (local metres) for the animated people and cars
  assets/*         PJ's signature (white), his art stills for the monitors, the real photographs from the walk-through
Run: python3 build/make_extras.py
"""
import json, os, math, subprocess, urllib.parse, shutil
S = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(S); D = os.path.join(R, 'data'); A = os.path.join(R, 'assets')
HOME = os.path.expanduser('~/Documents/2026/PJ O\'Rourke')
SCR = '/private/tmp/claude-501/-Users-michaelweinfeld-Documents-2026-PJ-O-Rourke/76302e7d-214a-4600-a2aa-90be76c21cbd/scratchpad/in'
LAT, LON = 40.724565, -73.994625; C = math.cos(math.radians(LAT))
P = lambda lo, la: [round((lo - LON) * 111320 * C, 1), round((la - LAT) * 110540, 1)]
def geo(addr):
    u = 'https://geosearch.planninglabs.nyc/v2/search?size=1&text=' + urllib.parse.quote(addr + ', Manhattan')
    b = subprocess.run(['curl', '-s', '--max-time', '30', u], capture_output=True).stdout
    try: f = json.loads(b)['features'][0]; return f['geometry']['coordinates'], f['properties'].get('label')
    except Exception: return None, None
# addresses checked on the web 2026-10-19 (Milano's, Ballato, Musket Room, Le Labo) or well known (Prince Street Pizza, Rubirosa)
PLACES = [("Milano's Bar", '51 East Houston Street', 'same building'), ('Ballato', '55 East Houston Street', 'two doors east'),
          ('Prince Street Pizza', '27 Prince Street', ''), ('Rubirosa', '235 Mulberry Street', ''), ('The Musket Room', '265 Elizabeth Street', ''), ('Le Labo', '233 Elizabeth Street', '')]
pins = []
for n, a, note in PLACES:
    c, lab = geo(a)
    if not c: print('no geocode', n); continue
    xy = P(*c); d = math.hypot(*xy)
    if d > 420: print('too far, skipped', n, d); continue
    pins.append({'n': n, 'a': a, 'xy': xy, 'd': round(d), 'note': note}); print(n, lab, xy, round(d), 'm')
json.dump(pins, open(os.path.join(D, 'pins.json'), 'w'))
# centrelines
lines = []
for r in json.load(open(os.path.join(D, 'centerline.json'))):
    g = r.get('the_geom'); n = (r.get('stname_label') or '').strip()
    if not g: continue
    parts = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
    for ln in parts:
        pts = [P(a, b) for a, b in ln]
        if len(pts) >= 2: lines.append({'n': n, 'w': float(r.get('streetwidth') or 30), 'p': pts})
json.dump(lines, open(os.path.join(D, 'lines.json'), 'w'), separators=(',', ':')); print('lines', len(lines))
# assets
os.makedirs(os.path.join(A, 'art'), exist_ok=True); os.makedirs(os.path.join(A, 'photos'), exist_ok=True)
def sips(src, dst, size, q=82):
    subprocess.run(['sips', '-Z', str(size), '-s', 'format', 'jpeg', '-s', 'formatOptions', str(q), src, '--out', dst], capture_output=True)
for i in range(1, 8): sips(os.path.join(S, 'art', 'art_%02d.jpg' % i), os.path.join(A, 'art', 'art_%02d.jpg' % i), 720)
for src, dst in (('Artwork/citibike-gumbit.gif', 'gumbit_citibike.jpg'), ('Artwork/mj-bubbles.gif', 'gumbit_bubbles.jpg'), ('Artwork/IMG_2725.GIF', 'art_cats.jpg')): sips(os.path.join(HOME, src), os.path.join(A, 'art', dst), 900)
shutil.copy(os.path.join(HOME, 'Location Research/avea-115-interior/vinyl_pj_sig_white.png'), os.path.join(A, 'pj_sig_white_full.png'))
subprocess.run(['sips', '-Z', '900', os.path.join(A, 'pj_sig_white_full.png'), '--out', os.path.join(A, 'pj_sig_white.png')], capture_output=True); os.remove(os.path.join(A, 'pj_sig_white_full.png'))
for src, dst in (('photo.jpg', 'found_portal.jpg'), ('front.jpg', 'found_front.jpg'), ('v2803_04.jpg', 'found_corridor.jpg'), ('v2803_06.jpg', 'found_tilewall.jpg'), ('v2804_08.jpg', 'found_rear.jpg'), ('v2804_05.jpg', 'found_rosette.jpg')):
    sips(os.path.join(SCR, src), os.path.join(A, 'photos', dst), 1000)
print(sorted(os.listdir(A)), os.popen('du -sh ' + A + ' ' + os.path.join(R, 'media')).read())
# the two walk-through photos with a person in them are cropped to the room before they go on a public page
from PIL import Image
P_ = os.path.join(A, 'photos')
im = Image.open(os.path.join(P_, 'found_portal.jpg')); w_, h_ = im.size; im.crop((int(w_ * .13), int(h_ * .02), int(w_ * .93), int(h_ * .42))).save(os.path.join(P_, 'found_portal.jpg'), quality=84)
im = Image.open(os.path.join(P_, 'found_front.jpg')); w_, h_ = im.size; im.crop((0, 0, int(w_ * .46), h_)).save(os.path.join(P_, 'found_front.jpg'), quality=84)
