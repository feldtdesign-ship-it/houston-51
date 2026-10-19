"""build_page_h51.py: data/ + build/h51_body.html + build/h51_3d.js + the numbers half of the 527 page -> index.html
The look and the numbers part come from west-27th-527/build/w27_template.html (same family); the story, the model and the screens are new.
Run: python3 build/build_page_h51.py"""
import json, os, base64, datetime, collections, re, math
S = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(S); D = os.path.join(R, 'data')
SRC = open(os.path.join(R, '..', 'west-27th-527', 'build', 'w27_template.html')).read()
LAT, LON = 40.724565, -73.994625
TODAY = datetime.date(2026, 10, 19)
NEAR = ('619', '17'); ALLCX = ('619', '17', '409')
NAMES = {'619': 'Broadway-Lafayette / Bleecker', '17': 'Prince St', '409': 'Spring St'}
def J(n, sub=''):
    p = os.path.join(D, sub, n)
    if not os.path.exists(p) or os.path.getsize(p) < 3: return None
    r = json.load(open(p)); return None if isinstance(r, dict) and 'daily' not in r else r
def dist(lat, lon): return math.hypot((lon - LON) * 111320 * math.cos(math.radians(LAT)), (lat - LAT) * 110540)
days = collections.Counter(); d = datetime.date(2026, 6, 1)
while d <= datetime.date(2026, 8, 31): days[(d.weekday() + 1) % 7] += 1; d += datetime.timedelta(days=1)
# ---- subway: hour x weekday, summer 2026 ----
hourly = {}
for cx in ALLCX:
    h = {dw: [0.0] * 24 for dw in range(7)}
    for x in (J(f'mta_hourly_{cx}.json') or []): h[int(x['dow'])][int(x['hr'])] = float(x['riders']) / days[int(x['dow'])]
    hourly[cx] = h
l_hourly = {dw: [round(sum(hourly[cx][dw][h] for cx in NEAR), 1) for h in range(24)] for dw in range(7)}
wkd = lambda h: [sum(h[d][hr] for d in (1, 2, 3, 4, 5)) / 5 for hr in range(24)]
wk = wkd(l_hourly); cxday = {cx: round(sum(wkd(hourly[cx]))) for cx in ALLCX}
peak_hr = max(range(24), key=lambda h: wk[h]); hl = lambda h: f"{(h + 11) % 12 + 1} {'am' if h < 12 else 'pm'}"
# ---- bus: MTA bus stop ridership estimates, the stops inside 300 m, summer 2026 (month x weekday x hour x stop x route) ----
stops = [s['stop_id'] for s in (J('bus_stops_near.json') or []) if s['d'] <= 300]
WD = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6}
acc = collections.defaultdict(lambda: collections.defaultdict(float)); months = set()
for r in (J('bus_est.json') or []):
    if r['stop_id'] not in stops or not ('2026-06' <= r['month'][:7] <= '2026-08'): continue
    acc[(r['month'][:7], r['weekday'])][int(r['hour'])] += float(r.get('estimated_ridership') or 0); months.add(r['month'][:7])
bus = {dw: [0.0] * 24 for dw in range(7)}
for wd, dw in WD.items():
    ks = [k for k in acc if k[1] == wd]
    for h in range(24): bus[dw][h] = round(sum(acc[k][h] for k in ks) / max(1, len(ks)), 2)
bus_day = round(sum(sum(bus[d][h] for d in (1, 2, 3, 4, 5)) / 5 for h in range(24)))
# ---- cars: the one DOT counter on East Houston by the door: Lafayette to Crosby, eastbound, one week in 2016 ----
byday = collections.defaultdict(lambda: [0.0] * 24); slots = collections.Counter()
for r in (J('atr.json') or []):
    if r['street'].upper() == 'E HOUSTON ST' and (r.get('fromst') or '').upper() == 'LAFAYETTE ST' and r.get('direction') == 'EB' and r['yr'] == '2016':
        k = (r['yr'], r['m'], r['d']); byday[k][int(r['hh'])] += float(r['vol']); slots[k] += 1
