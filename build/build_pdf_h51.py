"""build_pdf_h51.py: the build-out deck for 51 East Houston, in the system of the 115 Avenue A deck (avea-115-interior/deck/deck.html):
1920 x 1080 slides, Archivo + IBM Plex Mono, ink / paper / tactile-strip yellow, the strip as a dotted rule.
Run: python3 build/build_pdf_h51.py   -> pdf/long_room.html and PJ_ORourke_II_51_East_Houston.pdf
Images come from renders/*.jpg (build/render_h51.py + build/post_h51.py). Printed through pj-tee-tech-pack/tools/print_pdf.mjs (Chrome's own printer hangs on this Mac).
The numbers are the same ones on the micro site (data/): no money anywhere in this file, on purpose."""
import os, re, shutil, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PJ = os.path.dirname(os.path.dirname(OUT))
PDF = os.path.join(OUT, 'pdf'); IMG = os.path.join(PDF, 'img'); os.makedirs(IMG, exist_ok=True)
DECK = open(os.path.join(os.path.dirname(OUT), 'avea-115-interior', 'deck', 'deck.html')).read()
head_css = DECK[DECK.index('<link href='):DECK.index('</style>') + 8]
head_css = head_css.replace('--film:"https://feldtdesign-ship-it.github.io/pj-115-avenue-a/";', '')
for n in os.listdir(os.path.join(OUT, 'renders')):
    if n.endswith('.jpg'): shutil.copy(os.path.join(OUT, 'renders', n), os.path.join(IMG, n))
for n in os.listdir(IMG):
    if n.startswith('H51_') and n.endswith('.jpg'): subprocess.run(['sips', '-Z', '1920', '-s', 'format', 'jpeg', '-s', 'formatOptions', '86', os.path.join(IMG, n), '--out', os.path.join(IMG, n)], capture_output=True)
