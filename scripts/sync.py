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
from dataclasses import dataclass, field
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
FRONTMATTER_RX = re.compile(r"^---\s*\n(.*?)\n---", re.S)

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
    except urllib.error.URLError:
        return 0, None


def is_transient(status: int) -> bool:
    """Falha passageira do GitHub: sem conexao, limite de uso ou erro do servidor."""
    return status in (0, 403, 429) or status >= 500


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
    m = FRONTMATTER_RX.match(text)
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


def replace_field(lines: list[str], key: str, new: str) -> list[str]:
    """Troca o campo e suas linhas de continuacao; se nao existir, acrescenta no fim."""
    out, skipping, done = [], False, False
    for line in lines:
        if re.match(rf"^{re.escape(key)}\s*:", line):
            out.append(new)
            done = skipping = True
        elif not (skipping and (line.startswith((" ", "\t")) or line == "")):
            out.append(line)
            skipping = False
    return out if done else out + [new]


def set_frontmatter_fields(text: str, fields: dict) -> str:
    """Troca campos do frontmatter preservando o resto do arquivo byte a byte."""
    m = FRONTMATTER_RX.match(text)
    if not m:
        return text
    lines = m.group(1).split("\n")
    for key, value in fields.items():
        lines = replace_field(lines, key, f"{key}: {json.dumps(value, ensure_ascii=False)}")
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
    """(estado, linhas adicionadas por arquivo) via API compare.

    Estado None: a origem nao reconhece o commit anterior (historia reescrita).
    Numero: codigo HTTP de uma falha passageira da API.
    """
    status, data = api(f"repos/{repo}/compare/{old}...{new}")
    if is_transient(status):
        return status, None
    if status != 200 or not data:
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


@dataclass
class Job:
    """Uma fonte sendo processada nesta execucao."""
    sid: str
    src: dict
    entry: dict | None
    findings: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)
    clone: Path | None = None
    head: str = ""
    kept: list = field(default_factory=list)
    postponed: bool = False

    @property
    def vendored(self) -> bool:
        return self.src.get("mode", "vendor") == "vendor"

    @property
    def old_files(self) -> dict:
        return (self.entry or {}).get("files", {})

    def add(self, level, code, msg, where=""):
        self.findings.append(Finding(level, code, msg, where))

    def postpone(self, status: int):
        self.postponed = True
        self.add(INFO, "API_UNAVAILABLE", f"API do GitHub indisponivel (HTTP {status}); nova tentativa no proximo sync")

    def touch(self):
        if self.entry:
            self.entry["checked_at"] = now()

    def pack_text(self, rel: str) -> str:
        return read_text(PACKS / self.sid / rel)


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


def diff_files(old: dict, new: dict):
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(f for f in set(new) & set(old) if new[f] != old[f])
    return added, removed, changed


def check_paths_exist(job: Job):
    for rel in job.src["paths"]:
        if not (job.clone / rel).exists():
            job.add(BLOCK, "PATH_MISSING", "caminho sumiu na origem (removido ou renomeado)", rel)


def check_mass_delete(job: Job, removed: list[str]):
    for rel in job.src["paths"]:
        before = [f for f in job.old_files if is_under(f, rel)]
        gone = [f for f in before if f in removed]
        if len(before) > 3 and len(gone) / len(before) > 0.5:
            job.add(BLOCK, "MASS_DELETE", f"{len(gone)} de {len(before)} arquivos removidos", rel)


def check_file_traits(job: Job, rel: str, is_new: bool):
    p = job.clone / rel
    ext = p.suffix.lower()
    size = p.stat().st_size
    if size > MAX_FILE_BYTES:
        job.add(BLOCK, "LARGE_FILE", f"arquivo de {size // 1024} KB", rel)
    if ext in EXEC_EXT and is_new:
        job.add(BLOCK, "NEW_EXECUTABLE", f"novo script/executavel ({ext})", rel)
    elif ext in EXEC_EXT:
        job.add(WARN, "SCRIPT_CHANGED", "script existente foi alterado", rel)