def wday(k): return datetime.date(int(k[0]), int(k[1]), int(k[2])).weekday() < 5
full = [v for k, v in byday.items() if slots[k] >= 96 and wday(k)]
car_hourly = [round(sum(v[h] for v in full) / len(full)) for h in range(24)] if full else [0] * 24
car_day = sum(car_hourly)
json.dump({'street': 'East Houston Street, Lafayette to Crosby, eastbound', 'when': '2016', 'full_weekdays': len(full), 'per_day': car_day, 'hourly': car_hourly}, open(os.path.join(D, 'atr_summary.json'), 'w'))
# ---- the years ----
def months_from(cx):
    out = {}
    for r in (J(f'mta_hist_{cx}.json') or []): out[r['month'][:7]] = out.get(r['month'][:7], 0) + float(r['riders'])
    return sorted([[m, v] for m, v in out.items() if m <= '2026-08'])
series = []; ratios = {}
for cx, col in zip(ALLCX, ('f', 'c', 'jz')):
    pts = months_from(cx); m = dict(pts); ratios[cx] = round(m.get('2026-08', 0) / m.get('2020-01', 1) * 100) if m.get('2020-01') else 0
    if pts: series.append({'k': col, 'label': NAMES[cx], 'pts': pts})
near_m = collections.defaultdict(float)
for cx in NEAR:
    for m, v in months_from(cx): near_m[m] += v
ratio = round(near_m.get('2026-08', 0) / near_m.get('2020-01', 1) * 100) if near_m.get('2020-01') else 0
# ---- daily against the weather ----
w = json.load(open(os.path.join(D, 'weather.json')))['daily']
wx = {t: (w['temperature_2m_max'][i], w['precipitation_sum'][i] or 0.0, w['snowfall_sum'][i] or 0.0) for i, t in enumerate(w['time'])}
dsum = collections.defaultdict(float)
for cx in NEAR:
    for r in (J(f'mta_daily_{cx}.json') or []): dsum[r['day'][:10]] += float(r['riders'])
daily = [[dt, round(v), round(wx[dt][0], 1), round(wx[dt][1], 2), round(wx[dt][2], 2)] for dt, v in sorted(dsum.items()) if dt in wx and '2025-01-01' <= dt <= '2026-08-31' and wx[dt][0] is not None]
fsum = collections.defaultdict(float)
for cx in NEAR:
    for x in (J(f'fare_{cx}.json') or []): fsum[x['fare_class_category']] += float(x['riders'])
t = sum(fsum.values()) or 1
fare = ' · '.join(f"{k.replace('OMNY - ', '')} {v / t * 100:.0f}%" for k, v in sorted(fsum.items(), key=lambda kv: -kv[1])[:4]) + ' (two stations, summer 2026)'
cams = []; camtime = ''
for c in (J('cameras.json') or [])[:6]:
    fp = os.path.join(R, c['file'])
    if os.path.exists(fp) and os.path.getsize(fp) > 1000: cams.append({'name': c['name'].strip(), 'dist': c['dist'], 'id': c['id'], 't': c['t'], 'src': 'data:image/jpeg;base64,' + base64.b64encode(open(fp, 'rb').read()).decode()}); camtime = c['t']
# ---- crashes, vacancy ----
cr = [r for r in (J('collisions.json', 'raw') or []) if r.get('latitude') and r['crash_date'] >= '2023-01-01' and dist(float(r['latitude']), float(r['longitude'])) <= 150]
SUM = lambda k: sum(int(r.get(k) or 0) for r in cr); killed = SUM('number_of_persons_killed')
y24 = {}
for r in (J('registry_block.json', 'raw') or []):
    if str(r.get('reporting_year', '')).startswith('2024'): y24[(r.get('bbl'), r.get('property_number'), r.get('property_street'), r.get('primary_business_activity'))] = r
