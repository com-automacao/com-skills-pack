#!/usr/bin/env python3
"""Instala as skills avulsas do pack em ~/.claude/skills.

Uso:
    python scripts/install.py --dry-run     # mostra o que faria
    python scripts/install.py               # instala, pulando o que ja existe
    python scripts/install.py --force       # substitui, guardando backup
    python scripts/install.py --dest .claude/skills   # instala so neste projeto

Skills de plugins (engineering, data, design, base44, ruflo, scroll-craft) e as do
ai-memory nao sao instaladas aqui: use o plugin ou o programa oficial (veja o README).
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "packs"

# pasta de origem dentro de packs/ -> cada subpasta com SKILL.md vira uma skill
GROUPS = [
    "agent-skills/skills",
    "gsap-skills/skills",
    "genjutsu/skills",
    "motion-design/skills",
    "mattpocock-skills/skills/engineering",
    "anthropic-skills/skills",
    "perfex-crm-skills/skills",
    "codeigniter-skills/skills",
    "find-skills/skills",
    "com-automacao/skills",
]
# skills que ficam na raiz do proprio pacote
ROOT_SKILLS = {"design-dna": "design-dna", "img2threejs": "img2threejs"}
# pastas de apoio referenciadas por caminho relativo (../../references)
SUPPORT = {"agent-skills/references": "../references"}


def plan():
    items = []
    for g in GROUPS:
        base = ROOT / g
        for d in sorted(p for p in base.iterdir() if p.is_dir()):
            # _jutsu do genjutsu nao tem SKILL.md proprio, mas as skills dependem dele
            if (d / "SKILL.md").exists() or d.name.startswith("_"):
                items.append((d, d.name))
    for src, name in ROOT_SKILLS.items():
        items.append((ROOT / src, name))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=str(Path.home() / ".claude" / "skills"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    dest = Path(a.dest).expanduser().resolve()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    installed = skipped = 0

    jobs = [(s, dest / n) for s, n in plan()]
    jobs += [(ROOT / s, (dest / rel).resolve()) for s, rel in SUPPORT.items()]
    for src, target in jobs:
        if target.exists() and not a.force:
            print(f"  pula      {target.name} (ja existe; use --force)")
            skipped += 1
            continue
        print(f"  instala   {target.name}")
        installed += 1
        if a.dry_run:
            continue
        if target.exists():
            shutil.move(str(target), f"{target}.bak-{stamp}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, target)

    verb = "seriam instaladas" if a.dry_run else "instaladas"
    print(f"\n{installed} {verb}, {skipped} puladas. Destino: {dest}")
    if not a.dry_run and installed:
        print("Reinicie o Claude Code para carregar as skills.")


if __name__ == "__main__":
    main()
