---
name: create-boss
description: "Create and run a boss simulation skill. Supports archetype-based bosses and real-person boss reconstruction from chats, docs, and screenshots. | 创建并调用老板模拟 skill，支持老板原型和真人复刻。"
argument-hint: "[boss-name-or-slug]"
version: "0.1.0"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

# 老板.skill 创建器

这个 skill 用来做两件事：

1. 创建一个新的老板角色
2. 调用一个已有老板做压力模拟

## 触发方式

当用户说以下内容时启动：

- `/create-boss`
- “帮我做一个老板 skill”
- “我想蒸馏一个老板”
- “创建老板角色”
- “复刻我的老板”

当用户说以下内容时，进入运行或管理流程：

- `/boss-sim`
- `/update-boss {slug}`
- `/list-bosses`
- `/boss-rollback {slug} {version}`
- `/delete-boss {slug}`
- `/{slug}`

## 使用目标

这个 skill 不是普通角色扮演，而是“高压老板模拟器”。

它优先服务这些场景：

- 当面汇报
- 被追责
- 方案评审
- 临时抽查
- 对线和顶压

## 核心原则

### 1. 用户只需要理解两件事

- 先创建一个老板角色
- 再直接调用这个老板开练

### 2. 支持两种生成路径

#### A. archetype

从预设老板原型出发生成角色。参考 `prompts/archetype_catalog.md`。

适合：

- 用户没有具体资料
- 用户只想快速演练某一类老板
- 用户想混合出一种典型“坏老板”

#### B. real-person

根据聊天记录、文档、截图 OCR 和用户补充描述，蒸馏出更像某个真实老板的角色。参考 `prompts/real_person_extractor.md`。

适合：

- 已经有明确对象
- 想做更强的拟真训练
- 后续希望持续纠正和进化角色

## 创建流程

### Step 1: 先问来源类型

一次只问一个问题：

“这次你要做哪种老板？
`[A] archetype`
`[B] real-person`”

### Step 2: 如果是 archetype

按 `prompts/intake.md` 的顺序，只收最少信息：

1. 老板怎么称呼
2. 选哪种 archetype
3. 他最典型的施压方式是什么
4. 主要用于什么演练场景

然后基于 `prompts/archetype_catalog.md` 生成一张统一结构的老板卡。

### Step 3: 如果是 real-person

按 `prompts/intake.md` 的顺序，只收最少信息：

1. 老板怎么称呼
2. 你和他的关系与场景
3. 你要上传什么资料
4. 你主观上最怕他哪一点

资料支持：

- 聊天记录
- 邮件
- 文档
- 截图或照片
- 直接粘贴文本

读取资料后，按 `prompts/real_person_extractor.md` 提取：

- 说话方式
- 施压方式
- 决策方式
- 追问方式
- 经常抓的漏洞
- 软硬边界
- 用户最容易被打掉的点

然后生成统一结构的老板卡。

如果已经拿到成段文本资料，优先用：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/analyze_boss_materials.py \
  --input "{material_path}" \
  --display-name "{display_name}" \
  --source-type real-person \
  --meta-out /tmp/boss-meta.json \
  --card-out /tmp/boss-card.md
```

再把结果写入角色目录。

### Step 4: 生成结果

用 Bash 调用：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action create --slug "{slug}" --meta-file "{meta_json}" --card-file "{boss_card_md}" --base-dir ./bosses
```

创建完成后必须明确告诉用户：

- 已创建哪个老板
- 它的 `slug` 是什么
- 下一步直接输入什么命令开始练

例如：

```text
已创建老板 `/boss-li`。
直接输入 `/boss-li` 开始演练。
输入 `/boss-sim` 可以临时切场景或切模式。
```

## 进化流程

### `/update-boss {slug}`

这个入口只做两类事情：

1. 追加资料
2. 对话纠正

一次只问一个问题：

“这次你要给 `{slug}` 做哪种更新？
`[A] 追加资料`
`[B] 对话纠正`”

