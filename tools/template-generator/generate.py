#!/usr/bin/env python3
"""
Wedding Invitation Template Generator
======================================
Generates 50 professional animated HTML invitation templates for the
wedding-invitations platform using open-source JS animation libraries:
  - GSAP 3.13 (timelines, DrawSVG, ScrollTrigger) — free since Webflow acquisition
  - Anime.js 3.2  — lightweight JS animation
  - tsParticles   — star/particle backgrounds
  - Typed.js 3    — typewriter text effects
  - Vivus.js      — SVG path draw animation
  - Sakura.js     — falling petal effect
  - Three.js r172  — 3D crystal particle field
  - canvas-confetti — celebration burst

Usage:
    pip install Jinja2
    python generate.py
    # or specify output directory:
    python generate.py --output ../../apps/frontend/public/templates
"""

import argparse
import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# ──────────────────────────────────────────────────────────────────────────────
# SAMPLE DATA  (used for preview generation)
# ──────────────────────────────────────────────────────────────────────────────
SAMPLE = {
    "bride_name":    "Amelia",
    "groom_name":    "James",
    "guest_name":    "Distinguished Guest",
    "wedding_date":  "Saturday, June 14, 2026",
    "start_time":    "4:00 PM",
    "venue_name":    "The Grand Pavilion",
    "address":       "123 Garden Lane",
    "city":          "London",
    "country":       "United Kingdom",
    "message":       "Your presence is the greatest gift we could ask for. We cannot wait to celebrate with you.",
}

# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATE CONFIG   Maps each of the 50 template IDs to a jinja2 template file
# and a set of design variables (colors, fonts, etc.)
# ──────────────────────────────────────────────────────────────────────────────