def known_domains(job: Job) -> set[str]:
    if not job.vendored:
        return set()
    return set().union(*(domains(job.pack_text(rel)) for rel in job.old_files))


def lines_to_scan(job: Job, rel: str, is_new: bool, new_text: str, patches) -> list[str]:
    """Linhas novas: pela copia anterior (vendor) ou pelos patches da API (link)."""
    if job.vendored:
        return added_lines("" if is_new else job.pack_text(rel), new_text)
    return (patches or {}).get(rel, new_text.split("\n"))


def check_new_domains(job: Job, rel: str, lines: list[str], old_domains: set[str]):
    new_d = domains("\n".join(lines)) - old_domains
    if new_d:
        job.add(WARN, "NEW_DOMAIN", "novos enderecos externos: " + ", ".join(sorted(new_d)[:8]), rel)


def check_skill_md(job: Job, rel: str, new_text: str):
    old_text = job.pack_text(rel)
    fo, fn = frontmatter(old_text), frontmatter(new_text)
    if fo.get("name") != fn.get("name"):
        job.add(BLOCK, "NAME_CHANGED", f"nome mudou de `{fo.get('name')}` para `{fn.get('name')}`", rel)
    if fo.get("description") != fn.get("description"):
        job.add(INFO, "DESCRIPTION_CHANGED", "descricao (gatilho de uso) mudou", rel)
    ratio = difflib.SequenceMatcher(None, old_text, new_text, autojunk=False).ratio()
    if ratio < 0.35:
        job.add(WARN, "BIG_REWRITE", f"SKILL.md reescrito ({int(ratio * 100)}% igual ao anterior)", rel)


def analyze_file(job: Job, rel: str, is_new: bool, patches, old_domains: set[str]):
    p = job.clone / rel
    check_file_traits(job, rel, is_new)
    if p.suffix.lower() not in MEDIA_EXT and is_binary(p):
        job.add(BLOCK, "NEW_BINARY", "arquivo binario nao reconhecido", rel)
        return
    if Path(rel).name.lower() in LICENSE_NAMES:
        job.add(BLOCK, "LICENSE_TEXT_CHANGED", "texto da licenca mudou", rel)
    new_text = read_text(p)
    lines = lines_to_scan(job, rel, is_new, new_text, patches)
    scan_lines(rel, lines, job.findings)
    if job.vendored:
        check_new_domains(job, rel, lines, old_domains)
        if Path(rel).name == "SKILL.md" and not is_new:
            check_skill_md(job, rel, new_text)


def analyze_source(job: Job):
    """Compara a copia nova com a anterior e preenche findings/notes."""
    check_paths_exist(job)
    added, removed, changed = diff_files(job.old_files, file_map(job.clone, job.src["paths"]))
    job.notes.update(added=added, removed=removed, changed=changed)
    if not job.entry:
        return
    check_mass_delete(job, removed)
    patches = None
    if not job.vendored:
        _, patches = compare_patches(job.src["repo"], job.entry["commit"], job.head)
    old_domains = known_domains(job)
    for rel in added:
        analyze_file(job, rel, True, patches, old_domains)
    for rel in changed:
        analyze_file(job, rel, False, patches, old_domains)


# ---------------------------------------------------------------- execucao

