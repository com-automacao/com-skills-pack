#!/usr/bin/env python3
"""Sincroniza o pack com os repositorios de origem e detecta mudancas fora do padrao.

Uso:
    python scripts/sync.py                 # aplica so as fontes sem bloqueio (padrao)
    python scripts/sync.py --apply all     # aplica tudo, inclusive o que gerou bloqueio
    python scripts/sync.py --dry-run       # so relata, nao grava nada
    python scripts/sync.py --only gsap-skills,genjutsu

Niveis de achado:
    bloqueio -> a fonte NAO e atualizada no modo padrao; vira alerta para revisao humana
    aviso    -> a fonte e atualizada, mas o achado entra no alerta
    info     -> so registrado no STATUS.md / resumo do commit

Saidas:
    state/lock.json        commit e hash de cada arquivo acompanhado
    STATUS.md              painel de situacao (gerado)
    THIRD_PARTY_NOTICES.md creditos e licencas (gerado)
    --report <arquivo.md>  relatorio da execucao (usado no texto do alerta)
    GITHUB_OUTPUT          changed / has_block / has_warn (quando roda no Actions)

Dependencias: Python 3.9+, git, PyYAML.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PACKS = ROOT / "packs"
LOCK = ROOT / "state" / "lock.json"

BLOCK, WARN, INFO = "bloqueio", "aviso", "info"

LICENSE_NAMES = {"license", "license.txt", "license.md", "licence", "copying"}
EXEC_EXT = {
    ".sh", ".bash", ".zsh", ".ps1", ".psm1", ".bat", ".cmd", ".exe", ".dll", ".so",
    ".dylib", ".js", ".mjs", ".cjs", ".ts", ".py", ".rb", ".pl", ".jar", ".bin",
    ".msi", ".vbs", ".scr", ".wasm", ".com", ".apk",
}
CODE_EXT = EXEC_EXT - {".exe", ".dll", ".so", ".dylib", ".jar", ".bin", ".msi", ".scr", ".wasm", ".com", ".apk"}
MEDIA_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".otf", ".mp4", ".webm", ".mov", ".pdf", ".glb", ".gltf", ".hdr", ".mp3", ".wav",
}
MAX_FILE_BYTES = 2 * 1024 * 1024

# (codigo, nivel, regex, so_em_codigo, explicacao)
PATTERNS = [
    ("PIPE_TO_SHELL", BLOCK, r"\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b", False,
     "baixa um script da internet e executa direto"),
    ("DOWNLOAD_EXEC_PS", BLOCK, r"\b(iwr|irm|invoke-webrequest|invoke-restmethod|downloadstring)\b[^\n]*\|\s*(iex|invoke-expression)\b", False,
     "baixa e executa codigo PowerShell"),
    ("INVOKE_EXPRESSION", BLOCK, r"\binvoke-expression\b|\biex\s*[(\$]", False,
     "executa texto como codigo PowerShell"),
    ("BASE64_EXEC", BLOCK, r"base64\s+(-d|--decode)[^\n]*\|\s*(ba)?sh|frombase64string", False,
     "decodifica conteudo oculto em base64"),
    ("DESTRUCTIVE_RM", BLOCK, r"\brm\s+-(rf|fr)\s+(/|~|\$home|\*)(\s|$|[\"'])", False,
     "apaga pastas inteiras"),
    ("CLAUDE_SETTINGS", BLOCK, r"\.claude[\\/]settings(\.local)?\.json|permissions\.allow|dangerously-?skip-?permissions", False,
     "mexe em permissoes ou configuracao do Claude Code"),
    ("PROMPT_INJECTION", BLOCK,
     r"ignore (all |any )?(the )?(previous|prior|above) instructions|disregard (all )?(the )?(previous|prior|system)"
     r"|do not (tell|inform|notify) the user|without (telling|asking|informing) the user|hide (this|it) from the user", False,
     "texto que tenta manipular o agente ou esconder acoes do usuario"),
    ("HIDDEN_UNICODE", BLOCK, "[​-‏‪-‮⁦-⁩]", False,
     "caracteres invisiveis ou de inversao de texto"),
    ("SECRET", BLOCK,
     r"AKIA[0-9A-Z]{16}|sk-ant-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY", False,
     "chave ou token embutido"),
    ("SENSITIVE_FILES", BLOCK, r"\.ssh[\\/]id_|\.aws[\\/]credentials|wallet\.dat|seed phrase|keychain", False,
     "acessa arquivos de credenciais"),
    ("AUTO_INSTALL", WARN, r"\bnpx\s+(-y|--yes)\b|\bnpm\s+(i|install)\s+(-g|--global)\b|\bpip3?\s+install\b", False,
     "instala pacotes automaticamente"),
    ("DYNAMIC_EXEC", WARN, r"\beval\s*\(|\bnew Function\s*\(|child_process|subprocess\.(run|popen|call)|\bos\.system\s*\(", True,
     "executa comandos ou codigo dinamico"),
]
PATTERNS = [(c, lvl, re.compile(rx, re.I), code, why) for c, lvl, rx, code, why in PATTERNS]
URL_RX = re.compile(r"https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})")

LEVEL_ORDER = {BLOCK: 0, WARN: 1, INFO: 2}


# ---------------------------------------------------------------- utilidades

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def run(cmd, cwd=None) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{r.stderr.strip()}")
    return r.stdout


def token() -> str | None:
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    try:
        return run(["gh", "auth", "token"]).strip() or None
    except Exception:
        return None


TOKEN = token()


def api(path: str):
    """GET na API do GitHub. Devolve (status, json|None)."""
    req = urllib.request.Request(f"https://api.github.com/{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "com-skills-pack-sync")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_text(p: Path) -> str:
    try:
        return p.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")
    except FileNotFoundError:
        return ""


def is_binary(p: Path) -> bool:
    return b"\x00" in p.read_bytes()[:8192]


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
        if isinstance(data, dict):
            return data
    except yaml.YAMLError:
        pass
    # YAML invalido (ex.: "a: b" sem aspas na descricao): o Claude Code ainda le a skill,
    # entao extraimos nome e descricao linha a linha em vez de concluir que o nome sumiu
    out = {}
    for line in m.group(1).split("\n"):
        mm = re.match(r"^(name|description)\s*:\s*(.*)$", line)
        if mm:
            out[mm.group(1)] = mm.group(2).strip().strip("\"'")
    return out


def set_frontmatter_fields(text: str, fields: dict) -> str:
    """Troca campos do frontmatter preservando o resto do arquivo byte a byte."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return text
    lines = m.group(1).split("\n")
    for key, value in fields.items():
        new = f"{key}: {json.dumps(value, ensure_ascii=False)}"
        out, i, done = [], 0, False
        while i < len(lines):
            if re.match(rf"^{re.escape(key)}\s*:", lines[i]):
                out.append(new)
                done = True
                i += 1
                while i < len(lines) and (lines[i].startswith((" ", "\t")) or lines[i] == ""):
                    i += 1
                continue
            out.append(lines[i])
            i += 1
        if not done:
            out.append(new)
        lines = out
    return "---\n" + "\n".join(lines) + "\n---" + text[m.end():]