CONFIGS = {

    # ── BASIC / FADE  (3 color variants) ─────────────────────────────────────
    "basic-1": {
        "tpl": "basic/fade.html",
        "primary": "#FFF5F5", "secondary": "#EAC5C5", "accent": "#B85C70",
        "text_color": "#3A1A20",
        "heading_font": "Playfair Display", "body_font": "Lato",
        "svg_stroke": "#EAC5C5",
    },
    "basic-2": {
        "tpl": "basic/fade.html",
        "primary": "#F5FAF5", "secondary": "#A8C8B0", "accent": "#3D7A5A",
        "text_color": "#1A3322",
        "heading_font": "Playfair Display", "body_font": "Lato",
        "svg_stroke": "#A8C8B0",
    },
    "basic-3": {
        "tpl": "basic/fade.html",
        "primary": "#F0F5FA", "secondary": "#8BAFD6", "accent": "#2A5C96",
        "text_color": "#0E2244",
        "heading_font": "Playfair Display", "body_font": "Lato",
        "svg_stroke": "#8BAFD6",
    },

    # ── BASIC / TYPEWRITER  (3 color variants) ────────────────────────────────
    "basic-4": {
        "tpl": "basic/typewriter.html",
        "primary": "#FFFDF7", "secondary": "#E8C98C", "accent": "#B8860B",
        "text_color": "#3A2A06",
        "heading_font": "Cormorant Garamond", "body_font": "Open Sans",
    },
    "basic-5": {
        "tpl": "basic/typewriter.html",
        "primary": "#FFF8F5", "secondary": "#F0B8C0", "accent": "#B84860",
        "text_color": "#3A1020",
        "heading_font": "Cormorant Garamond", "body_font": "Open Sans",
    },
    "basic-6": {
        "tpl": "basic/typewriter.html",
        "primary": "#F8F5FF", "secondary": "#C4B0E8", "accent": "#7050B8",
        "text_color": "#201040",
        "heading_font": "Cormorant Garamond", "body_font": "Open Sans",
    },

    # ── BASIC / SLIDE  (3 color variants) ────────────────────────────────────
    "basic-7": {
        "tpl": "basic/slide.html",
        "primary": "#FDF5F0", "secondary": "#E8C0A0", "accent": "#C45028",
        "text_color": "#3A1808",
        "heading_font": "Libre Baskerville", "body_font": "Source Sans Pro",
    },
    "basic-8": {
        "tpl": "basic/slide.html",
        "primary": "#F5FAF0", "secondary": "#B4D8A4", "accent": "#4A8830",
        "text_color": "#183010",
        "heading_font": "Libre Baskerville", "body_font": "Source Sans Pro",
    },
    "basic-9": {
        "tpl": "basic/slide.html",
        "primary": "#F8F5FF", "secondary": "#DDD0F8", "accent": "#7048C8",
        "text_color": "#200A50",
        "heading_font": "Libre Baskerville", "body_font": "Source Sans Pro",
    },

    # ── BASIC / FLORAL  (3 color variants) ───────────────────────────────────
    "basic-10": {
        "tpl": "basic/floral.html",
        "primary": "#FFFCF8", "secondary": "#FFD0E8", "accent": "#C03870",
        "text_color": "#380018",
        "heading_font": "EB Garamond", "body_font": "Raleway",
        "svg_stroke": "#FFB0D0",
    },
    "basic-11": {
        "tpl": "basic/floral.html",
        "primary": "#F8FFFC", "secondary": "#A8E4C8", "accent": "#207858",
        "text_color": "#082818",
        "heading_font": "EB Garamond", "body_font": "Raleway",
        "svg_stroke": "#78C8A0",
    },
    "basic-12": {
        "tpl": "basic/floral.html",
        "primary": "#F8FCFF", "secondary": "#A8C8F0", "accent": "#2048A0",
        "text_color": "#081838",
        "heading_font": "EB Garamond", "body_font": "Raleway",
        "svg_stroke": "#78A8E0",
    },

    # ── BASIC / FLOAT  (3 color variants) ────────────────────────────────────
    "basic-13": {
        "tpl": "basic/float.html",
        "primary": "#FFFFFF", "secondary": "#F0E4E4", "accent": "#8B2A2A",
        "text_color": "#2A1010",
        "heading_font": "Josefin Sans", "body_font": "Crimson Text",
    },
    "basic-14": {
        "tpl": "basic/float.html",
        "primary": "#FAFAF8", "secondary": "#EDE4D8", "accent": "#7A5830",
        "text_color": "#381E08",
        "heading_font": "Josefin Sans", "body_font": "Crimson Text",
    },
    "basic-15": {
        "tpl": "basic/float.html",
        "primary": "#F5F8FF", "secondary": "#D4DEFC", "accent": "#2038A0",
        "text_color": "#081030",
        "heading_font": "Josefin Sans", "body_font": "Crimson Text",
    },

    # ── PREMIUM / GOLDEN  (3 color variants) ─────────────────────────────────
    "premium-1": {
        "tpl": "premium/golden.html",
        "primary": "#FDF8EC", "secondary": "#E8CC78", "accent": "#B8860B",
        "text_color": "#3A2800",
        "heading_font": "Cinzel Decorative", "body_font": "Didact Gothic",
        "shimmer_colors": "#b8860b,#ffd700,#daa520,#f0e080,#b8860b",
        "dark": False,
    },
    "premium-2": {
        "tpl": "premium/golden.html",
        "primary": "#FFF5F8", "secondary": "#F0B0C0", "accent": "#B85878",
        "text_color": "#380018",
        "heading_font": "Cinzel Decorative", "body_font": "Didact Gothic",
        "shimmer_colors": "#b85878,#f090b0,#e878a0,#f090b0,#b85878",
        "dark": False,
    },
    "premium-3": {
        "tpl": "premium/golden.html",
        "primary": "#0E0800", "secondary": "#1E1400", "accent": "#FFD700",
        "text_color": "#F0E8C8",
        "heading_font": "Cinzel Decorative", "body_font": "Didact Gothic",
        "shimmer_colors": "#b8860b,#ffd700,#f0c040,#ffd700,#b8860b",
        "dark": True,
    },

    # ── PREMIUM / PETAL  (3 color variants) ──────────────────────────────────
    "premium-4": {
        "tpl": "premium/petal.html",
        "primary": "#FFF0F5", "secondary": "#FFB8D0", "accent": "#C03878",
        "text_color": "#380020",
        "heading_font": "Great Vibes", "body_font": "Lato",
    },
    "premium-5": {
        "tpl": "premium/petal.html",
        "primary": "#FFF5F5", "secondary": "#FF9898", "accent": "#C02030",
        "text_color": "#380008",
        "heading_font": "Great Vibes", "body_font": "Lato",
    },
    "premium-6": {
        "tpl": "premium/petal.html",
        "primary": "#FFF8FC", "secondary": "#FFC8E4", "accent": "#D04890",
        "text_color": "#400030",
        "heading_font": "Great Vibes", "body_font": "Lato",
    },

    # ── PREMIUM / LACE  (3 color variants) ───────────────────────────────────
    "premium-7": {
        "tpl": "premium/lace.html",
        "primary": "#FFFDF8", "secondary": "#F0E0C0", "accent": "#A87840",
        "text_color": "#3A2A10",
        "heading_font": "Cormorant Garamond", "body_font": "Montserrat",
        "lace_color": "#E8D0A8",
    },
    "premium-8": {
        "tpl": "premium/lace.html",
        "primary": "#FFF8FC", "secondary": "#F0D0E8", "accent": "#A84870",
        "text_color": "#380020",
        "heading_font": "Cormorant Garamond", "body_font": "Montserrat",
        "lace_color": "#E0B8D0",
    },
    "premium-9": {
        "tpl": "premium/lace.html",
        "primary": "#F8F8F8", "secondary": "#E4E4E4", "accent": "#686868",
        "text_color": "#181818",
        "heading_font": "Cormorant Garamond", "body_font": "Montserrat",
        "lace_color": "#C8C8C8",
    },

    # ── PREMIUM / STARLIGHT  (3 color variants, all dark) ────────────────────
    "premium-10": {
        "tpl": "premium/starlight.html",
        "primary": "#080818", "secondary": "#141430", "accent": "#FFD700",
        "text_color": "#F0E8C8",
        "heading_font": "Crimson Text", "body_font": "Quattrocento Sans",
        "particle_color": "#FFD700",
    },
    "premium-11": {
        "tpl": "premium/starlight.html",
        "primary": "#060818", "secondary": "#10142C", "accent": "#A0B8FF",
        "text_color": "#E0E8FF",
        "heading_font": "Crimson Text", "body_font": "Quattrocento Sans",
        "particle_color": "#A0B8FF",
    },
    "premium-12": {
        "tpl": "premium/starlight.html",
        "primary": "#100818", "secondary": "#1A1028", "accent": "#D870FF",
        "text_color": "#F0D8FF",
        "heading_font": "Crimson Text", "body_font": "Quattrocento Sans",
        "particle_color": "#D870FF",
    },

    # ── PREMIUM / SCROLL  (3 color variants) ─────────────────────────────────
    "premium-13": {
        "tpl": "premium/scroll.html",
        "primary": "#FDF5F0", "secondary": "#ECC0B0", "accent": "#C06848",
        "text_color": "#381808",
        "heading_font": "Libre Baskerville", "body_font": "Raleway",
    },
    "premium-14": {
        "tpl": "premium/scroll.html",
        "primary": "#F5FAF5", "secondary": "#B8D8B0", "accent": "#507840",
        "text_color": "#182810",
        "heading_font": "Libre Baskerville", "body_font": "Raleway",
    },
    "premium-15": {
        "tpl": "premium/scroll.html",
        "primary": "#F8F5FF", "secondary": "#D8C8F0", "accent": "#7050C8",
        "text_color": "#201050",
        "heading_font": "Libre Baskerville", "body_font": "Raleway",
    },

    # ── LUXURY / CINEMATIC  (4 variants, all dark) ───────────────────────────
    "luxury-1": {
        "tpl": "luxury/cinematic.html",
        "bg": "#080800", "secondary": "#140E00", "accent": "#FFD700",
        "text_color": "#F0E8C8", "highlight": "#B8860B",
        "heading_font": "Cinzel Decorative", "body_font": "Raleway",
        "confetti_colors": "['#D4AF37','#FFD700','#B8860B','#F5E6CC']",
    },
    "luxury-2": {
        "tpl": "luxury/cinematic.html",
        "bg": "#0A0008", "secondary": "#180010", "accent": "#FF90C0",
        "text_color": "#FFE8F0", "highlight": "#C04880",
        "heading_font": "Cinzel Decorative", "body_font": "Raleway",
        "confetti_colors": "['#FF90C0','#FFB8D0','#E87090','#C04880']",
    },
    "luxury-3": {
        "tpl": "luxury/cinematic.html",
        "bg": "#000810", "secondary": "#001020", "accent": "#90C8FF",
        "text_color": "#E0EEFF", "highlight": "#4880C0",
        "heading_font": "Cinzel Decorative", "body_font": "Raleway",
        "confetti_colors": "['#90C8FF','#B0D8FF','#6090D0','#4880C0']",
    },
    "luxury-4": {
        "tpl": "luxury/cinematic.html",
        "bg": "#0A0A0A", "secondary": "#181818", "accent": "#E8E8E8",
        "text_color": "#FFFFFF", "highlight": "#A0A0A0",
        "heading_font": "Cinzel Decorative", "body_font": "Raleway",
        "confetti_colors": "['#E0E0E0','#C0C0C0','#A0A0A0','#808080']",
    },

    # ── LUXURY / CRYSTAL  (4 variants) ───────────────────────────────────────
    "luxury-5": {
        "tpl": "luxury/crystal.html",
        "bg": "#F0FBFF", "secondary": "#D8F0FF", "accent": "#4898C8",
        "text_color": "#082038",
        "heading_font": "Josefin Slab", "body_font": "Josefin Sans",
        "particle_color": "#90C8F0",
        "ornament_color": "#4898C8",
    },
    "luxury-6": {
        "tpl": "luxury/crystal.html",
        "bg": "#FFFFFF", "secondary": "#F0E8FF", "accent": "#9860D8",
        "text_color": "#180828",
        "heading_font": "Josefin Slab", "body_font": "Josefin Sans",
        "particle_color": "#D0A8FF",
        "ornament_color": "#9860D8",
    },
    "luxury-7": {
        "tpl": "luxury/crystal.html",
        "bg": "#F8F8FF", "secondary": "#E8ECFF", "accent": "#6070C8",
        "text_color": "#0A1038",
        "heading_font": "Josefin Slab", "body_font": "Josefin Sans",
        "particle_color": "#A8B8FF",
        "ornament_color": "#6070C8",
    },
    "luxury-8": {
        "tpl": "luxury/crystal.html",
        "bg": "#FFF8F0", "secondary": "#FFE8D0", "accent": "#C07038",
        "text_color": "#280E00",
        "heading_font": "Josefin Slab", "body_font": "Josefin Sans",
        "particle_color": "#F0B880",
        "ornament_color": "#C07038",
    },

    # ── LUXURY / ROYAL  (4 variants, all dark) ───────────────────────────────
    "luxury-9": {
        "tpl": "luxury/royal.html",
        "bg": "#180018", "secondary": "#280028", "accent": "#FFD700",
        "text_color": "#F0E8C8",
        "heading_font": "Cinzel", "body_font": "Cormorant Garamond",
        "ornament_color": "#B8860B",
    },
    "luxury-10": {
        "tpl": "luxury/royal.html",
        "bg": "#001800", "secondary": "#002800", "accent": "#FFD700",
        "text_color": "#E8F0C8",
        "heading_font": "Cinzel", "body_font": "Cormorant Garamond",
        "ornament_color": "#B8860B",
    },
    "luxury-11": {
        "tpl": "luxury/royal.html",
        "bg": "#180000", "secondary": "#280000", "accent": "#FFD700",
        "text_color": "#F0E0C8",
        "heading_font": "Cinzel", "body_font": "Cormorant Garamond",
        "ornament_color": "#B8860B",
    },
    "luxury-12": {
        "tpl": "luxury/royal.html",
        "bg": "#000818", "secondary": "#001028", "accent": "#FFD700",
        "text_color": "#C8E0F0",
        "heading_font": "Cinzel", "body_font": "Cormorant Garamond",
        "ornament_color": "#B8860B",
    },

    # ── LUXURY / MIDNIGHT  (4 variants, all dark) ────────────────────────────
    "luxury-13": {
        "tpl": "luxury/midnight.html",
        "bg": "#030310", "secondary": "#08081E", "accent": "#7080B0",
        "text_color": "#C0C8E0",
        "heading_font": "Playfair Display", "body_font": "Open Sans",
        "star_color": "#A0B0FF",
    },
    "luxury-14": {
        "tpl": "luxury/midnight.html",
        "bg": "#0A0318", "secondary": "#140528", "accent": "#B050D8",
        "text_color": "#E0C8F8",
        "heading_font": "Playfair Display", "body_font": "Open Sans",
        "star_color": "#D880FF",
    },
    "luxury-15": {
        "tpl": "luxury/midnight.html",
        "bg": "#021008", "secondary": "#041A0A", "accent": "#40B068",
        "text_color": "#C0E8CC",
        "heading_font": "Playfair Display", "body_font": "Open Sans",
        "star_color": "#70F098",
    },
    "luxury-16": {
        "tpl": "luxury/midnight.html",
        "bg": "#0E0800", "secondary": "#181200", "accent": "#C09030",
        "text_color": "#F0E0C0",
        "heading_font": "Playfair Display", "body_font": "Open Sans",
        "star_color": "#FFD078",
    },

    # ── LUXURY / DIAMOND  (4 variants) ───────────────────────────────────────
    "luxury-17": {
        "tpl": "luxury/diamond.html",
        "bg": "#FFFEF8", "secondary": "#FFF8E0", "accent": "#B8860B",
        "text_color": "#3A2800",
        "heading_font": "Cinzel Decorative", "body_font": "Cormorant Garamond",
        "shimmer_colors": "#b8860b,#ffd700,#daa520,#f0d060,#b8860b",
        "confetti_colors": "['#D4AF37','#FFD700','#B8860B','#F5E6CC','#FFB6C1']",
    },
    "luxury-18": {
        "tpl": "luxury/diamond.html",
        "bg": "#FFF5F8", "secondary": "#FFE8EE", "accent": "#B85878",
        "text_color": "#380018",
        "heading_font": "Cinzel Decorative", "body_font": "Cormorant Garamond",
        "shimmer_colors": "#b85878,#f090b0,#e070a0,#f090b0,#b85878",
        "confetti_colors": "['#F090B0','#FFB8D0','#E87090','#FFD4E0']",
    },
    "luxury-19": {
        "tpl": "luxury/diamond.html",
        "bg": "#F8FCFF", "secondary": "#E8F4FF", "accent": "#5888C0",
        "text_color": "#001830",
        "heading_font": "Cinzel Decorative", "body_font": "Cormorant Garamond",
        "shimmer_colors": "#5888c0,#88b0e8,#a0c8ff,#88b0e8,#5888c0",
        "confetti_colors": "['#88B0E8','#A0C8FF','#C0D8FF','#5888C0']",
    },
    "luxury-20": {
        "tpl": "luxury/diamond.html",
        "bg": "#F8FFF8", "secondary": "#E8FFE8", "accent": "#388858",
        "text_color": "#001E10",
        "heading_font": "Cinzel Decorative", "body_font": "Cormorant Garamond",
        "shimmer_colors": "#388858,#58a878,#78c898,#58a878,#388858",
        "confetti_colors": "['#58A878','#78C898','#A0E8B0','#388858']",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

def generate(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    tpl_root = Path(__file__).parent / "jinja_templates"
    env = Environment(
        loader=FileSystemLoader(str(tpl_root)),
        autoescape=select_autoescape([]),  # raw HTML output — we trust our templates
        trim_blocks=True,
        lstrip_blocks=True,
    )

    ok = 0
    errors = []

    for template_id, cfg in CONFIGS.items():
        tpl_path = cfg["tpl"]
        try:
            tpl = env.get_template(tpl_path)
        except Exception as e:
            errors.append(f"  [LOAD ERROR] {template_id} ({tpl_path}): {e}")
            continue

        # Merge sample data + design config, excluding internal 'tpl' key
        context = {**SAMPLE, **{k: v for k, v in cfg.items() if k != "tpl"}}

        try:
            html = tpl.render(**context)
        except Exception as e:
            errors.append(f"  [RENDER ERROR] {template_id}: {e}")
            continue

        out_file = output_dir / f"{template_id}.html"
        out_file.write_text(html, encoding="utf-8")
        print(f"  OK  {template_id:12s}  ->  {out_file.name}")
        ok += 1

    print("\n" + "-" * 60)
    print(f"Generated {ok}/{len(CONFIGS)} templates -> {output_dir}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(e)
    else:
        print("All templates generated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Generate wedding invitation HTML templates.")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent.parent.parent / "apps" / "frontend" / "public" / "templates"),
        help="Output directory for generated HTML files",
    )
    args = parser.parse_args()
    output_dir = Path(args.output).resolve()

    print("\nWedding Invitation Template Generator")
    print("-" * 60)
    print(f"Templates : {len(CONFIGS)}")
    print(f"Output    : {output_dir}\n")

    generate(output_dir)


if __name__ == "__main__":
    main()
