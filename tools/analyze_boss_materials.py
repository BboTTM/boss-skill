#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARCHETYPE_KEYWORDS = {
    "强压型": ["马上", "立刻", "今天", "现在", "为什么还没", "别解释", "结论", "谁负责"],
    "PUA 型": ["成长", "层级", "不应该", "我是在帮你", "我对你有期待", "你这个水平"],
    "结果导向型": ["结果", "交付", "影响", "deadline", "截止", "什么时候能做完"],
    "控制型": ["同步", "按我的", "不要自己发挥", "我来定", "先别发", "先给我看"],
    "情绪化型": ["没耐心", "每次都这样", "你到底在说什么", "烦", "受不了"],
}

DIMENSION_KEYWORDS = {
    "speaking_style": ["结论", "重点", "直接", "打断", "同步", "一句话", "先说"],
    "pressure_patterns": ["谁负责", "deadline", "今天", "马上", "现在", "解释", "准备不足", "复盘"],
    "decision_style": ["拍板", "决定", "方案", "选项", "风险", "影响", "优先级"],
    "triggers": ["没重点", "没准备", "不清楚", "不知道", "拖", "失控", "风险"],
    "soft_spots": ["结论先行", "两个选项", "时间点", "owner", "风险预案", "一句话"],
}

SAMPLE_LINE_PATTERNS = [
    r"[^。！？\n]*(结论|重点|谁负责|什么时候|别解释|先说)[^。！？\n]*[。！？]?",
    r"[^。！？\n]*(不应该|我是在帮你|按我的|先别发)[^。！？\n]*[。！？]?",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_lines(text: str) -> list[str]:
    lines = [line.strip() for line in re.split(r"[\n\r]+", text) if line.strip()]
    return lines


def keyword_hits(text: str, keywords: list[str]) -> int:
    return sum(text.count(keyword) for keyword in keywords)


def pick_archetype(text: str) -> tuple[str, dict[str, int]]:
    scores = {name: keyword_hits(text, words) for name, words in ARCHETYPE_KEYWORDS.items()}
    best = max(scores, key=scores.get) if scores else "强压型"
    if scores.get(best, 0) == 0:
        best = "强压型"
    return best, scores


def extract_sample_lines(text: str) -> list[str]:
    found: list[str] = []
    for pattern in SAMPLE_LINE_PATTERNS:
        for match in re.findall(pattern, text):
            if isinstance(match, tuple):
                continue
        for matched in re.finditer(pattern, text):
            line = matched.group(0).strip()
            if line and line not in found:
                found.append(line)
    return found[:5]


def infer_bullets(text: str, dimension: str) -> list[str]:
    bullets: list[str] = []
    keywords = DIMENSION_KEYWORDS[dimension]
    for line in normalize_lines(text):
        if any(keyword in line for keyword in keywords):
            cleaned = re.sub(r"\s+", " ", line)
            if cleaned not in bullets:
                bullets.append(cleaned[:80])
        if len(bullets) >= 4:
            break
    return bullets


def build_card(meta: dict, text: str) -> str:
    speaking = infer_bullets(text, "speaking_style") or ["先要结论，不爱听长背景", "不满意时会直接打断"]
    pressure = infer_bullets(text, "pressure_patterns") or ["逼时间点", "逼责任归属"]
    triggers = infer_bullets(text, "triggers") or ["汇报没重点", "没有风险预案"]
    soft_spots = infer_bullets(text, "soft_spots") or ["先给结论", "给明确时间点和 owner"]
    samples = extract_sample_lines(text) or ["你先别讲过程，结论是什么？", "这个事情到底谁负责？"]
    card = [
        "## 核心人格",
        "",
        meta["core_persona"],
        "",
        "## speaking_style",
        "",
        *[f"- {item}" for item in speaking[:4]],
        "",
        "## pressure_patterns",
        "",
        *[f"- {item}" for item in pressure[:4]],
        "",
        "## decision_style",
        "",
        meta["decision_style"],
        "",
        "## triggers",
        "",
        *[f"- {item}" for item in triggers[:4]],
        "",
        "## soft_spots",
        "",
        *[f"- {item}" for item in soft_spots[:4]],
        "",
        "## sample_lines",
        "",
        *[f"- {item}" for item in samples[:4]],
        "",
        "## debrief_rules",
        "",
        meta["debrief_rules"],
    ]
    return "\n".join(card).strip() + "\n"


def analyze(text: str, display_name: str, source_type: str, user_notes: str = "") -> tuple[dict, str]:
    combined = f"{user_notes}\n{text}".strip()
    archetype, scores = pick_archetype(combined)
    top_style = infer_bullets(combined, "speaking_style")
    top_pressure = infer_bullets(combined, "pressure_patterns")
    confidence = "high" if len(combined) > 800 else "medium" if len(combined) > 200 else "low"
    core_persona = (
        f"{archetype}老板，偏好先压住对方，再推动结论和责任明确。"
        if source_type == "real-person"
        else f"{archetype}老板，用高压方式逼结论和交付。"
    )
    if confidence == "low":
        core_persona += " 当前判断基于有限资料。"
    meta = {
        "display_name": display_name,
        "source_type": source_type,
        "core_persona": core_persona,
        "default_mode": "immersive",
        "default_intensity": "high" if archetype in {"强压型", "PUA 型", "情绪化型"} else "medium",
        "decision_style": (
            "偏结果导向，喜欢先听结论和责任边界，再决定是否追问细节。"
            if top_pressure
            else "会先确认结果、时间点和 owner，再判断是否接受方案。"
        ),
        "debrief_rules": (
            "复盘时优先指出：结论是否前置、责任是否清楚、时间承诺是否明确、是否提前处理风险。"
        ),
        "analysis": {
            "archetype_guess": archetype,
            "archetype_scores": scores,
            "confidence": confidence,
            "source_excerpt_length": len(combined),
        },
    }
    return meta, build_card(meta, combined)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Analyze boss source materials and draft a boss card.")
    p.add_argument("--input", action="append", dest="inputs", default=[], help="Material text file path. Repeatable.")
    p.add_argument("--display-name", required=True)
    p.add_argument("--source-type", choices=["archetype", "real-person"], required=True)
    p.add_argument("--notes-file")
    p.add_argument("--meta-out", required=True)
    p.add_argument("--card-out", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    material_texts = [read_text(Path(path)) for path in args.inputs]
    notes = read_text(Path(args.notes_file)) if args.notes_file else ""
    combined = "\n\n".join(material_texts).strip()
    meta, card = analyze(combined, args.display_name, args.source_type, user_notes=notes)
    Path(args.meta_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.card_out).write_text(card, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