def file_map(base: Path, rels: list[str]) -> dict[str, str]:
    """{caminho relativo: sha256} de tudo sob os caminhos acompanhados."""
    out = {}
    for rel in rels:
        p = base / rel
        if p.is_file():
            out[rel] = sha256(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and ".git" not in f.parts:
                    out[f.relative_to(base).as_posix()] = sha256(f)
    return out


# ---------------------------------------------------------------- download

def sparse_clone(repo: str, branch: str, paths: list[str], dest: Path) -> str:
    url = f"https://github.com/{repo}.git"
    if TOKEN and os.environ.get("GITHUB_ACTIONS"):
        url = f"https://x-access-token:{TOKEN}@github.com/{repo}.git"
    run(["git", "-c", "core.autocrlf=false", "clone", "--quiet", "--depth", "1", "--filter=blob:none",
         "--sparse", "--branch", branch, url, str(dest)])
    run(["git", "-c", "core.autocrlf=false", "sparse-checkout", "set", "--no-cone", *[f"/{p}" for p in paths]], cwd=dest)
    return run(["git", "rev-parse", "HEAD"], cwd=dest).strip()


def list_dirs(clone: Path, watch: str) -> list[str]:
    try:
        out = run(["git", "ls-tree", "-d", "--name-only", f"HEAD:{watch}"], cwd=clone)
    except RuntimeError:
        return []
    return [f"{watch}/{d}" for d in out.split() if d]


def compare_patches(repo: str, old: str, new: str):
    """Linhas adicionadas por arquivo via API compare. None se a historia foi reescrita."""
    status, data = api(f"repos/{repo}/compare/{old}...{new}")
    if status == 404 or not data:
        return None, None
    added = {}
    for f in data.get("files", []):
        lines = [l[1:] for l in (f.get("patch") or "").split("\n") if l.startswith("+") and not l.startswith("+++")]
        added[f["filename"]] = lines
    return data.get("status"), added


# ---------------------------------------------------------------- analise

class Finding(dict):
    def __init__(self, level, code, msg, where=""):
        super().__init__(level=level, code=code, msg=msg, where=where)


def scan_lines(rel: str, lines: list[str], findings: list):
    ext = Path(rel).suffix.lower()
    seen = set()
    for n, line in enumerate(lines, 1):
        for code, level, rx, only_code, why in PATTERNS:
            if only_code and ext not in CODE_EXT:
                continue
            if rx.search(line) and code not in seen:
                seen.add(code)
                snippet = line.strip()[:160]
                findings.append(Finding(level, code, f"{why}: `{snippet}`", rel))


def added_lines(old: str, new: str) -> list[str]:
    sm = difflib.SequenceMatcher(None, old.split("\n"), new.split("\n"), autojunk=False)
    out = []
    for tag, _, _, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            out.extend(new.split("\n")[j1:j2])
    return out


def domains(text: str) -> set[str]:
    return {d.lower() for d in URL_RX.findall(text)}


def analyze_source(sid, src, lock_entry, clone, head, findings, notes):
    """Compara a copia nova com a anterior e preenche findings/notes."""
    repo, paths, mode = src["repo"], src["paths"], src.get("mode", "vendor")
    old_files = (lock_entry or {}).get("files", {})
    new_files = file_map(clone, paths)
    baseline = not lock_entry

    for rel in paths:
        if not (clone / rel).exists():
            findings.append(Finding(BLOCK, "PATH_MISSING", "caminho sumiu na origem (removido ou renomeado)", rel))

    added = sorted(set(new_files) - set(old_files))
    removed = sorted(set(old_files) - set(new_files))
    changed = sorted(f for f in set(new_files) & set(old_files) if new_files[f] != old_files[f])
    notes["added"], notes["removed"], notes["changed"] = added, removed, changed
    if baseline:
        return

    # remocao em massa por caminho acompanhado
    for rel in paths:
        before = [f for f in old_files if f == rel or f.startswith(rel + "/")]
        gone = [f for f in before if f in removed]
        if len(before) > 3 and len(gone) / len(before) > 0.5:
            findings.append(Finding(BLOCK, "MASS_DELETE", f"{len(gone)} de {len(before)} arquivos removidos", rel))

    # linhas novas: copia local (vendor) ou patches da API (link)
    patches = None
    if mode == "link":
        _, patches = compare_patches(repo, lock_entry["commit"], head)
    old_domains = set()
    for rel in old_files:
        if mode == "vendor":
            old_domains |= domains(read_text(PACKS / sid / rel))

    for rel in added + changed:
        p = clone / rel
        ext = p.suffix.lower()
        size = p.stat().st_size
        if size > MAX_FILE_BYTES:
            findings.append(Finding(BLOCK, "LARGE_FILE", f"arquivo de {size // 1024} KB", rel))
        if rel in added and ext in EXEC_EXT:
            findings.append(Finding(BLOCK, "NEW_EXECUTABLE", f"novo script/executavel ({ext})", rel))
        elif rel in changed and ext in EXEC_EXT:
            findings.append(Finding(WARN, "SCRIPT_CHANGED", "script existente foi alterado", rel))
        if ext not in MEDIA_EXT and is_binary(p):
            findings.append(Finding(BLOCK, "NEW_BINARY", "arquivo binario nao reconhecido", rel))
            continue
        if Path(rel).name.lower() in LICENSE_NAMES:
            findings.append(Finding(BLOCK, "LICENSE_TEXT_CHANGED", "texto da licenca mudou", rel))
        new_text = read_text(p)
        if mode == "vendor":
            old_text = read_text(PACKS / sid / rel) if rel in changed else ""
            lines = added_lines(old_text, new_text)
        else:
            lines = (patches or {}).get(rel, new_text.split("\n"))
        scan_lines(rel, lines, findings)
        if mode == "vendor":
            new_d = domains("\n".join(lines)) - old_domains
            if new_d:
                findings.append(Finding(WARN, "NEW_DOMAIN", "novos enderecos externos: " + ", ".join(sorted(new_d)[:8]), rel))
        if Path(rel).name == "SKILL.md" and rel in changed and mode == "vendor":
            old_text = read_text(PACKS / sid / rel)
            fo, fn = frontmatter(old_text), frontmatter(new_text)
            if fo.get("name") != fn.get("name"):
                findings.append(Finding(BLOCK, "NAME_CHANGED", f"nome mudou de `{fo.get('name')}` para `{fn.get('name')}`", rel))
            if fo.get("description") != fn.get("description"):
                findings.append(Finding(INFO, "DESCRIPTION_CHANGED", "descricao (gatilho de uso) mudou", rel))
            ratio = difflib.SequenceMatcher(None, old_text, new_text, autojunk=False).ratio()
            if ratio < 0.35:
                findings.append(Finding(WARN, "BIG_REWRITE", f"SKILL.md reescrito ({int(ratio * 100)}% igual ao anterior)", rel))


# ---------------------------------------------------------------- execucao

def process(sid, src, lock, overrides, args, report):
    repo, branch, mode = src["repo"], src.get("branch", "main"), src.get("mode", "vendor")
    entry = lock.get(sid)
    findings: list[Finding] = []
    notes: dict = {"repo": repo, "mode": mode}
    report[sid] = {"findings": findings, "notes": notes, "applied": False}

    status, meta = api(f"repos/{repo}")
    if status != 200 or not meta:
        findings.append(Finding(BLOCK, "REPO_GONE", f"repositorio inacessivel (HTTP {status})"))
        return
    if meta["full_name"].lower() != repo.lower():
        findings.append(Finding(BLOCK, "REPO_RENAMED", f"repositorio agora se chama `{meta['full_name']}`; atualize o sources.yaml"))
    if meta.get("archived"):
        findings.append(Finding(WARN, "ARCHIVED", "repositorio arquivado: nao recebera mais atualizacoes"))
    spdx = (meta.get("license") or {}).get("spdx_id") or "NONE"
    expected = src.get("license", "NONE")
    if spdx != expected:
        findings.append(Finding(BLOCK, "LICENSE_CHANGED", f"licenca esperada `{expected}`, encontrada `{spdx}`"))
    notes["license"] = spdx

    with tempfile.TemporaryDirectory(prefix=f"sync-{sid}-") as tmp:
        clone = Path(tmp) / "repo"
        try:
            head = sparse_clone(repo, branch, src["paths"], clone)
        except RuntimeError as e:
            findings.append(Finding(BLOCK, "CLONE_FAILED", str(e).splitlines()[-1][:200]))
            return
        notes["commit"] = head
        notes["previous"] = (entry or {}).get("commit")
        if src.get("watch"):
            tracked = {p for p in src["paths"]}
            fresh = [d for d in list_dirs(clone, src["watch"]) if d not in tracked]
            known = set((entry or {}).get("known_upstream", []))
            notes["upstream_extra"] = fresh
            for d in fresh:
                if entry and d not in known:
                    findings.append(Finding(INFO, "NEW_UPSTREAM_SKILL", "skill nova na origem (nao incluida)", d))

        if entry and entry.get("commit") == head and not args.force:
            notes["unchanged"] = True
            entry["checked_at"] = now()
            return

        if entry and entry.get("commit") and entry["commit"] != head:
            st, _ = compare_patches(repo, entry["commit"], head)
            if st is None or st == "diverged":
                findings.append(Finding(BLOCK, "HISTORY_REWRITTEN", "historico da origem foi reescrito (force-push); commit anterior sumiu"))

        analyze_source(sid, src, entry, clone, head, findings, notes)

        has_block = any(f["level"] == BLOCK for f in findings)
        if args.dry_run or (has_block and args.apply == "safe"):
            if entry:
                entry["checked_at"] = now()
            return

        if mode == "vendor":
            dest = PACKS / sid
            if dest.exists():
                shutil.rmtree(dest)
            for rel in src["paths"]:
                s = clone / rel
                if not s.exists():
                    old = (entry or {}).get("files", {})
                    if any(f == rel or f.startswith(rel + "/") for f in old):
                        findings.append(Finding(WARN, "KEPT_OLD", "caminho ausente na origem; mantida a copia anterior", rel))
                    continue
                d = dest / rel
                d.parent.mkdir(parents=True, exist_ok=True)
                if s.is_dir():
                    shutil.copytree(s, d, ignore=shutil.ignore_patterns(".git"))
                else:
                    shutil.copy2(s, d)
            for rel, fields in (overrides.get(sid) or {}).items():
                skill_md = dest / rel / "SKILL.md"
                if skill_md.exists():
                    raw = skill_md.read_bytes().decode("utf-8")
                    skill_md.write_bytes(set_frontmatter_fields(raw.replace("\r\n", "\n"), fields).encode("utf-8"))
        lock[sid] = {
            "repo": repo,
            "commit": head,
            "license": spdx,
            "checked_at": now(),
            "updated_at": now(),
            "files": file_map(clone, src["paths"]),
            "known_upstream": notes.get("upstream_extra", []),
        }
        report[sid]["applied"] = True


def write_status(cfg, lock, report):
    rows = []
    for sid, src in cfg["sources"].items():
        e = lock.get(sid, {})
        fs = report.get(sid, {}).get("findings", [])
        worst = min((LEVEL_ORDER[f["level"]] for f in fs if f["level"] != INFO), default=None)
        state = {0: "🔴 bloqueado", 1: "🟡 aviso"}.get(worst, "🟢 ok")
        n = len([p for p in src["paths"] if Path(p).name.lower() not in LICENSE_NAMES])
        commit = e.get("commit", "")
        link = f"[`{commit[:7]}`](https://github.com/{src['repo']}/commit/{commit})" if commit else "-"
        modo = "copiado" if src.get("mode", "vendor") == "vendor" else "só link"
        rows.append(f"| `{sid}` | [{src['repo']}](https://github.com/{src['repo']}) | {src.get('license')} | {modo} | {n} | {link} | {e.get('updated_at', '-')} | {state} |")
    extra = []
    for sid, e in lock.items():
        for d in e.get("known_upstream", []):
            extra.append(f"- `{sid}`: [{d}](https://github.com/{e['repo']}/tree/HEAD/{d})")
    text = [
        "# Situação do pack",
        "",
        "_Arquivo gerado por `scripts/sync.py`. Não edite à mão._",
        "",
        f"Última verificação: **{now()}**",
        "",
        "| Fonte | Repositório | Licença | Modo | Itens | Commit | Atualizado em | Estado |",
        "|---|---|---|---|---:|---|---|---|",
        *rows,
        "",
        "## Skills disponíveis na origem e ainda não incluídas",
        "",
        *(extra or ["Nenhuma."]),
        "",
        "Para incluir, acrescente o caminho em `sources.yaml` e rode o sync.",
        "",
    ]
    (ROOT / "STATUS.md").write_text("\n".join(text), encoding="utf-8", newline="\n")


def write_notices(cfg):
    lines = ["# Créditos e licenças", "",
             "Este pack redistribui skills de terceiros sem modificá-las, exceto onde",
             "`sources.yaml` declara um ajuste (`overrides`). Cada pasta em `packs/` mantém a",
             "licença original da sua origem.", "",
             "| Fonte | Autor / repositório | Licença | Arquivo de licença |", "|---|---|---|---|"]
    for sid, src in cfg["sources"].items():
        lic = next((p for p in src["paths"] if Path(p).name.lower() in LICENSE_NAMES), None)
        if src.get("mode") == "link":
            where = "não redistribuído (só link)"
        elif lic:
            where = f"[packs/{sid}/{lic}](packs/{sid}/{lic})"
        else:
            where = "LICENSE.txt dentro de cada skill"
        lines.append(f"| `{sid}` | [{src['repo']}](https://github.com/{src['repo']}) | {src.get('license')} | {where} |")
    lines += ["", "`packs/com-automacao/` contém skills próprias da Com Automação.", ""]
    (ROOT / "THIRD_PARTY_NOTICES.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_report(path, report, blocked_applied):
    out = [f"## Sync de {now()}", ""]
    for level, title in ((BLOCK, "🔴 Bloqueios (não aplicados automaticamente)"), (WARN, "🟡 Avisos (aplicados)")):
        items = [(sid, f) for sid, r in report.items() for f in r["findings"] if f["level"] == level]
        if items:
            out += [f"### {title}", ""]
            for sid, f in items:
                where = f" — `{f['where']}`" if f["where"] else ""
                out.append(f"- **{sid}** · `{f['code']}`{where}: {f['msg']}")
            out.append("")
    upd = []
    for sid, r in report.items():
        n = r["notes"]
        if r["applied"] and not n.get("unchanged"):
            prev, cur = (n.get("previous") or "")[:7], (n.get("commit") or "")[:7]
            rng = f"[{prev}…{cur}](https://github.com/{n['repo']}/compare/{n.get('previous')}...{n.get('commit')})" if prev else cur
            upd.append(f"- **{sid}** {rng}: +{len(n.get('added', []))} / ~{len(n.get('changed', []))} / -{len(n.get('removed', []))} arquivos")
    if upd:
        out += ["### Atualizações aplicadas", "", *upd, ""]
    infos = [(sid, f) for sid, r in report.items() for f in r["findings"] if f["level"] == INFO]
    if infos:
        out += ["### Informativo", ""] + [f"- **{sid}** · {f['msg']} — `{f['where']}`" for sid, f in infos] + [""]
    if not upd and not any(r["findings"] for r in report.values()):
        out.append("Nenhuma mudança nas origens.")
    text = "\n".join(out)
    if path:
        Path(path).write_text(text, encoding="utf-8", newline="\n")
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", choices=["safe", "all"], default="safe")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="reprocessa mesmo sem commit novo")
    ap.add_argument("--only", default="")
    ap.add_argument("--report", default="")
    ap.add_argument("--simulate-alert", action="store_true",
                    help="injeta um achado de teste para conferir o caminho do alerta; nao altera arquivos")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    overrides = cfg.get("overrides") or {}
    only = {s for s in args.only.split(",") if s}
    report: dict = {}

    for sid, src in cfg["sources"].items():
        if only and sid not in only:
            continue
        print(f"-> {sid} ({src['repo']})", flush=True)
        try:
            process(sid, src, lock, overrides, args, report)
        except Exception as e:  # uma fonte com erro nao derruba as outras
            report[sid] = {"findings": [Finding(BLOCK, "SYNC_ERROR", str(e)[:300])], "notes": {"repo": src["repo"]}, "applied": False}
        for f in report[sid]["findings"]:
            print(f"   [{f['level']}] {f['code']} {f['where']} {f['msg'][:120]}")

    if args.simulate_alert:
        sid = next(iter(report), "teste")
        report.setdefault(sid, {"findings": [], "notes": {"repo": "-"}, "applied": False})
        report[sid]["findings"].append(Finding(
            BLOCK, "TESTE", "alerta de teste disparado manualmente. Nenhuma origem mudou; pode fechar esta issue.",
            now()))

    if not args.dry_run:
        LOCK.parent.mkdir(exist_ok=True)
        LOCK.write_text(json.dumps(lock, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        write_status(cfg, lock, report)
        write_notices(cfg)
    text = write_report(args.report, report, args.apply == "all")
    print("\n" + text)

    has_block = any(f["level"] == BLOCK for r in report.values() for f in r["findings"])
    has_warn = any(f["level"] == WARN for r in report.values() for f in r["findings"])
    changed = any(r["applied"] and not r["notes"].get("unchanged") for r in report.values())
    # impressao digital dos achados: evita abrir o mesmo alerta todo dia
    # sem o commit: a mesma pendencia nao pode abrir uma issue nova a cada dia
    # com bloqueio, so os bloqueios contam: um aviso novo nao reabre o mesmo alerta
    lv = {BLOCK} if any(f["level"] == BLOCK for r in report.values() for f in r["findings"]) else {WARN}
    keys = sorted(f"{sid}|{f['code']}|{f['where']}|{f['msg']}"
                  for sid, r in report.items() for f in r["findings"] if f["level"] in lv)
    fingerprint = hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"fingerprint={fingerprint}\n")
            fh.write(f"has_block={'true' if has_block else 'false'}\n")
            fh.write(f"has_warn={'true' if has_warn else 'false'}\n")
            fh.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    sys.exit(main())