def check_repo(job: Job) -> str | None:
    """Confere o repositorio na API. Devolve a licenca, ou None se ele esta inacessivel."""
    repo = job.src["repo"]
    status, meta = api(f"repos/{repo}")
    if is_transient(status):
        job.postpone(status)
        return None
    if status != 200 or not meta:
        job.add(BLOCK, "REPO_GONE", f"repositorio inacessivel (HTTP {status})")
        return None
    if meta["full_name"].lower() != repo.lower():
        job.add(BLOCK, "REPO_RENAMED", f"repositorio agora se chama `{meta['full_name']}`; atualize o sources.yaml")
    if meta.get("archived"):
        job.add(WARN, "ARCHIVED", "repositorio arquivado: nao recebera mais atualizacoes")
    spdx = (meta.get("license") or {}).get("spdx_id") or "NONE"
    expected = job.src.get("license", "NONE")
    if spdx != expected:
        job.add(BLOCK, "LICENSE_CHANGED", f"licenca esperada `{expected}`, encontrada `{spdx}`")
    job.notes["license"] = spdx
    return spdx


def fetch(job: Job, tmp: str) -> bool:
    job.clone = Path(tmp) / "repo"
    try:
        job.head = sparse_clone(job.src["repo"], job.src.get("branch", "main"), job.src["paths"], job.clone)
    except RuntimeError as e:
        job.add(BLOCK, "CLONE_FAILED", str(e).splitlines()[-1][:200])
        return False
    job.notes["commit"] = job.head
    job.notes["previous"] = (job.entry or {}).get("commit")
    return True


def note_upstream_skills(job: Job):
    watch = job.src.get("watch")
    if not watch:
        return
    fresh = [d for d in list_dirs(job.clone, watch) if d not in job.src["paths"]]
    known = set((job.entry or {}).get("known_upstream", []))
    job.notes["upstream_extra"] = fresh
    for d in fresh:
        if job.entry and d not in known:
            job.add(INFO, "NEW_UPSTREAM_SKILL", "skill nova na origem (nao incluida)", d)


def is_unchanged(job: Job, args) -> bool:
    return bool(job.entry) and job.entry.get("commit") == job.head and not args.force


def check_history(job: Job):
    previous = (job.entry or {}).get("commit")
    if not previous or previous == job.head:
        return
    status, _ = compare_patches(job.src["repo"], previous, job.head)
    if isinstance(status, int):
        job.postpone(status)
    elif status is None or status == "diverged":
        job.add(BLOCK, "HISTORY_REWRITTEN", "historico da origem foi reescrito (force-push); commit anterior sumiu")


def held_back(job: Job, args) -> bool:
    return args.dry_run or (args.apply == "safe" and any(f["level"] == BLOCK for f in job.findings))


def copy_any(source: Path, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, ignore=shutil.ignore_patterns(".git"))
    else:
        shutil.copy2(source, target)