shutil.copy(os.path.join(os.path.dirname(OUT), 'avea-115-interior', 'deck', 'img', 'PJ_sig_crop.svg'), os.path.join(IMG, 'PJ_sig_crop.svg'))
T = json.load(open(os.path.join(OUT, 'data', 'atr_summary.json')))
foot = lambda n: '<div class="foot"><span>PJ O\'Rourke II / 51 East Houston Street</span><span>%02d</span></div>' % n
S = []
S.append('''<section class="slide dark">
  <img class="cover-img" src="img/H51_hero_1_long.jpg" style="height:760px;object-position:50% 60%" alt="">
  <div style="position:absolute;left:0;right:0;top:0;height:760px;background:linear-gradient(180deg,rgba(12,12,12,.55) 0,rgba(12,12,12,0) 22%)"></div>
  <div class="label" style="position:absolute;left:80px;top:60px;color:#f6f5f2">Proposal · 51 East Houston Street · Nolita · October 2026</div>
  <div style="position:absolute;left:80px;right:80px;top:782px;display:flex;justify-content:space-between;align-items:flex-end">
    <div class="h-xl" style="font-size:84px">PJ O'Rourke II<br><span style="color:var(--yellow)">at 51 East Houston</span></div>
    <img class="sig" src="img/PJ_sig_crop.svg" style="width:300px;margin-bottom:-6px" alt="PJ O'Rourke signature">
  </div>
  <div class="strip bottom"></div>
</section>''')
S.append('''<section class="slide light">
  <div style="position:absolute;left:80px;top:80px;width:860px">
    <div class="label dim">01 · The proposal</div>
    <div class="h-cond" style="font-size:132px;margin-top:34px">A long room.<br>Painted white.<br>Then the work.</div>
    <div class="rule" style="margin:48px 0 40px;width:120px;background:var(--yellow);opacity:1;height:8px"></div>
    <p class="quote" style="font-size:44px">A shop 68 feet deep and 10 feet wide between Mulberry and Mott, with a storage room behind it. A white box today. A gallery you walk down, with a screen at the end of the sightline.</p>
    <p class="label dim" style="margin-top:28px">Listed by Meridian Retail Leasing at 1,400 sq ft</p>
  </div>
  <img src="img/H51_hero_7_tables.jpg" style="position:absolute;right:0;top:0;width:960px;height:1080px;object-fit:cover;object-position:62% 50%" alt="">
  <div class="tag" style="position:absolute;right:40px;bottom:60px">Concept image</div>
</section>''')
S.append('''<section class="slide dark">
  <div class="label" style="position:absolute;left:80px;top:70px">02 · The method</div>
  <div class="h-xl" style="position:absolute;left:80px;top:118px;font-size:96px">Peel It Back.<br>Build It Out.</div>
  <div style="position:absolute;left:80px;right:80px;top:380px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:28px">
    <div><img src="img/H51_doll_found.jpg" style="width:100%;height:480px;object-fit:cover;object-position:50% 55%" alt=""><div class="tag" style="margin-top:18px">As found</div><p class="body" style="font-size:24px;margin-top:12px;color:#d8d5ce">Hexagon marble, a strip of wood, a black-and-white tile wall, steel and timber, grey slate at the back.</p></div>
    <div><img src="img/H51_doll_white.jpg" style="width:100%;height:480px;object-fit:cover;object-position:50% 55%" alt=""><div class="tag" style="margin-top:18px">The white box</div><p class="body" style="font-size:24px;margin-top:12px;color:#d8d5ce">Every finish lifted. White walls, one pale floor, the track lighting that is already there.</p></div>
    <div><img src="img/H51_doll_built.jpg" style="width:100%;height:480px;object-fit:cover;object-position:50% 55%" alt=""><div class="tag" style="margin-top:18px">Built out</div><p class="body" style="font-size:24px;margin-top:12px;color:#d8d5ce">Prints on the east wall, tees on the west, two oak tables, fifteen screens, the yellow strip down the floor.</p></div>
  </div>
  ''' + foot(3) + '''<div class="strip bottom"></div>
</section>''')
S.append('''<section class="slide dark">
  <img class="cover-img" src="img/H51_hero_3_prints.jpg" style="object-position:50% 50%" alt="">
  <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(12,12,12,.72) 0,rgba(12,12,12,0) 30%,rgba(12,12,12,0) 62%,rgba(12,12,12,.85) 100%)"></div>
  <div class="label" style="position:absolute;left:80px;top:70px">03 · The walls</div>
  <div class="h-xl" style="position:absolute;left:80px;top:118px;font-size:96px">A Gallery That<br>Sells The Shirts</div>
  <div style="position:absolute;left:80px;right:80px;bottom:110px;display:flex;justify-content:space-between;gap:80px">
    <div style="max-width:720px"><div class="tag">East wall</div><p class="body" style="margin-top:18px;font-size:34px;font-weight:600">Nine of PJ's line drawings in black 16 by 20 frames, one level row, above the yellow strip.</p></div>
    <div style="max-width:720px;text-align:right"><div class="tag">West wall</div><p class="body" style="margin-top:18px;font-size:34px;font-weight:600">Pipe and plank. His tees on hangers, one colourway to a bay.</p></div>
  </div>
  <div class="strip bottom"></div>
</section>''')
S.append('''<section class="slide dark">
  <img src="img/H51_hero_2_rail.jpg" style="position:absolute;left:0;top:0;width:1180px;height:1080px;object-fit:cover;object-position:40% 50%" alt="">
  <div style="position:absolute;left:1240px;top:80px;right:80px">
    <div class="label dim">04 · In the room</div>
    <div class="h-cond" style="font-size:150px;margin-top:30px">Tees.<br>Prints.<br>Arcade.</div>
    <p class="body" style="margin-top:38px;color:#d8d5ce">Cream, navy, lilac, moss and peach, with his art on every one. Oak tables carry the folded stacks. A Galaga cabinet sits kitty-corner at the back.</p>
  </div>
  <img src="img/H51_hero_6_galaga.jpg" style="position:absolute;left:1240px;bottom:80px;width:600px;height:280px;object-fit:cover;object-position:45% 55%" alt="Arcade cabinet in the back corner">
  <div class="strip v" style="left:1180px"></div>
</section>''')
S.append('''<section class="slide dark">
  <img class="cover-img" src="img/H51_hero_4_wall.jpg" style="object-position:50% 50%" alt="">
  <div style="position:absolute;inset:0;background:linear-gradient(0deg,rgba(12,12,12,.88) 0,rgba(12,12,12,.35) 34%,rgba(12,12,12,0) 56%)"></div>
  <div class="label" style="position:absolute;left:80px;top:70px">05 · The screens</div>
  <div style="position:absolute;left:80px;right:80px;bottom:120px;display:flex;justify-content:space-between;align-items:flex-end;gap:60px">
    <div class="h-cond" style="font-size:170px">15 screens.<br>All PJ.</div>
    <div style="max-width:760px"><div class="tag">Video wall</div><p class="body" style="margin-top:16px;font-size:30px;font-weight:600">Six panels on the black back wall of the storage room, seen down the whole corridor through the doorway. They show one picture, then six, then prints. Three more hang on poles, and three face East Houston from the window.</p></div>
  </div>
  <div class="strip bottom"></div>
</section>''')
S.append('''<section class="slide light">
  <img src="img/H51_hero_5_reverse.jpg" style="position:absolute;left:0;top:0;width:1180px;height:1080px;object-fit:cover;object-position:62% 50%" alt="">
  <div style="position:absolute;left:1240px;top:80px;right:80px">
    <div class="label dim">06 · The details</div>
    <div class="h-cond" style="font-size:132px;margin-top:30px">The platform edge, indoors.</div>
    <p class="body" style="margin-top:34px">The yellow tactile strip is the edge of every subway platform, where PJ started. Here it runs the length of the east wall: 79 feet, from the glass through the doorway to the back wall.</p>
    <p class="body" style="margin-top:20px">Black paint on the storage room's back wall, the track, the pipe and the frames. White everywhere else. The work does the colour.</p>
  </div>
  <div class="strip v" style="left:1180px"></div>
</section>''')
S.append('''<section class="slide dark">
  <img src="img/H51_plan_built.jpg" style="position:absolute;left:0;top:0;width:560px;height:1080px;object-fit:cover;object-position:50% 50%" alt="Plan">
  <div style="position:absolute;left:660px;top:80px;right:80px">
    <div class="label dim">07 · Measured, not guessed</div>
    <div class="h-xl" style="font-size:92px;margin-top:30px">We already know this room.</div>
    <p class="body" style="margin-top:28px;color:#d8d5ce;max-width:1050px">Every rendering is built from a to-scale 3D model, drawn from Meridian's plan and read against a walk-through video of the space. Dimensions are read off those and are approximate.</p>
    <table style="margin-top:36px;width:100%;border-collapse:collapse;font-size:27px">
      <tr style="border-top:2px solid #3a3936"><td style="padding:13px 0" class="cap">Front zone</td><td style="text-align:right;font-weight:800">9 ft 11 in wide, 26 ft from the glass</td></tr>
      <tr style="border-top:2px solid #3a3936"><td style="padding:13px 0" class="cap">Back zone</td><td style="text-align:right;font-weight:800">8 ft 10 in wide, to 67 ft 7 in</td></tr>
      <tr style="border-top:2px solid #3a3936"><td style="padding:13px 0" class="cap">Bath</td><td style="text-align:right;font-weight:800">8 ft 8 in x 5 ft 3 in, west wall</td></tr>
      <tr style="border-top:2px solid #3a3936"><td style="padding:13px 0" class="cap">Passage past the bath</td><td style="text-align:right;font-weight:800">about 3 ft 6 in wide</td></tr>
      <tr style="border-top:2px solid #3a3936"><td style="padding:13px 0" class="cap">Storage room behind</td><td style="text-align:right;font-weight:800">12 ft 6 in x 24 ft 6 in</td></tr>
      <tr style="border-top:2px solid #3a3936;border-bottom:2px solid #3a3936"><td style="padding:13px 0" class="cap">Building</td><td style="text-align:right;font-weight:800">1900 walk-up, 5 storeys, 24.6 ft lot</td></tr>
    </table>
    <p class="cap" style="margin-top:22px;color:#a9a69e">The plan is an architect's drawing of proposed work, so the video wins where they differ. Ceiling about 11 ft at the front, lower at the back, estimated. Not drawn: Milano's and the building's entrance hall. Meridian lists 1,400 sq ft; the city lists 705 sq ft of retail on record.</p>
  </div>
  <div class="strip bottom"></div>
</section>''')
S.append('''<section class="slide light">
  <img src="img/H51_hero_8_street.jpg" style="position:absolute;left:0;top:0;width:1920px;height:600px;object-fit:cover;object-position:50% 62%" alt="">
  <div class="label" style="position:absolute;left:80px;top:48px;color:#f6f5f2">08 · The corner</div>
  <div style="position:absolute;left:80px;right:80px;top:650px;display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr;gap:56px;align-items:start">
    <div class="h-cond" style="font-size:104px">Crossroads of Nolita, NoHo and the LES.</div>
    <div><div class="num" style="font-size:120px">149</div><div class="rule" style="margin:14px 0 12px"></div><p class="body" style="font-size:24px">metres to the B, D, F, M and 6 at Broadway-Lafayette and Bleecker.</p></div>
    <div><div class="num" style="font-size:120px">10,961</div><div class="rule" style="margin:14px 0 12px"></div><p class="body" style="font-size:24px">people an hour at the weekday peak through the two nearest stations, MTA, summer 2026.</p></div>
    <div><div class="num" style="font-size:120px">''' + '{:,}'.format(T['per_day']) + '''</div><div class="rule" style="margin:14px 0 12px"></div><p class="body" style="font-size:24px">cars a weekday eastbound on East Houston by the door, DOT count, 2016.</p></div>
  </div>
  <div class="foot"><span>Sources: MTA, NYC DOT, NYC Open Data, Meridian Retail Leasing</span><span>09</span></div>
</section>''')
S.append('''<section class="slide dark">
  <img class="cover-img" src="img/H51_hero_1_long.jpg" style="object-position:50% 50%;filter:brightness(.55)" alt="">
  <div style="position:absolute;left:80px;top:500px">
    <div class="h-xl" style="font-size:132px">Ready when<br><span style="color:var(--yellow)">you are.</span></div>
    <p class="body" style="margin-top:34px;font-size:34px">The room, the numbers and the build-out, to scroll:</p>
    <p class="label" style="margin-top:10px;font-size:26px;color:var(--yellow)">feldtdesign-ship-it.github.io/houston-51</p>
  </div>
  <img class="sig" src="img/PJ_sig_crop.svg" style="position:absolute;right:80px;bottom:110px;width:380px" alt="">
  <div class="foot"><span>PJ O'Rourke II</span><span>Not an offer. Gathered 19 October 2026.</span></div>
  <div class="strip bottom"></div>
</section>''')
html = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>PJ O\'Rourke II · 51 East Houston Street</title>\n' + head_css + '\n</head><body>\n' + '\n'.join(S) + '\n</body></html>\n'
open(os.path.join(PDF, 'long_room.html'), 'w').write(html)
out = os.path.join(OUT, 'PJ_ORourke_II_51_East_Houston.pdf')
subprocess.run(['node', os.path.join(PJ, 'pj-tee-tech-pack', 'tools', 'print_pdf.mjs'), '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', os.path.join(PDF, 'long_room.html'), out], check=False)
print('pdf', out, os.path.exists(out) and os.path.getsize(out) // 1024, 'KB')
