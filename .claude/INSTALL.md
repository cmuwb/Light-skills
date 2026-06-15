# 在 Claude Code 中安装 Light（含常驻纪律双保险）

Light 是一套全流程科研技能包。Claude Code 通过原生 skill 发现机制加载 28 个 `light-*`
技能；本文额外说明**常驻纪律双保险**的安装——让 a07-a10 等常驻技能真正每会话生效，
而非靠 description 概率匹配。

## 为什么需要双保险

Claude Code 技能只有两种触发：用户打 `/name`，或模型读 description 那句自主判断相关才
加载。正文只在被调用那次进上下文，compaction 后可能整个掉。所以 ROUTER/CONVENTIONS
写的"a07-a10 所有任务后台生效""常驻、输出前必跑"在纯 description 机制下**是愿望非保证**。
self-review/research-ethics 这种要求 100% 触发的兜不住。

双保险（都不需 MCP、不花钱、Claude Code 原生）：
- **CLAUDE.md 块**（`CLAUDE.snippet.md`）：每会话开头必载，列常驻技能 + 路由速查。
- **SessionStart hook**（`hooks/session_start_resident.py`）：harness 层确定性注入同一份
  常驻纪律为 additionalContext，不依赖模型自觉。

两者互补：CLAUDE.md 保证"开头看到"，hook 保证"compaction/resume 后仍注入"。

## 前置

- Git；已安装 Claude Code CLI；本机有 `python`（hook 用，纯 stdlib）。

## 1. 克隆 + 链接技能

```bash
git clone https://github.com/Light0305/Light-skills.git ~/.claude/Light-skills
cd ~/.claude/Light-skills
```

**macOS / Linux：**
```bash
./install.sh claude
```

**Windows (PowerShell)：**
```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\Light-skills\install.ps1" -Client claude
```

脚本把 28 个技能链接到 `~/.claude/skills/`，共享库链接到 `~/.claude/databases`、
`~/.claude/code_assets`，装完即可发现技能。**下面 2、3 步是常驻纪律双保险（可选但强烈建议）。**

## 2. 追加常驻纪律到全局 `CLAUDE.md`（幂等，带 marker 守卫）

**macOS / Linux：**
```bash
mkdir -p ~/.claude
touch ~/.claude/CLAUDE.md
if ! grep -q '<!-- LIGHT-SKILLS-START -->' ~/.claude/CLAUDE.md; then
  cat ~/.claude/Light-skills/CLAUDE.snippet.md >> ~/.claude/CLAUDE.md
else
  echo 'Light 常驻块已存在于 ~/.claude/CLAUDE.md；升级请手动替换 START/END 之间旧块。'
fi
```

**Windows (PowerShell)：**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude" | Out-Null
$claudemd = "$env:USERPROFILE\.claude\CLAUDE.md"
if (-not (Test-Path $claudemd)) { New-Item -ItemType File -Path $claudemd | Out-Null }
if (-not (Select-String -Path $claudemd -Pattern '<!-- LIGHT-SKILLS-START -->' -Quiet)) {
  Get-Content "$env:USERPROFILE\.claude\Light-skills\CLAUDE.snippet.md" | Add-Content $claudemd
} else {
  Write-Host 'Light 常驻块已存在于 ~/.claude/CLAUDE.md；升级请手动替换 START/END 之间旧块。'
}
```

## 3. 注册 SessionStart hook 到全局 `settings.json`

hook 输出一份常驻纪律，由 harness 在每次会话开始确定性注入（compaction/resume 后也注入）。
脚本 `hooks/session_start_resident.py` 纯 stdlib、零网络、跨平台、只读无副作用。

`settings.json` 是 JSON 不是 marker 文本，**不能像 CLAUDE.md 那样安全 append**——若你已有
其他 hooks，盲目拼接会产生非法 JSON。请**手动合并**下面片段进 `~/.claude/settings.json`
的 `hooks` 段（已有 `hooks` 就把 `SessionStart` 数组并进去，没有就整段加）。

**Windows**（片段见 `hooks/settings.snippet.windows.json`）：
```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command",
        "command": "python \"%USERPROFILE%\.claude\Light-skills\hooks\session_start_resident.py\"" } ] }
    ]
  }
}
```

**macOS / Linux**（片段见 `hooks/settings.snippet.unix.json`，用 `python3`）：
```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command",
        "command": "python3 \"$HOME/.claude/Light-skills/hooks/session_start_resident.py\"" } ] }
    ]
  }
}
```

> 路径说明：故意写**绝对路径**（`~/.claude/Light-skills/...`）而非 `${CLAUDE_PROJECT_DIR}`
> ——后者指向当前项目，而本 hook 装在全局克隆里，必须不随项目变。脚本内部用
> `Path(__file__)` 自定位，无需额外环境变量。Windows 用 `%USERPROFILE%`、Unix 用 `$HOME`，
> 因 stock Windows shell 不展开 `$HOME`。装在别处就改这个绝对路径。
> hook 失败不阻断会话（SessionStart 不可阻断），仅 debug log 记一行；JSON 仅在 exit 0 时被解析。

## 验证

```bash
# 1) hook 脚本自测（应 ALL PASS、exit 0）
python ~/.claude/Light-skills/hooks/session_start_resident.py --selftest
# 2) 重启 Claude Code，新开会话。模型上下文开头应含"Light 科研技能包 · 常驻纪律"。
```
启动后输入「帮我做文献调研」「这篇该投哪个期刊」「继续，刚断了」，预期路由到对应
`light-*` 技能；断点恢复类先走 `light-memory-pm` + `light-orchestrator`。

## 升级

```bash
cd ~/.claude/Light-skills && git pull && ./install.sh claude
```
若 `CLAUDE.snippet.md` 有更新，手动替换 `~/.claude/CLAUDE.md` 中 `LIGHT-SKILLS-START` /
`LIGHT-SKILLS-END` 之间旧块；hook 脚本随 git pull 自动更新（settings.json 路径不变无需改）。

## 卸载

1. 删 `~/.claude/CLAUDE.md` 里 `LIGHT-SKILLS-START`/`END` 之间整块。
2. 删 `~/.claude/settings.json` 里手动加的 `SessionStart` hook 项。
3. 删技能与共享链接（**只删链接，不对共享路径 blanket `rm -rf`**）：

**macOS / Linux：**
```bash
for p in ~/.claude/skills/light-* ~/.claude/databases ~/.claude/code_assets; do
  if [ -L "$p" ]; then rm "$p"; elif [ -e "$p" ]; then echo "skip non-symlink: $p"; fi
done
rm -rf ~/.claude/Light-skills
```

**Windows (PowerShell)：** 用 `cmd /c rmdir` 删 junction（**勿用 `Remove-Item -Recurse`，会穿透链接删源**）：
```powershell
$paths = @("$env:USERPROFILE\.claude\databases","$env:USERPROFILE\.claude\code_assets") +
  @(Get-ChildItem "$env:USERPROFILE\.claude\skills" -Filter 'light-*' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
foreach ($p in $paths) {
  if (Test-Path -LiteralPath $p) {
    $item = Get-Item -LiteralPath $p -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { cmd /c rmdir "$p" }
    else { Write-Host "skip non-link: $p" }
  }
}
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\Light-skills" -ErrorAction SilentlyContinue
```
