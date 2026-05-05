# Calendar Management Demo

OpenClaw 行程管理 demo skill。  
這不是企業正式行事曆系統，而是一個以 SQLite 管理 demo 行程、讓 OpenClaw 可透過 Line 對話展示查詢、建立、修改、取消會議的最小可落地版本。

## OpenClaw Agent Handoff

如果你是 OpenClaw agent，使用這個 repo 時照這段做。

### 1. 安裝到 OpenClaw workspace

```bash
mkdir -p ~/.openclaw/workspace/skills/calendar-management
cp -R skills/calendar-management/. ~/.openclaw/workspace/skills/calendar-management/
```

安裝後驗證：

```bash
openclaw skills info calendar-management --agent main
```

預期看到：

```text
calendar-management ✓ Ready
Visible to model: yes
```

如果 skill 剛複製進去但 agent 看不到，重啟 gateway：

```bash
openclaw config validate
openclaw gateway restart --force --json
openclaw health --json
```

### 2. 使用方式

這個功能不用常駐。OpenClaw gateway 常駐即可；`calendar-management` 是 skill 文件 + Python CLI tools。agent 要查詢或修改行程時，到 skill 目錄執行對應 tool。

```bash
cd ~/.openclaw/workspace/skills/calendar-management
```

查詢行程：

```bash
python tools/query_events.py \
  --db-path db/calendar.db \
  --user-id user_001 \
  --starts-at 2026-05-11T00:00:00+08:00 \
  --ends-at 2026-05-16T00:00:00+08:00
```

建立會議：

```bash
python tools/create_event.py \
  --db-path db/calendar.db \
  --creator-user-id user_002 \
  --participant-user-ids user_003,user_004 \
  --room-id room_B \
  --title 使用者需求討論 \
  --description Demo \
  --starts-at 2026-05-26T14:00:00+08:00 \
  --ends-at 2026-05-26T15:00:00+08:00 \
  --dry-run-line
```

取消會議：

```bash
python tools/cancel_event.py \
  --db-path db/calendar.db \
  --event-id <event_id> \
  --actor-user-id user_002 \
  --dry-run-line
```

### 3. Line Push 判斷

預設 seed 裡的 `Udemo*` 不是可推送的真實 Line user id。沒有真實 id 或 `LINE_CHANNEL_ACCESS_TOKEN` 時，必須使用 `--dry-run-line`。

要真實推送時，先更新 runtime DB：

```bash
sqlite3 ~/.openclaw/workspace/skills/calendar-management/db/calendar.db \
  "UPDATE users SET line_user_id = '<real-line-user-id>' WHERE user_id = 'user_003';"
```

並確保 agent 執行環境能讀到：

```bash
export LINE_CHANNEL_ACCESS_TOKEN="<channel-access-token>"
```

### 4. Agent 回覆規則

- 工具回傳 `ok: true` 才能說建立、修改或取消成功。
- 工具回傳 `participant_conflict` 或 `room_conflict` 時，要列出衝突事件，不要硬建會議。
- 找不到 user mapping 時，不要自動建立使用者；回覆 demo registry 沒有該使用者。
- 沒有真實 Line 設定時，要明講是 dry-run notification。

## 目標

- 用 SQLite 建立 demo-only calendar backend。
- 提供 6 個 calendar tools：查詢、新增、修改、取消、找空檔、找可用會議室。
- 讓 OpenClaw 能載入 `calendar-management` skill。
- 建立/取消會議時可透過 Line push adapter 發送通知。

## 非目標

- 不整合企業正式行事曆。
- 不處理完整 user lifecycle。
- 不做邀請接受/拒絕流程。
- 不做 cron reminder。
- 不把 `calendar.db` 當正式資料源。

## 專案結構

```text
skills/calendar-management/
├── SKILL.md
├── prompt.md
├── skill.json
├── db/
│   ├── init.sql
│   ├── seed.sql
│   └── calendar.db
└── tools/
    ├── calendar_core.py
    ├── query_events.py
    ├── create_event.py
    ├── update_event.py
    ├── cancel_event.py
    ├── find_free_slots.py
    ├── find_available_rooms.py
    └── line_push.py
```

## 安裝與測試

```bash
uv run pytest tests/calendar_management -v
python -m json.tool skills/calendar-management/skill.json >/tmp/calendar-skill.json
```

目前測試覆蓋：

- SQLite schema / seed data。
- 6 個 calendar tools。
- Line push dry-run 與錯誤處理。
- 3 個 demo scenarios。

## 重建 Demo DB

