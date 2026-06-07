# 安全策略 / Security Policy

## 报告漏洞 / Reporting a Vulnerability

Light 是科研技能包,本身不部署服务,但它内置可运行脚本、安装脚本(`install.ps1`/`install.sh`),并会引导调用外部 API。若你发现以下任一问题:

- 安装脚本可能造成意外的文件覆盖、越权链接或删除
- 内置脚本中的命令注入、路径穿越、不安全的反序列化等隐患
- 技能引导泄露密钥、凭证或个人隐私数据的风险
- 依赖项中的已知漏洞

请**私下**联系,不要直接开公开 issue:

📧 **1833058953@qq.com**(标题注明 `[Security]`)

Please report privately to the email above rather than opening a public issue.

## 响应 / Response

- 我会在合理时间内确认收到并评估。
- 修复后会在 [CHANGELOG.md](CHANGELOG.md) 注明(可匿名致谢)。
- 由于本项目由个人业余维护,响应时间无 SLA 承诺,但会尽力优先处理安全问题。

## 使用者注意 / Note for users

- 运行任何内置脚本前,建议先浏览源码——它们都是可读的纯文本。
- 技能调用外部 API 时不会上传你的代码或数据到第三方,除非该任务明确需要(如检索文献)。涉及上传的操作会提示。
- 安装采用软链接/junction,卸载只需删除客户端技能目录下对应的链接,不影响源仓库。

## 支持范围 / Supported Versions

仅对最新 `master` 提供安全修复。

| 版本 / Version | 支持 / Supported |
| -------------- | ---------------- |
| 最新 master    | ✅               |
| 历史标签       | ❌               |
