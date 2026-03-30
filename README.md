<div align="center">

# 老板.skill

<hr>

> “老板老板，又老又死板，讲不出东西，听不懂人话。”

**练习！把老板的讲话风格与决策习惯蒸馏成 AI Skill。<br>
让AI模仿老板来拷打你，学会到底怎么和老板沟通。**

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)
![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green.svg)

<br>

先创建一个老板角色，再直接开练。<br>
支持自选老板大类风格生成角色。<br>
也支持根据聊天记录、文档、截图和主观描述做真人复刻。<br>
角色不是一次性 prompt，会随着资料导入、对话纠正持续进化。<br>
你可以用它练汇报、练被追责、练对线，也可以直接辱骂老板。

[安装](#安装) · [使用](#使用) · [效果示例](#效果示例) · [详细安装](INSTALL.md) · [English](README_EN.md)

</div>

把“老板风格”蒸馏成一个可反复调用的 AI Skill。

它支持两种来源：

- `老板 archetype`
  例如强压型、PUA 型、结果导向型、控制型、情绪化老板
- `真人复刻`
  根据聊天记录、文档、截图 OCR 和你的补充描述，生成更像某个真实老板的角色

生成后可以直接用 `/{slug}` 开练，默认沉浸式模拟；输入 `/debrief` 再切换到复盘模式。
这个角色还支持持续进化：追加资料、当场纠正、版本回滚。

公共 demo：

- [bosses/boss-li](./bosses/boss-li)

## 适合什么场景

- 当面汇报压力演练
- 被老板追责时的抗压训练
- 方案评审时的挑刺和追问
- 向上管理和反驳训练

## 设计原则

- 使用时要明了：先创建角色，再直接开练
- 沉浸感优先：默认像老板本人一样说话
- 训练价值优先：支持随时切到复盘模式
- 压力可以很强，但保持在职场施压和沟通攻击范围内

## 安装

这个仓库本身就是一个 meta-skill 目录。

Claude Code:

```bash
mkdir -p .claude/skills
cp -R /path/to/this-repo .claude/skills/create-boss
```

或全局安装：

```bash
cp -R /path/to/this-repo ~/.claude/skills/create-boss
```

可选依赖：

```bash
pip3 install -r requirements.txt
```

如果你要发布到仓库，建议保留根目录结构不变，让整个 repo 就是一个 skill 目录。

## 使用

### 1. 创建老板角色

在 Claude Code 中输入：

```text
/create-boss
```

然后选择：

- `archetype`：从预设老板原型开始
- `real-person`：根据资料复刻具体老板

创建完成后会得到一个 `slug`，例如 `boss-li`。

### 2. 追加资料或纠正

如果已经有角色，后续不用重建，直接更新：

```text
/update-boss boss-li
```

你可以做两类更新：

- 追加资料：聊天记录、截图、文档、邮件、补充说明
- 当场纠正：例如“他不会这么说”“他更像是先冷一下再问谁负责”

追加的原始资料会归档到：

```text
bosses/{slug}/knowledge/
```

纠正记录会归档到：

```text
bosses/{slug}/corrections.jsonl
```

每次更新都会自动存一个版本，后面可以回滚。

### 3. 直接开练

如果已经有角色，直接调用：

```text
/boss-li
```

或用统一入口：

```text
/boss-sim
```

### 4. 运行时命令

在已经进入某个老板的模拟对话后，可以使用：

- `/debrief`：切到复盘模式
- `/mode immersive`：回到沉浸式扮演
- `/mode debrief`：持续复盘模式
- `/reset`：重开当前场景
- `/intensity low|medium|high`：调整压迫强度

## 效果示例

> 输入：`强压型 + 结果导向型，最讨厌汇报没重点`

场景一：当面汇报

```text
用户        ❯ 这个项目我先讲一下背景，我们最近遇到一个历史问题...

老板.skill  ❯ 先别讲背景，结论是什么？
              你现在这个汇报我听了半分钟，还不知道你要我拍什么板。
              谁负责？什么时候交？风险你准备怎么兜？
```

场景二：复盘模式

```text
用户        ❯ /debrief

老板.skill  ❯ 这轮他真正不满的不是你方案差，而是你没有把结论、owner、时间点放到最前面。
              你刚才最容易被打掉的点是：解释过多，但没有先给选择。
              更好的回应范式是：
              1. 先一句话说结论
              2. 再给两个方案
              3. 最后讲风险和时间
```

## 管理命令

- `/create-boss`
- `/update-boss {slug}`
- `/boss-sim`
- `/list-bosses`
- `/boss-rollback {slug} {version}`
- `/delete-boss {slug}`
- `/{slug}`

## 自动抽取

如果你已经拿到了文本资料，也可以直接用分析脚本先草拟一版角色：

```bash
python3 tools/analyze_boss_materials.py \
  --input /path/to/messages.txt \
  --display-name "李总" \
  --source-type real-person \
  --meta-out /tmp/boss-meta.json \
  --card-out /tmp/boss-card.md
```

然后再写入角色：

```bash
python3 tools/skill_writer.py \
  --action create \
  --slug boss-li \
  --meta-file /tmp/boss-meta.json \
  --card-file /tmp/boss-card.md \
  --base-dir ./bosses
```

如果后续有新资料，也可以在导入后强制重刷一遍角色卡：

```bash
python3 tools/skill_writer.py --action refresh-card --slug boss-li --base-dir ./bosses
```

## 仓库结构

```text
create-boss/
├── SKILL.md
├── prompts/
│   ├── intake.md
│   ├── archetype_catalog.md
│   ├── real_person_extractor.md
│   ├── material_ingest.md
│   ├── correction_handler.md
│   └── boss_card_template.md
├── tools/
│   ├── analyze_boss_materials.py
│   └── skill_writer.py
├── tests/
│   ├── test_analyze_boss_materials.py
│   └── test_skill_writer.py
├── bosses/
│   └── {slug}/
│       ├── SKILL.md
│       ├── boss-card.md
│       ├── corrections.jsonl
│       ├── meta.json
│       ├── knowledge/
│       └── versions/
└── requirements.txt
```

## 说明

当前版本重点是把“可创建、可进化、可回滚”的链路跑通：

- 角色创建清楚
- 角色结构统一
- 生成结果可复用
- 可直接进入模拟
- 可追加资料
- 可纠正并立即进化
- 可版本回滚

OCR、版本管理、更多 archetype、批量导入都可以在这个基础上继续加。

## 功能特性

### 角色创建

- 支持 `archetype` 和 `real-person` 两种创建路径
- 统一落成 `meta.json + boss-card.md + SKILL.md`
- 可直接产出 `/{slug}` 可调用角色

### 持续进化

- 追加资料后自动归档到 `knowledge/`
- 导入文本资料后可自动刷新角色卡
- 对话纠正会写进 `corrections.jsonl`
- 每次更新自动保存历史版本

### 发布友好

- 带测试
- 带安装文档
- 带英文 README
- 带 OpenAI/AgentSkills 元数据

## 验证

```bash
python3 -m unittest discover -s tests -v
```

---

<div align="center">

MIT License © [BboTTM](https://github.com/BboTTM)

本 Skill 在结构设计、README 组织方式和 meta-skill 思路上参考了
[titanwings/colleague-skill](https://github.com/titanwings/colleague-skill)。

</div>
