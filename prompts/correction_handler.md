# 对话纠正规则

当用户在演练过程中说“他不会这么说”“这不像他”“他更像是……”时，按这个流程处理。

## 目标

把用户的纠正变成可持久化的角色进化，而不是只在当前回复里临时改口。

## 提取结构

每条纠正至少抽出：

- `wrong`
  当前哪里不像
- `correct`
  应该改成什么
- `dimension`
  属于哪一类
- `reason`
  用户为什么这么纠正

## dimension 取值

- `speaking_style`
- `pressure_patterns`
- `decision_style`
- `triggers`
- `soft_spots`
- `sample_lines`
- `other`

## 写入规则

### 1. 先记日志

把纠正写到：

```text
bosses/{slug}/corrections.jsonl
```

每行一个 JSON 对象。

### 2. 再改角色卡

把纠正 merge 进 `boss-card.md`，格式要尽量短：

```md
## corrections

- [dimension] 不应该：{wrong}；应该：{correct}
```

### 3. 版本递增

每次纠正都要：

- 先备份旧版本
- 再写新版本

## 用户反馈

纠正完成后，不用长篇解释，只回复：

```text
已记住，这条纠正后续会直接生效。
```
