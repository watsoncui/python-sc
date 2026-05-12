# 离线版 API Key 安全存储方案（Tauri）

> 任务 4：学生在桌面端输入个人 API Key 时的存储/分发安全方案。

## 1. 威胁模型

| 威胁 | 描述 | 优先级 |
|---|---|---|
| T1：磁盘明文泄露 | 同机另一个进程/用户读到 `~/.config/...` 里的 Key | 高 |
| T2：版本控制误提交 | 学生在 GitHub 上传整盘资料夹时含 Key | 高 |
| T3：恶意 Web 内容 | WebView 内执行的第三方脚本读取 `localStorage` 中的 Key | 中 |
| T4：网络中间人 | 代码或第三方依赖把 Key 发往非白名单域名 | 中 |
| T5：内存 dump | 攻击者获得 Python 进程内存，捞出 Key | 低 |

## 2. 分层防御

```
┌─────────────────────────────────────────────────────────────┐
│ 1️⃣  操作系统密钥环（首选）                                    │
│    macOS Keychain · Windows Credential Manager · libsecret  │
└─────────────────────────────────────────────────────────────┘
                       ▲  Tauri 命令（带 capability allowlist）
┌─────────────────────────────────────────────────────────────┐
│ 2️⃣  Rust core (src-tauri)                                    │
│    - tauri-plugin-stronghold / tauri-plugin-keyring         │
│    - secret_get / secret_set / secret_delete / secret_list  │
└─────────────────────────────────────────────────────────────┘
                       ▲  127.0.0.1 + 一次性 token
┌─────────────────────────────────────────────────────────────┐
│ 3️⃣  Python sidecar (LocalProvider)                           │
│    - 仅在 acomplete() 内部 get_secret，调用后立即 del         │
│    - httpx 客户端绑定 KNOWN_ENDPOINTS 白名单                  │
└─────────────────────────────────────────────────────────────┘
                       ▲  IPC（不再持久化）
┌─────────────────────────────────────────────────────────────┐
│ 4️⃣  WebView 前端                                              │
│    - 不存储 Key；仅显示掩码（sk-****abcd）                    │
│    - CSP: connect-src 'self' + 白名单 LLM 端点               │
└─────────────────────────────────────────────────────────────┘
```

## 3. 推荐技术栈：`tauri-plugin-stronghold`（首选）+ `tauri-plugin-keyring`（备选）

### 3.1 为什么选 Stronghold？

* IOTA Foundation 出品，专为客户端密钥存储设计。
* 在 OS 密钥环不可用时回退到 **加密的本地 vault 文件**（同样基于
  ChaCha20-Poly1305 + Argon2id），优于明文 JSON。
* 与 Tauri 同生命周期，关闭应用即解除内存解密。

### 3.2 capability 配置（`src-tauri/capabilities/secret.json`）

```jsonc
{
  "identifier": "secret-store",
  "description": "Allow renderer + sidecar to operate the secret store.",
  "windows": ["main"],
  "permissions": [
    "stronghold:default",
    {
      "identifier": "stronghold:allow-write",
      "allow": [{ "snapshotPath": "$APPLOCALDATA/secrets.stronghold" }]
    }
  ]
}
```

* 显式 allowlist，避免把整个 plugin 暴露给任意命令。
* `snapshotPath` 走 `$APPLOCALDATA` —— OS 限定的应用本地目录，普通用户级权限。

### 3.3 Rust 端 IPC（节选）

```rust
// src-tauri/src/main.rs
#[tauri::command]
async fn secret_set(state: State<'_, AppState>, name: String, value: String)
    -> Result<(), String> {
    state.stronghold
        .store_record(&state.client, name.as_bytes(), value.as_bytes())
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn secret_get(state: State<'_, AppState>, name: String)
    -> Result<Option<String>, String> {
    let bytes = state.stronghold
        .get_record(&state.client, name.as_bytes())
        .await
        .map_err(|e| e.to_string())?;
    Ok(bytes.map(|b| String::from_utf8_lossy(&b).into_owned()))
}
```