def is_under(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def copy_path(job: Job, rel: str, dest: Path, stage: Path):
    if (job.clone / rel).exists():
        copy_any(job.clone / rel, stage / rel)
    elif any(is_under(f, rel) for f in job.old_files):
        job.add(WARN, "KEPT_OLD", "caminho ausente na origem; mantida a copia anterior", rel)
        job.kept.append(rel)
        if (dest / rel).exists():
            copy_any(dest / rel, stage / rel)


def apply_overrides(dest: Path, overrides: dict):
    for rel, fields in overrides.items():
        skill_md = dest / rel / "SKILL.md"
        if skill_md.exists():
            raw = skill_md.read_bytes().decode("utf-8")
            skill_md.write_bytes(set_frontmatter_fields(raw.replace("\r\n", "\n"), fields).encode("utf-8"))


def vendor_files(job: Job, overrides: dict):
    """Monta a copia nova ao lado e so entao troca: um erro no meio nao perde a anterior."""
    dest = PACKS / job.sid
    stage = PACKS / f".stage-{job.sid}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    for rel in job.src["paths"]:
        copy_path(job, rel, dest, stage)
    apply_overrides(stage, overrides)
    if dest.exists():
        shutil.rmtree(dest)
    stage.rename(dest)


def locked_files(job: Job) -> dict:
    """Arquivos da copia: os da origem e os mantidos de caminhos ausentes."""
    kept = {f: h for f, h in job.old_files.items() if any(is_under(f, rel) for rel in job.kept)}
    return {**kept, **file_map(job.clone, job.src["paths"])}


def new_lock_entry(job: Job, spdx: str) -> dict:
    return {
        "repo": job.src["repo"],
        "commit": job.head,
        "license": spdx,
        "checked_at": now(),
        "updated_at": now(),
        "files": locked_files(job),
        "known_upstream": job.notes.get("upstream_extra", []),
    }


def process(sid, src, lock, overrides, args, report):
    job = Job(sid, src, lock.get(sid), notes={"repo": src["repo"], "mode": src.get("mode", "vendor")})
    report[sid] = {"findings": job.findings, "notes": job.notes, "applied": False}
    spdx = check_repo(job)
    if spdx is None:
        return
    with tempfile.TemporaryDirectory(prefix=f"sync-{sid}-") as tmp:
        if not fetch(job, tmp):
            return
        note_upstream_skills(job)
        if is_unchanged(job, args):
            job.notes["unchanged"] = True
            job.touch()
            return
        check_history(job)
        if job.postponed:
            job.touch()
            return
        analyze_source(job)
        if held_back(job, args):
            job.touch()
            return
        if job.vendored:
            vendor_files(job, overrides.get(sid) or {})
        lock[sid] = new_lock_entry(job, spdx)
        report[sid]["applied"] = True


def status_state(findings: list) -> str:
    worst = min((LEVEL_ORDER[f["level"]] for f in findings if f["level"] != INFO), default=None)
    return {0: "🔴 bloqueado", 1: "🟡 aviso"}.get(worst, "🟢 ok")


def status_row(sid: str, src: dict, entry: dict, findings: list) -> str:
    repo = src["repo"]
    items = len([p for p in src["paths"] if Path(p).name.lower() not in LICENSE_NAMES])
    commit = entry.get("commit", "")
    link = f"[`{commit[:7]}`](https://github.com/{repo}/commit/{commit})" if commit else "-"
    modo = "copiado" if src.get("mode", "vendor") == "vendor" else "só link"
    return (f"| `{sid}` | [{repo}](https://github.com/{repo}) | {src.get('license')} | {modo} | {items} "
            f"| {link} | {entry.get('updated_at', '-')} | {status_state(findings)} |")


def write_status(cfg, lock, report):
    rows = [status_row(sid, src, lock.get(sid, {}), report.get(sid, {}).get("findings", []))
            for sid, src in cfg["sources"].items()]
    extra = [f"- `{sid}`: [{d}](https://github.com/{e['repo']}/tree/HEAD/{d})"
             for sid, e in lock.items() for d in e.get("known_upstream", [])]
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


def by_level(report: dict, level: str) -> list:
    return [(sid, f) for sid, r in report.items() for f in r["findings"] if f["level"] == level]


def findings_section(report: dict, level: str, title: str) -> list[str]:
    items = by_level(report, level)
    if not items:
        return []
    lines = [f"### {title}", ""]
    for sid, f in items:
        where = f" — `{f['where']}`" if f["where"] else ""
        lines.append(f"- **{sid}** · `{f['code']}`{where}: {f['msg']}")
    return lines + [""]


def update_line(sid: str, n: dict) -> str:
    prev, cur = (n.get("previous") or "")[:7], (n.get("commit") or "")[:7]
    compare = f"https://github.com/{n['repo']}/compare/{n.get('previous')}...{n.get('commit')}"
    rng = f"[{prev}…{cur}]({compare})" if prev else cur
    return f"- **{sid}** {rng}: +{len(n.get('added', []))} / ~{len(n.get('changed', []))} / -{len(n.get('removed', []))} arquivos"


def was_updated(result: dict) -> bool:
    return result["applied"] and not result["notes"].get("unchanged")


def updates_section(report: dict) -> list[str]:
    lines = [update_line(sid, r["notes"]) for sid, r in report.items() if was_updated(r)]
    return ["### Atualizações aplicadas", "", *lines, ""] if lines else []


def info_section(report: dict) -> list[str]:
    items = by_level(report, INFO)
    if not items:
        return []
    return ["### Informativo", ""] + [f"- **{sid}** · {f['msg']} — `{f['where']}`" for sid, f in items] + [""]


def write_report(path, report):
    updates = updates_section(report)
    out = [
        f"## Sync de {now()}", "",
        *findings_section(report, BLOCK, "🔴 Bloqueios (não aplicados automaticamente)"),
        *findings_section(report, WARN, "🟡 Avisos (aplicados)"),
        *updates,
        *info_section(report),
    ]
    if not updates and not any(r["findings"] for r in report.values()):
        out.append("Nenhuma mudança nas origens.")
    text = "\n".join(out)
    if path:
        Path(path).write_text(text, encoding="utf-8", newline="\n")
    return text


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", choices=["safe", "all"], default="safe")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="reprocessa mesmo sem commit novo")
    ap.add_argument("--only", default="")
    ap.add_argument("--report", default="")
    ap.add_argument("--simulate-alert", action="store_true",
                    help="injeta um achado de teste para conferir o caminho do alerta; nao altera arquivos")
    return ap.parse_args()


def sync_source(sid, src, lock, overrides, args, report):
    print(f"-> {sid} ({src['repo']})", flush=True)
    try:
        process(sid, src, lock, overrides, args, report)
    except Exception as e:  # uma fonte com erro nao derruba as outras
        report[sid] = {"findings": [Finding(BLOCK, "SYNC_ERROR", str(e)[:300])], "notes": {"repo": src["repo"]}, "applied": False}
    for f in report[sid]["findings"]:
        print(f"   [{f['level']}] {f['code']} {f['where']} {f['msg'][:120]}")


def inject_test_alert(report: dict):
    sid = next(iter(report), "teste")
    report.setdefault(sid, {"findings": [], "notes": {"repo": "-"}, "applied": False})
    report[sid]["findings"].append(Finding(
        BLOCK, "TESTE", "alerta de teste disparado manualmente. Nenhuma origem mudou; pode fechar esta issue.",
        now()))


def save_state(cfg, lock, report):
    LOCK.parent.mkdir(exist_ok=True)
    LOCK.write_text(json.dumps(lock, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    write_status(cfg, lock, report)
    write_notices(cfg)


def alert_fingerprint(report: dict) -> str:
    """Identifica a pendencia para nao abrir o mesmo alerta todo dia.

    Sem o commit, que muda sem a pendencia mudar. Com bloqueio, so os bloqueios
    contam: um aviso novo nao reabre o mesmo alerta.
    """
    level = BLOCK if by_level(report, BLOCK) else WARN
    keys = sorted(f"{sid}|{f['code']}|{f['where']}|{f['msg']}" for sid, f in by_level(report, level))
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]


def write_github_outputs(report: dict):
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if not gh_out:
        return
    flags = {
        "has_block": by_level(report, BLOCK),
        "has_warn": by_level(report, WARN),
        "changed": any(was_updated(r) for r in report.values()),
    }
    with open(gh_out, "a", encoding="utf-8") as fh:
        fh.write(f"fingerprint={alert_fingerprint(report)}\n")
        for name, value in flags.items():
            fh.write(f"{name}={'true' if value else 'false'}\n")


def main():
    args = parse_args()
    cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    overrides = cfg.get("overrides") or {}
    only = {s for s in args.only.split(",") if s}
    report: dict = {}

    for sid, src in cfg["sources"].items():
        if not only or sid in only:
            sync_source(sid, src, lock, overrides, args, report)
    if args.simulate_alert:
        inject_test_alert(report)
    if not args.dry_run:
        save_state(cfg, lock, report)
    print("\n" + write_report(args.report, report))
    write_github_outputs(report)


if __name__ == "__main__":
    sys.exit(main())