vac_n = sum(1 for r in y24.values() if str(r.get('vacant_on_12_31', '')).upper().startswith('Y')); vac_t = len(y24)
nbldg = len(json.load(open(os.path.join(D, 'footprints.json')))); ntrees = sum(1 for x in json.load(open(os.path.join(D, 'trees.json'))) if x.get('status') == 'Alive')
points = json.load(open(os.path.join(D, 'model_points.json')))
pins = json.load(open(os.path.join(D, 'pins.json'))); cx_list = {c['complex_id'] + ':' + str(c['dist']): c for c in (J('subway_complexes.json', 'raw') or [])}
PINS = [{'n': "51 East Houston · with Milano's Bar", 'xy': [0, 0], 'd': 0, 'hot': True}]
PINS += [{'n': 'Broadway-Lafayette · B D F M 6', 'xy': points['bwy_laf'], 'd': 149, 'hot': True}, {'n': 'Prince St · N R W', 'xy': points['prince_rw'], 'd': 261, 'hot': True}]
PINS += [{'n': p['n'], 'xy': p['xy'], 'd': p['d']} for p in pins if p['n'] != "Milano's Bar"]
ped = [round(v / max(wk), 3) for v in wk]; ped = [max(.08, v) for v in ped]
cm = max(car_hourly) or 1; carn = [max(.1, round(v / cm, 3)) for v in car_hourly] if car_day else ped
FLOW = {'ped': ped, 'car': carn}
lines = json.load(open(os.path.join(D, 'lines.json')))
nb = ' · '.join(f"<b>{p['n']}</b> {p['d']} m" for p in pins if p['n'] not in ("Milano's Bar",)) + ' · also on Meridian\'s list: Torrisi, Tacombi, Love Adorned, Sézane'
bk = sorted(json.load(open(os.path.join(D, 'citibike.json'))), key=lambda s: s['dist'])[:4]
bikes = ' · '.join(f"{b['name']}, {b['dist']} m, {b.get('capacity') or '?'} docks" for b in bk)
data = {'l_hourly': l_hourly, 'bus_a': bus, 'car_hourly': car_hourly, 'series': series, 'daily': daily, 'fare': fare, 'cams': cams}
f = lambda n: f"{n:,}"