* 所有 IO 都在异步任务里完成，不会阻塞 UI。
* Stronghold snapshot 在第一次启动时由 **学生设置的 master passphrase 解锁**；
  passphrase 永不落盘。

### 3.4 Python sidecar 接入

`common/security/keyring_store.py:TauriKeyringStore` 通过一个 `invoke_fn`
注入函数（由 sidecar 启动时构造，本质是经 stdio 与 Rust 通信的小型 RPC）。
若 Tauri 不可用（headless 测试 / 课堂打包前预览），自动退化到
`EncryptedFileStore`（PBKDF2-HMAC-SHA256 600k 轮 + Fernet）。

```python
store = build_default_store(
    mode="desktop",
    tauri_invoke=invoke_fn,                     # 注入 IPC
    fallback_path=Path.home() / ".scicompute" / "keys.enc.json",
    fallback_passphrase=settings.fallback_passphrase,
)
local = LocalProvider(store=store)
```

## 4. 网络出口白名单

Key 拿到后立刻发往 `KNOWN_ENDPOINTS` 中的固定主机：

```python
KNOWN_ENDPOINTS = {
    "openai":      "https://api.openai.com/v1",
    "deepseek":    "https://api.deepseek.com/v1",
    "moonshot":    "https://api.moonshot.cn/v1",
    "siliconflow": "https://api.siliconflow.cn/v1",
    "ollama-local":"http://127.0.0.1:11434/v1",
}
```

Tauri 端再叠一层 CSP（`tauri.conf.json` → `security.csp`）：

```json
"csp": "default-src 'self'; connect-src 'self' https://api.openai.com https://api.deepseek.com https://api.moonshot.cn https://api.siliconflow.cn http://127.0.0.1:* ;"
```

任一第三方 JS 试图把 Key POST 到未列名域名都会被 WebView 拒绝。

## 5. 分发与签名

* **代码签名**：macOS 走 Developer ID + notarization，Windows 走 EV 代码签名，
  Linux 提供 AppImage + GPG `.sig`。
* **更新通道**：使用 Tauri Updater，**强制 ed25519 签名验证**；公钥编译进二进制。
* **可复现构建**：`tauri build` 在 GitHub Actions 中使用固定 toolchain 版本，
  hash 公开在 release page。

## 6. 学生引导式 UX

1. 第一次启动 → 弹窗输入并确认 master passphrase（用于解锁 Stronghold）。
2. 设置页 → “添加 API Key”，按端点白名单下拉选择，输入 sk-… 字符串。
3. 输入后立即调用 `secret_set`，UI 把明文从输入框清空，只保留 `sk-****abcd` 掩码。
4. 切换 “云端助教 / 本地个人 API” 时显示当前模式与最近一次调用的 endpoint。
5. 设置页提供 “导出 / 销毁” 按钮：
   * 导出：要求重新输入 passphrase，生成临时加密 JSON（带过期时间）。
   * 销毁：`secret_delete` + Stronghold snapshot 重新生成空 vault。

## 7. 兜底：如果 Stronghold 也用不了

* `EncryptedFileStore` 已实现完整 fallback；权限文件被 `chmod 0600`，
  passphrase 强制 ≥ 12 字符，路径默认 `$HOME/.scicompute/keys.enc.json`。
* `.gitignore` 模板（脚手架自动写入学生项目）中包含
  `~/.scicompute/`, `*.stronghold`, `*.enc.json` 三条规则，**显著降低 T2 风险**。

## 8. 测试覆盖

* `tests/test_security.py` 验证 EncryptedFileStore 的加密/解密/错密码失败/null
  store 等关键路径；CI 默认运行。
* Tauri 侧由 Rust `cargo test` 单测 IPC capability 路径，并使用 Playwright 做
  WebView e2e（不在本 PR 范围，预留接口）。
