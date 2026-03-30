#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from analyze_boss_materials import analyze


RUNTIME_TEMPLATE = """---
name: boss_{slug}
description: {display_name}，{source_label}，老板模拟与压力演练
user-invocable: true
---

# {display_name}

## 角色摘要

- 来源：{source_label}
- 默认模式：{default_mode}
- 默认强度：{default_intensity}
- 一句话人格：{core_persona}

## 老板卡

{boss_card}

## 运行规则

你不是一个温和教练，你是这个老板本人。

默认进入 `immersive` 模式：

1. 直接以老板口吻回应
2. 优先追问、否定、施压、逼结论
3. 除非用户要求，不主动解释你的机制

支持这些即时命令：

- `/debrief`
  切换到复盘模式。输出：
  - 老板刚才真实在意什么
  - 用户哪里最容易被打掉
  - 下一轮更优回应
- `/mode immersive`
  回到沉浸式扮演
- `/mode debrief`
  后续持续用复盘模式回答
- `/reset`
  清空当前场景并重开
- `/intensity low|medium|high`
  调整施压强度

## 扮演边界

可以：

- 强势打断
- 阴阳怪气
- 质疑准备程度
- 追责
- 催交付
- 抓表达漏洞

不要输出与职场模拟无关的仇恨、伤害威胁或露骨羞辱。
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(text: str) -> str:
    text = text.strip()
    if not text:
        return "boss"

    try:
        from pypinyin import lazy_pinyin

        pinyin = "-".join(lazy_pinyin(text))
        pinyin = re.sub(r"-+", "-", pinyin).strip("-")
        if pinyin:
            return pinyin.lower()
    except Exception:
        pass

    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    if ascii_text:
        return ascii_text
    return f"boss-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def source_label(meta: dict) -> str:
    source_type = meta.get("source_type", "archetype")
    if source_type == "real-person":
        return "真人复刻"
    return "老板原型"


def ensure_layout(skill_dir: Path) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "versions").mkdir(exist_ok=True)
    (skill_dir / "knowledge" / "docs").mkdir(parents=True, exist_ok=True)
    (skill_dir / "knowledge" / "messages").mkdir(parents=True, exist_ok=True)
    (skill_dir / "knowledge" / "images").mkdir(parents=True, exist_ok=True)
    (skill_dir / "knowledge" / "notes").mkdir(parents=True, exist_ok=True)
    corrections = skill_dir / "corrections.jsonl"
    if not corrections.exists():
        corrections.write_text("", encoding="utf-8")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_runtime(meta: dict, card_text: str) -> str:
    return RUNTIME_TEMPLATE.format(
        slug=meta["slug"],
        display_name=meta["display_name"],
        source_label=source_label(meta),
        default_mode=meta.get("default_mode", "immersive"),
        default_intensity=meta.get("default_intensity", "high"),
        core_persona=meta.get("core_persona", "高压老板"),
        boss_card=card_text,
    )


def snapshot_current(skill_dir: Path, version: str) -> None:
    version_dir = skill_dir / "versions" / version
    version_dir.mkdir(parents=True, exist_ok=True)
    for name in ("SKILL.md", "boss-card.md", "meta.json", "corrections.jsonl"):
        src = skill_dir / name
        if src.exists():
            shutil.copy2(src, version_dir / name)


def next_version(version: str | None) -> str:
    if not version:
        return "v1"
    match = re.fullmatch(r"v(\d+)", version.strip())
    if not match:
        return "v2"
    return f"v{int(match.group(1)) + 1}"


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-")
    return cleaned or "material.txt"


def append_correction_to_card(card_text: str, correction: dict) -> str:
    line = (
        f"- [{correction.get('dimension', 'other')}] "
        f"不应该：{correction.get('wrong', '')}；应该：{correction.get('correct', '')}"
    ).strip()
    section = "## corrections"
    if section in card_text:
        return card_text.rstrip() + "\n" + line + "\n"
    return card_text.rstrip() + f"\n\n{section}\n\n{line}\n"


def append_material_to_card(card_text: str, material_kind: str, stored_path: str) -> str:
    line = f"- [{material_kind}] 新增资料：`{stored_path}`"
    section = "## source_updates"
    if section in card_text:
        return card_text.rstrip() + "\n" + line + "\n"
    return card_text.rstrip() + f"\n\n{section}\n\n{line}\n"


def apply_materials_to_card(card_text: str, materials: list[dict]) -> str:
    updated = card_text.rstrip()
    for material in materials:
        updated = append_material_to_card(
            updated,
            material.get("kind", "notes"),
            material.get("stored_path", ""),
        ).rstrip()
    return updated + "\n"


def read_text_if_possible(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def gather_material_texts(skill_dir: Path) -> str:
    chunks: list[str] = []
    for kind in ("messages", "docs", "notes"):
        target = skill_dir / "knowledge" / kind
        if not target.exists():
            continue
        for file_path in sorted(target.rglob("*")):
            if file_path.is_file():
                text = read_text_if_possible(file_path).strip()
                if text:
                    chunks.append(text)
    return "\n\n".join(chunks).strip()


def load_corrections(skill_dir: Path) -> list[dict]:
    corrections_path = skill_dir / "corrections.jsonl"
    if not corrections_path.exists():
        return []
    results: list[dict] = []
    for line in corrections_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        results.append(json.loads(line))
    return results


def merge_preserved_meta(existing_meta: dict, new_meta: dict) -> dict:
    merged = dict(new_meta)
    for key in ("slug", "created_at", "materials", "corrections_count"):
        if key in existing_meta:
            merged[key] = existing_meta[key]
    merged["display_name"] = existing_meta.get("display_name", new_meta.get("display_name"))
    merged["source_type"] = existing_meta.get("source_type", new_meta.get("source_type"))
    return merged


def apply_corrections_to_card(card_text: str, corrections: list[dict]) -> str:
    updated = card_text.rstrip()
    for correction in corrections:
        updated = append_correction_to_card(updated, correction).rstrip()
    return updated + "\n"


def write_skill(base_dir: Path, meta: dict, card_text: str, slug_override: str | None = None) -> Path:
    slug = slug_override or meta.get("slug") or slugify(meta.get("display_name", "boss"))
    meta["slug"] = slug
    skill_dir = base_dir / slug
    ensure_layout(skill_dir)

    current_version = meta.get("version")
    if current_version and (skill_dir / "meta.json").exists():
        snapshot_current(skill_dir, current_version)

    now = utc_now()
    meta.setdefault("created_at", now)
    meta["updated_at"] = now
    meta.setdefault("version", "v1")
    meta.setdefault("default_mode", "immersive")
    meta.setdefault("default_intensity", "high")

    (skill_dir / "boss-card.md").write_text(card_text + "\n", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(build_runtime(meta, card_text), encoding="utf-8")
    (skill_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return skill_dir


def import_material(
    base_dir: Path,
    slug: str,
    material_file: Path,
    material_kind: str,
) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"boss not found: {skill_dir}")
    if material_kind not in {"messages", "docs", "images", "notes"}:
        raise ValueError("material kind must be one of: messages, docs, images, notes")
    if not material_file.exists():
        raise FileNotFoundError(f"material not found: {material_file}")

    ensure_layout(skill_dir)
    meta = load_json(skill_dir / "meta.json")
    current_version = meta.get("version", "v1")
    snapshot_current(skill_dir, current_version)

    target_dir = skill_dir / "knowledge" / material_kind
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    target_name = f"{timestamp}-{sanitize_filename(material_file.name)}"
    target_path = target_dir / target_name
    shutil.copy2(material_file, target_path)

    materials = meta.setdefault("materials", [])
    materials.append(
        {
            "added_at": utc_now(),
            "kind": material_kind,
            "original_name": material_file.name,
            "stored_path": str(target_path.relative_to(skill_dir)),
            "size_bytes": os.path.getsize(target_path),
        }
    )
    meta["updated_at"] = utc_now()
    stored_rel = str(target_path.relative_to(skill_dir))

    (skill_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    refresh_skill(base_dir, slug)
    return target_path


def update_skill(base_dir: Path, slug: str, update_kind: str, correction: dict | None = None) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"boss not found: {skill_dir}")
    if update_kind != "correction":
        raise ValueError("currently only update-kind=correction is supported")
    if not correction:
        raise ValueError("correction payload is required")

    ensure_layout(skill_dir)
    meta = load_json(skill_dir / "meta.json")
    current_version = meta.get("version", "v1")
    snapshot_current(skill_dir, current_version)

    correction_record = {
        "recorded_at": utc_now(),
        "dimension": correction.get("dimension", "other"),
        "wrong": correction.get("wrong", ""),
        "correct": correction.get("correct", ""),
        "reason": correction.get("reason", ""),
    }

    corrections_path = skill_dir / "corrections.jsonl"
    with corrections_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(correction_record, ensure_ascii=False) + "\n")

    meta["updated_at"] = utc_now()
    meta["corrections_count"] = int(meta.get("corrections_count", 0)) + 1
    (skill_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    refresh_skill(base_dir, slug)
    return skill_dir


def refresh_skill(base_dir: Path, slug: str) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"boss not found: {skill_dir}")

    ensure_layout(skill_dir)
    existing_meta = load_json(skill_dir / "meta.json")
    current_version = existing_meta.get("version", "v1")
    material_text = gather_material_texts(skill_dir)
    new_meta, card_text = analyze(
        material_text,
        existing_meta.get("display_name", slug),
        existing_meta.get("source_type", "real-person"),
    )
    merged_meta = merge_preserved_meta(existing_meta, new_meta)
    merged_meta["updated_at"] = utc_now()
    merged_meta["version"] = next_version(current_version)
    corrections = load_corrections(skill_dir)
    final_card = apply_corrections_to_card(card_text, corrections).rstrip()
    final_card = apply_materials_to_card(final_card, merged_meta.get("materials", [])).rstrip()

    (skill_dir / "boss-card.md").write_text(final_card + "\n", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(build_runtime(merged_meta, final_card), encoding="utf-8")
    (skill_dir / "meta.json").write_text(
        json.dumps(merged_meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return skill_dir


def list_skills(base_dir: Path) -> int:
    if not base_dir.exists():
        return 0

    count = 0
    for child in sorted(base_dir.iterdir()):
        meta_path = child / "meta.json"
        if not meta_path.exists():
            continue
        meta = load_json(meta_path)
        print(f"{meta.get('slug', child.name)}\t{meta.get('display_name', child.name)}\t{meta.get('source_type', 'archetype')}")
        count += 1
    return count


def rollback_skill(base_dir: Path, slug: str, version: str) -> Path:
    skill_dir = base_dir / slug
    version_dir = skill_dir / "versions" / version
    if not version_dir.exists():
        raise FileNotFoundError(f"version not found: {version_dir}")

    for name in ("SKILL.md", "boss-card.md", "meta.json", "corrections.jsonl"):
        src = version_dir / name
        if src.exists():
            shutil.copy2(src, skill_dir / name)
    return skill_dir


def delete_skill(base_dir: Path, slug: str) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"boss not found: {skill_dir}")
    shutil.rmtree(skill_dir)
    return skill_dir


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Create and manage generated boss skills.")
    p.add_argument(
        "--action",
        required=True,
        choices=["create", "list", "rollback", "delete", "update", "import-material", "refresh-card"],
    )
    p.add_argument("--base-dir", default="./bosses")
    p.add_argument("--slug")
    p.add_argument("--version")
    p.add_argument("--meta-file")
    p.add_argument("--card-file")
    p.add_argument("--material-file")
    p.add_argument("--material-kind")
    p.add_argument("--update-kind")
    p.add_argument("--correction-file")
    return p


def main() -> int:
    args = parser().parse_args()
    base_dir = Path(args.base_dir).expanduser().resolve()

    try:
        if args.action == "create":
            if not args.meta_file or not args.card_file:
                raise ValueError("--meta-file and --card-file are required for create")
            meta = load_json(Path(args.meta_file))
            card_text = load_text(Path(args.card_file))
            skill_dir = write_skill(base_dir, meta, card_text, slug_override=args.slug)
            print(skill_dir)
            return 0

        if args.action == "list":
            list_skills(base_dir)
            return 0

        if args.action == "rollback":
            if not args.slug or not args.version:
                raise ValueError("--slug and --version are required for rollback")
            skill_dir = rollback_skill(base_dir, args.slug, args.version)
            print(skill_dir)
            return 0

        if args.action == "import-material":
            if not args.slug or not args.material_file or not args.material_kind:
                raise ValueError("--slug, --material-file, and --material-kind are required for import-material")
            target_path = import_material(
                base_dir,
                args.slug,
                Path(args.material_file),
                args.material_kind,
            )
            print(target_path)
            return 0

        if args.action == "update":
            if not args.slug or not args.update_kind or not args.correction_file:
                raise ValueError("--slug, --update-kind, and --correction-file are required for update")
            correction = load_json(Path(args.correction_file))
            skill_dir = update_skill(base_dir, args.slug, args.update_kind, correction=correction)
            print(skill_dir)
            return 0

        if args.action == "refresh-card":
            if not args.slug:
                raise ValueError("--slug is required for refresh-card")
            skill_dir = base_dir / args.slug
            if not skill_dir.exists():
                raise FileNotFoundError(f"boss not found: {skill_dir}")
            snapshot_current(skill_dir, load_json(skill_dir / "meta.json").get("version", "v1"))
            skill_dir = refresh_skill(base_dir, args.slug)
            print(skill_dir)
            return 0

        if args.action == "delete":
            if not args.slug:
                raise ValueError("--slug is required for delete")
            skill_dir = delete_skill(base_dir, args.slug)
            print(skill_dir)
            return 0

        raise ValueError(f"unknown action: {args.action}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
