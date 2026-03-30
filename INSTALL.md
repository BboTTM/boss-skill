# 安装说明

## Claude Code

Claude Code 从项目根目录下的 `.claude/skills/` 发现 skill。

安装到当前项目：

```bash
mkdir -p .claude/skills
cp -R /path/to/create-boss .claude/skills/create-boss
```

安装到全局：

```bash
mkdir -p ~/.claude/skills
cp -R /path/to/create-boss ~/.claude/skills/create-boss
```

## 依赖

```bash
pip3 install -r requirements.txt
```

依赖是可选的：

- `pypinyin`
  用于把中文老板名字更稳定地转换成 slug

## 验证安装

```bash
python3 tools/analyze_boss_materials.py --help
python3 tools/skill_writer.py --help
python3 -m unittest discover -s tests -v
```

## 推荐发布前检查

```bash
python3 -m unittest discover -s tests -v
find . -maxdepth 3 -type f | sort
```
