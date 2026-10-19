# Long Room: 51 East Houston Street

A scroll-driven site for PJ O'Rourke II: the ground-floor shop at 51 East Houston Street, Nolita, shown as found, peeled back to a white box, then built out with prints, tees and fifteen video screens, followed by the transit and traffic numbers.

Built from NYC Open Data (building footprints, planimetric layers, street trees), MTA ridership, NYC DOT counts, and the Meridian Retail Leasing brochure and plan. The room is a drawing from the plan and a walk-through video; dimensions are approximate. The upper floors are drawn from the city's height and floor count. The fit-out is a proposal.

Rebuild:

    python3 build/pull.py            # city and MTA data into data/
    python3 build/pull_raw.py        # lot, collisions, registry
    python3 build/make_extras.py     # pins, street lines, web images
    /Applications/Blender.app/Contents/MacOS/Blender --background --python build/build_h51.py   # model -> assets/houston_51.glb
    python3 build/build_page_h51.py  # index.html
    build/make_card.sh               # og.jpg