# ---------- assemble from the 527 look + numbers half ----------
head = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Long Room · 51 East Houston Street</title>
<meta name="description" content="DESC">
<meta name="theme-color" content="#141210">
<link rel="canonical" href="URL">
<meta property="og:type" content="website"><meta property="og:title" content="51 East Houston Street · Long Room"><meta property="og:description" content="DESC">
<meta property="og:url" content="URL"><meta property="og:image" content="URLog.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="51 East Houston Street · Long Room"><meta name="twitter:description" content="DESC"><meta name="twitter:image" content="URLog.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800&family=Figtree:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap">
'''
URL = 'https://feldtdesign-ship-it.github.io/houston-51/'
DESC = "PJ O'Rourke II at 51 East Houston Street: a 1,400 square foot ground-floor shop in Nolita, about 68 feet deep, peeled back to a white box and built out with prints, tees and a screen on every sightline. The corner, the room, the trains and the traffic, from public data."
head = head.replace('DESC', DESC).replace('URL', URL)
css = SRC[SRC.index('<style>'):SRC.index('</style>') + 8]
css = css.replace('--f:#C56BD3;--six:#B933AD;', '--f:#FF6319;--six:#00933C;').replace('--paper:#141210;', '--paper:#141210;--sc:20,18,16;--cardbg:rgba(30,27,24,.66);')
css = css.replace('#scrim{position:fixed;inset:0;z-index:1;pointer-events:none;background:linear-gradient(90deg,rgba(20,18,16,.94) 0%,rgba(20,18,16,.72) 34%,rgba(20,18,16,.08) 60%,rgba(20,18,16,0) 100%);transition:background .5s}',
                  '#scrim{position:fixed;inset:0;z-index:1;pointer-events:none;background:linear-gradient(90deg,rgba(var(--sc),.66) 0%,rgba(var(--sc),.34) 26%,rgba(var(--sc),0) 48%,rgba(var(--sc),0) 100%);transition:background .5s}')
css = css.replace('#scrim.flip{background:linear-gradient(270deg,rgba(20,18,16,.94) 0%,rgba(20,18,16,.72) 34%,rgba(20,18,16,.08) 60%,rgba(20,18,16,0) 100%)}',
                  '#scrim.flip{background:linear-gradient(270deg,rgba(var(--sc),.66) 0%,rgba(var(--sc),.34) 26%,rgba(var(--sc),0) 48%,rgba(var(--sc),0) 100%)}')
css = css.replace('.card{background:rgba(30,27,24,.88);backdrop-filter:blur(6px);border-top:3px solid var(--f);padding:26px 28px}', '.card{background:var(--cardbg);backdrop-filter:blur(6px);border-top:3px solid var(--f);padding:24px 26px}')
assert '--cardbg' in css and 'rgba(var(--sc),.66)' in css
extra = open(os.path.join(S, 'h51.css')).read()
css = css.replace('</style>', extra + '\n</style>')
body = open(os.path.join(S, 'h51_body.html')).read().replace('__NEIGHBOURS__', nb).replace('__BIKES__', bikes)
# the numbers half, patched
a = SRC.index('<div id="divider">'); b = SRC.index('<footer>'); num = SRC[a:b]
def sub(s, old, new):
    assert old in s, old[:90]; return s.replace(old, new)
for old, new in (
 ('527 West 27th Street · the Jardim retail · no station inside 500 m', '51 East Houston Street · Long Room · Broadway-Lafayette 149 m'),
 ('people an hour through Hudson Yards and 23rd Street', 'people an hour through Broadway-Lafayette and Prince Street'),
 ('Bus inside 300 m · M11 and M12', 'Bus boardings inside 300 m · M21, M1, M103, M55'),
 ('<span id="d-a">–</span><span> riders an hour</span>', '<span id="d-a">–</span><span> boardings an hour</span>'),
 ('Boardings and alightings at the stops on Tenth Avenue at 25th, 27th and 30th, and Eleventh at 26th and 29th. True scale, which is why it is small.', "MTA's estimate of passengers boarding at the 15 stops within 300 m, summer 2026, by hour of a typical weekday. Boardings only, true scale."),
 ('Cars on Eleventh · four blocks south', 'Cars on East Houston · Lafayette to Crosby'),
 ('Northbound at 23rd Street, DOT counter, 2019. The nearest avenue the city has counted. 27th Street has never been counted.', 'Eastbound only, one week in 2016, DOT counter, a block west of the door. The westbound lanes were not counted.'),
 ('Cars on Eleventh Avenue are below on their own scale.', 'Cars on East Houston are below on their own scale.'),
 ('Cars on Eleventh /hr', 'Cars on Houston /hr'), ('Vehicles an hour, Eleventh Ave northbound at 23rd Street, 2019', 'Vehicles an hour, East Houston eastbound, Lafayette to Crosby, 2016, weekdays'),
 ('Vehicles per hour on Eleventh Avenue', 'Vehicles per hour on East Houston Street'),
 ('Entries at Hudson Yards and 23rd Street together, by hour and weekday', 'Entries at Broadway-Lafayette and Prince Street together, by hour and weekday'),
 ('Hudson Yards is at __R471__ percent of where it started, 23rd Street at __R165__. The two nearest together are at __RATIO__ percent.', 'Broadway-Lafayette is at __R619__ percent of where it started, Prince Street at __R17__, Spring Street at __R409__. The two nearest together are at __RATIO__ percent.'),
 ('<span><i class="l"></i>34 St-Hudson Yards, 7</span><span><i class="y"></i>23 St, C E</span><span><i class="a"></i>34 St-Penn Station, A C E</span>', '<span><i class="l"></i>Broadway-Lafayette / Bleecker, B D F M 6</span><span><i class="y"></i>Prince St, N R W</span><span><i class="a"></i>Spring St, 6</span>'),
 ('Very little. No traffic counter has been put on 27th Street, and nobody counts the sidewalk.', 'More than most blocks, and still not the sidewalk. Nobody counts the people on foot.'),
 ('<span class="k">Frontage</span><span><b>61 ft 7 in</b> on 27th Street, about 32 ft of it glass</span>', '<span class="k">Frontage</span><span><b>About 10 ft</b> of glass and door on East Houston, in a 24.6 ft lot · read from the video and the plan</span>'),
 ('<b>__CARS__ a day</b> northbound on Eleventh at 23rd, 2019, DOT counter, peak __CARPEAK__ an hour', '<b>__CARS__ a day</b> eastbound on East Houston, Lafayette to Crosby, a weekday average from the week counted in 2016, DOT counter, peak __CARPEAK__ an hour'),
 ('<span class="k">Bus a month</span><span><b>__BUSMO__</b> boardings and alightings at the stops inside 300 m, last twelve full months</span>', '<span class="k">Bus a weekday</span><span><b>__BUSDAY__</b> estimated boardings at the 15 stops inside 300 m, summer 2026, MTA estimate</span>'),
 ('<span class="k">Who rides here</span>', '<span class="k">Storefronts dark</span><span><b>__VACN__ of __VACT__</b> within 250 m filed vacant on 31 December 2024, DOF registry</span></div>\n    <div><span class="k">Who rides here</span>'),
 ):
    num = sub(num, old, new)
i = num.index('<h2><small>The block</small>'); s0 = num.rfind('<section>', 0, i); s1 = num.index('</section>', i) + len('</section>')
room = '''<section>
  <h2><small>The room</small>As found, as drawn</h2>
  <p>The model above is a drawing. These are the room: frames from the walk-through video and a photograph of one of the steel portals, as it stands today.</p>
  <div class="gal"><figure><img src="assets/photos/found_front.jpg" alt="The glass door and window from the sidewalk"><figcaption class="eyebrow">The glass from the sidewalk: window left, door right, black steel</figcaption></figure>
  <figure><img src="assets/photos/found_corridor.jpg" alt="The corridor"><figcaption class="eyebrow">The corridor from the door: marble, then wood, then the tile wall</figcaption></figure>
  <figure><img src="assets/photos/found_portal.jpg" alt="Steel portal"><figcaption class="eyebrow">A steel portal framed in raw timber, a bare white-painted brick wall</figcaption></figure>
  <figure><img src="assets/photos/found_rosette.jpg" alt="The tile wall and rosette"><figcaption class="eyebrow">The black hexagon tile wall and the plaster rosette</figcaption></figure></div>