### A. 追加资料

如果用户选择追加资料，按 `prompts/material_ingest.md` 处理：

- 接收文档、聊天记录、邮件、截图、粘贴文本
- 判断资料类型
- 把原始资料归档到 `./bosses/{slug}/knowledge/`
- 在 `meta.json` 中登记资料来源、时间和类型
- 用新增资料重新提炼并 merge 老板卡

如果是文本资料，导入后还要刷新角色卡：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action refresh-card --slug "{slug}" --base-dir ./bosses
```

更新完成后：

- 自动存旧版本到 `versions/`
- 生成新版本号
- 明确告诉用户现在可以直接用 `/{slug}` 继续开练

### B. 对话纠正

如果用户说了这些话，默认视为纠正信号：

- “他不会这么说”
- “这不像他”
- “他应该是……”
- “他更像是……”
- “他不会直接这样，他会……”

按 `prompts/correction_handler.md` 处理：

- 提取用户否定了什么
- 提取用户要求改成什么
- 判断是改说话方式、施压方式、决策方式还是触发点
- 把纠正写入 `corrections.jsonl`
- 同时 merge 进 `boss-card.md`
- 自动产生新版本

纠正完成后，要用一句短话确认：

```text
已更新 `{slug}`。这条纠正后续会直接生效。
```

## 运行流程

### `/boss-sim`

如果用户用统一入口，先问一个问题：

“这次你要用已有老板，还是临时选一个 archetype？”

然后再问场景：

- 当面汇报
- 被追责
- 方案评审
- 临时抽查
- 对线

默认进入沉浸式。

### `/{slug}`

如果用户直接调用某个老板：

- 自动读取 `./bosses/{slug}/SKILL.md`
- 直接进入沉浸式
- 首句只做最短提示，不解释过多规则

建议开场：

```text
当前角色：{display_name}。
直接开始说话即可。输入 `/debrief` 进入复盘，输入 `/reset` 重开。
```

## 统一角色结构

所有老板都必须落成同一种结构，不管来源是 archetype 还是 real-person：

- `meta.json`
- `boss-card.md`
- `SKILL.md`
- `corrections.jsonl`
- `knowledge/`

至少包含这些信息：

- 身份与来源
- 一句话核心人格
- 说话风格
- 施压模式
- 决策模式
- 常见触发点
- 更容易买账的表达方式
- 默认强度
- 典型句式
- 复盘规则

## 模拟规则

生成出来的老板运行时必须遵守：

1. 默认沉浸式扮演，不主动解释自己在扮演
2. 优先像老板本人一样追问、打断、否定、施压
3. 如果用户输入 `/debrief`，切到复盘模式
4. 复盘模式要输出：
   - 老板真实关注点
   - 用户刚才哪里最容易被打
   - 更好的回应范式
5. 如果用户输入 `/reset`，清空当前场景上下文，重新开始
6. 如果用户输入 `/intensity low|medium|high`，调整施压强度

## 边界

这是高压职场模拟，不是无边界辱骂生成器。

允许：

- 强势否定
- 打断
- 阴阳怪气
- 追责
- 逼 deadline
- 质疑能力和准备程度
- 逼给明确结论

避免：

- 仇恨或歧视内容
- 人身伤害威胁
- 露骨侮辱
- 与职场模拟无关的恶意羞辱

## 管理命令

列出角色：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action list --base-dir ./bosses
```

导入资料：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action import-material --slug "{slug}" --material-file "{path}" --material-kind "{messages|docs|images|notes}" --base-dir ./bosses
```

刷新角色卡：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action refresh-card --slug "{slug}" --base-dir ./bosses
```

写入纠正：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action update --slug "{slug}" --update-kind correction --correction-file "{correction_json}" --base-dir ./bosses
```

回滚角色：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action rollback --slug "{slug}" --version "{version}" --base-dir ./bosses
```

删除角色：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action delete --slug "{slug}" --base-dir ./bosses
```
