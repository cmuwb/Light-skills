# 在 Codex 中安装 Light

Light 是一套全流程科研技能包。Codex 通过原生 skill 发现机制加载它。

## 前置

- Git
- 已安装 Codex CLI

## 安装（推荐：克隆 + 链接）

1. **克隆 Light 仓库：**
   ```bash
   git clone https://github.com/Light0305/Light.git ~/.codex/Light
   ```

2. **创建 skills 链接：**

   **macOS / Linux：**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/Light/skills ~/.agents/skills/light
   ```

   **Windows (PowerShell)：**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\light" "$env:USERPROFILE\.codex\Light\skills"
   ```

3. **追加路由说明到全局 AGENTS.md**（让 Codex 知道何时调用 Light）：
   ```bash
   cat ~/.codex/Light/AGENTS.snippet.md >> ~/.codex/AGENTS.md
   ```
   Windows (PowerShell)：
   ```powershell
   Get-Content "$env:USERPROFILE\.codex\Light\AGENTS.snippet.md" | Add-Content "$env:USERPROFILE\.codex\AGENTS.md"
   ```

4. **重启 Codex**（退出并重新启动 CLI）以发现技能。

## 验证

启动 Codex 后输入「帮我做文献调研」或「这篇论文该投哪个期刊」，应触发 Light 对应技能。

## 卸载

删除链接与克隆目录，并移除 `~/.codex/AGENTS.md` 中 Light 追加的小节即可。