</section>'''
num = num[:s0] + room + num[s1:]
src_a = num.index('<p class="src">'); src_b = num.index('</p>', src_a) + 4
srcs = ('<p class="src">Sources · <a href="https://data.ny.gov/">MTA subway hourly ridership, complexes 619, 17, 409, 232 and 103, and MTA bus stop ridership estimates, data.ny.gov</a> · <a href="https://data.cityofnewyork.us/Transportation/Automated-Traffic-Volume-Counts/7ym2-wayt">NYC DOT Automated Traffic Volume Counts</a> · '
 '<a href="https://data.cityofnewyork.us/City-Government/Storefronts-Reported-Vacant-or-Not/92iy-9c3n">DOF Storefront Registry</a> · <a href="https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95">NYC Motor Vehicle Collisions</a> · NYC building footprints and Planimetric Database · PLUTO, lot 1005090023 · NYC Street Tree Census · '
 '<a href="https://open-meteo.com/">Open-Meteo</a> · <a href="https://webcams.nyctmc.org/">NYC DOT cameras</a> · NYC Planning Labs GeoSearch · Meridian Retail Leasing, 51 East Houston Street brochure, plan and photographs · '
 '<a href="https://citylore.org/?p=21811">CityLore, Milano\'s Bar</a> · <a href="https://www.timeout.com/newyork/restaurants/emilios-ballato">Time Out, Ballato</a></p>')
num = num[:src_a] + srcs + num[src_b:]
footer = ('<footer><div class="wrap"><p>Model built from NYC Open Data: building footprints with recorded roof heights, planimetric roadbed, sidewalk and median polygons, street centreline names and the 2015 street tree census. Lot matched by BBL. The room is drawn from the Meridian plan, the walk-through video and one photograph; dimensions are read off those and are approximate. '
          'The upper floors are drawn from the city\'s height and floor count, not from a photograph. The fit-out, the screens and their positions are a proposal for PJ O\'Rourke II, not an offer or a lease. Transit figures are MTA, summer 2026. Vehicle counts are NYC DOT, one week of 2016. Gathered __TODAY__.</p></div></footer>\n')
# numbers script
ja = SRC.index('<script>\nconst D = __DATA__;'); jb = SRC.index('</script>', ja) + 9; njs = SRC[ja:jb]
njs = sub(njs, '$(\'sub\').innerHTML=`Entries at 34 St-Hudson Yards and 23 St added together and doubled to include exits, summer 2026 average. The nearest stairs are <b>543 m</b> away. Peak for a ${dayName} is <b>${fmt(Math.max(...L[state.day])*2)}</b> an hour.`;',
          '$(\'sub\').innerHTML=`Entries at Broadway-Lafayette and Prince St added together and doubled to include exits, summer 2026 average. The nearest stairs are <b>149 m</b> away. Peak for a ${dayName} is <b>${fmt(Math.max(...L[state.day])*2)}</b> an hour.`;')
js3d = open(os.path.join(S, 'h51_3d.js')).read()
imp = '<script type="importmap">\n{"imports":{"three":"https://unpkg.com/three@0.161.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.161.0/examples/jsm/"}}\n</script>\n'
out = head + css + '</head><body>\n' + body + num + footer + njs + '\n\n' + imp + '<script type="module">\n' + js3d + '</script></body></html>\n'
subs = {'__DATA__': json.dumps(data, separators=(',', ':')), '__POINTS__': json.dumps(points), '__PINS__': json.dumps(PINS), '__LINES__': json.dumps(lines, separators=(',', ':')), '__FLOW__': json.dumps(FLOW),
        '__TODAY__': f"{TODAY.day} {TODAY:%B %Y}", '__CARS__': f(car_day), '__CARPEAK__': f(max(car_hourly)), '__CRASH__': str(len(cr)), '__HURT__': str(SUM('number_of_persons_injured')), '__PED__': str(SUM('number_of_pedestrians_injured')), '__CYC__': str(SUM('number_of_cyclist_injured')),
        '__KILLED__': 'none killed' if not killed else f"{killed} killed", '__R619__': str(ratios['619']), '__R17__': str(ratios['17']), '__R409__': str(ratios['409']), '__RATIO__': str(ratio),
        '__VACN__': str(vac_n), '__VACT__': str(vac_t), '__BUSDAY__': f(bus_day), '__CAMTIME__': camtime, '__NBLDG__': f(nbldg), '__NTREES__': f(ntrees)}
for k, v in subs.items(): out = out.replace(k, v)
left = sorted(set(re.findall(r'__[A-Z0-9]+__', out)))
open(os.path.join(R, 'index.html'), 'w').write(out)
print({k: v for k, v in subs.items() if k not in ('__DATA__', '__POINTS__', '__PINS__', '__LINES__', '__FLOW__')})
print(f"built index.html {len(out) // 1024} KB · cams {len(cams)} · daily {len(daily)} · series {[s['label'] for s in series]} · bus stops {len(stops)} · car weekdays {len(full)} · unfilled {left}")