```bash
rm -f skills/calendar-management/db/calendar.db
sqlite3 skills/calendar-management/db/calendar.db < skills/calendar-management/db/init.sql
sqlite3 skills/calendar-management/db/calendar.db < skills/calendar-management/db/seed.sql
```

Seed data 內建：

- 7 位 demo 使用者。
- 2 間 demo 會議室。
- 2026 年 5 月 demo 行程。
- 中文姓名、英文姓名與 `Udemo*` placeholder Line user ids。

## CLI Demo

查詢王大明 2026/5/11 到 2026/5/15 行程：

```bash
python skills/calendar-management/tools/query_events.py \
  --db-path skills/calendar-management/db/calendar.db \
  --user-id user_001 \
  --starts-at 2026-05-11T00:00:00+08:00 \
  --ends-at 2026-05-16T00:00:00+08:00
```

建立會議並使用 Line dry-run：

```bash
python skills/calendar-management/tools/create_event.py \
  --db-path skills/calendar-management/db/calendar.db \
  --creator-user-id user_002 \
  --participant-user-ids user_003,user_004 \
  --room-id room_B \
  --title 使用者需求討論 \
  --description Demo \
  --starts-at 2026-05-26T14:00:00+08:00 \
  --ends-at 2026-05-26T15:00:00+08:00 \
  --dry-run-line
```

取消會議：

```bash
python skills/calendar-management/tools/cancel_event.py \
  --db-path skills/calendar-management/db/calendar.db \
  --event-id <event_id> \
  --actor-user-id user_002 \
  --dry-run-line
```

## 安裝到 OpenClaw

將 skill 複製到 OpenClaw workspace：

```bash
mkdir -p ~/.openclaw/workspace/skills/calendar-management
cp -R skills/calendar-management/. ~/.openclaw/workspace/skills/calendar-management/
```

驗證 OpenClaw 能看到 skill：

```bash
openclaw skills info calendar-management --agent main
```

預期顯示：

```text
calendar-management ✓ Ready
Visible to model: yes
```

必要時重啟 gateway：

```bash
openclaw config validate
openclaw gateway restart --force --json
openclaw health --json
```

## Runtime Model

`calendar-management` 本身不用常駐。它是一組 OpenClaw skill 文件與 Python CLI tools；agent 需要查詢或修改行程時，才會依照 skill 說明呼叫對應腳本。

需要常駐的是 OpenClaw gateway。只要 gateway 正常、skill 已放在 `~/.openclaw/workspace/skills/calendar-management/`，agent 就可以直接呼叫這個 skill。

## Line Push

真實 Line push 需要兩件事：

- 設定 `LINE_CHANNEL_ACCESS_TOKEN`。
- 把 `users.line_user_id` 的 `Udemo*` placeholder 換成真實 Line user ids。

```bash
export LINE_CHANNEL_ACCESS_TOKEN="<channel-access-token>"
```

沒有 token 或真實 Line user id 時，請使用 `--dry-run-line`。Dry-run 仍會寫入 `notification_logs`，可驗證通知流程。

## Demo 場景

1. 查詢個人行程：王大明 2026/5/11 到 2026/5/15。
2. 建立會議：李小美邀請張小志、陳小鳳，2026/5/26 14:00-15:00，會議室 B。
3. 取消會議：取消剛建立的會議，並送出 dry-run Line notification。

## Demo Users

| User ID | 中文姓名 | English Name | Department |
| --- | --- | --- | --- |
| `user_001` | 王大明 | David Wang | 產品 |
| `user_002` | 李小美 | May Lee | 工程 |
| `user_003` | 張小志 | Jason Chang | 設計 |
| `user_004` | 陳小鳳 | Fiona Chen | 市場 |
| `user_005` | 林志強 | Kevin Lin | 業務 |
| `user_006` | 黃雅婷 | Tina Huang | 法遵 |
| `user_007` | 趙建宏 | Henry Chao | 營運 |

## 已驗證狀態

- `uv run pytest tests/calendar_management -v`：18 passed。
- `skill.json`：JSON valid。
- OpenClaw runtime：`calendar-management ✓ Ready`。
- OpenClaw query prompt：可回覆 seeded schedule。
- OpenClaw cancel prompt：可取消 event 並寫入 dry-run notification。
- Real Line push：尚未在此 repo 驗證，原因是本機 shell 沒有 `LINE_CHANNEL_ACCESS_TOKEN`，且 seed 使用 placeholder Line user ids。

詳細操作記錄見 [docs/calendar-management-demo.md](docs/calendar-management-demo.md)。
