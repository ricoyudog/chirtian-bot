## Context

Phase 4 完成了 executor 全棧（Webull adapter、order builder、execution gate、confirmation manager）。現有模組覆蓋：analyzer（parser + LLM client）、portfolio（sizing + reconcile）、executor（broker integration + confirmation）、safety（runtime guard + idempotency）、state（audit ledger + work queue）。

Phase 5 需要在這些模組之上加一層觀察基礎設施，用模擬倉跑實戰等級測試。Webull 帳戶目前是模擬倉，不需要額外的 shadow mode — 直接跑就是。

決策依據：`wiki/decisions/2026-05-21-phase-5-shadow-live-gates.md`。

## Goals / Non-Goals

**Goals:**
- 端到端觀察期 runner，整合現有 pipeline 在模擬倉執行
- 每個 pipeline stage 的延遲和結果指標收集
- Alert drill 端到端演練框架
- 觀察期結束後自動產生 shadow run summary 和 go/no-go readiness checklist

**Non-Goals:**
- 不建 daemon/poller（那是後續 phase）
- 不建 TA integration（那是後續 phase）
- 不建 alert channel 實際整合（Telegram/Discord/email）
- 不修改現有 spec 的行為
- 不建 live capital / prod mode 支持

## Unknowns & Investigation

- **Substack polling 如何觸發 pipeline？** — 目前沒有 poller 模組。觀察期 runner 需要手動觸發或接收外部事件。結論：Phase 5 先做手動觸發（CLI command 或 Python entry point），poller 留給後續 phase。
- **TA integration 不存在時如何模擬？** — TA latency/unavailable rate 是必要觀察指標，但 TA 模組尚未建。結論：在 metrics collector 中預留 TA stage 的計時點位，觀察期 runner 跳過 TA stage 時記錄為 `TA_SKIPPED`。
- **Stale signal 的精確定義？** — 什麼算「錯過合理執行窗口」？結論：信號時間與實際執行時間差距超過信號的合理窗口（由 config 定義，預設 15 分鐘），且非市場休市造成。

## Decisions

### 1. 新增 `src/shadow/` 模組，不修改現有模組

**Decision:** Phase 5 所有新代碼放在 `src/shadow/`，包含 observation runner、metrics collector、alert drill runner。

**Why:** 不污染現有已驗證的模組。觀察層是橫切關注點，獨立模組方便日後移除或重構。

**Alternatives:** 在每個現有模組中加 metrics hooks — 耦合太高，觀察期結束後難以清理。

### 2. Metrics 寫入現有 AuditLedger，用 event_type prefix 區分

**Decision:** 所有 shadow metrics 使用 `shadow_metric.*` event_type prefix 寫入現有 `AuditLedger`。

**Why:** 複用現有 append-only 基礎設施，不需要新的存儲機制。Query 時用 prefix 過濾。

### 3. 觀察期狀態持久化用 SQLite（復用 WorkQueue 的模式）

**Decision:** 觀察期狀態（start_date, signal_count, metrics 彙總）存在一個 SQLite 檔案 `runtime/shadow_state.db`。

**Why:** 與 WorkQueue 一致的持久化模式，重啟不丟狀態，不需要外部服務。

### 4. Alert drill MVP 只做 console output + audit ledger

**Decision:** Alert drill 的 alert delivery 在 MVP 階段只驗證 console output 和 audit ledger 的 alert event 記錄。

**Why:** 決策文件說「MVP 在真錢前可先使用 console output + audit ledger」。真正的 alert channel（Telegram/Discord）整合在真錢前才需要。

### 5. 觀察期 runner 的入口是 CLI command

**Decision:** 提供 `python -m shadow observe start|stop|status` 作為觀察期的操作入口。

**Why:** 沒有 daemon，手動觸發最直接。與 Webull CLI adapter 的操作模式一致。

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| 手動觸發可能漏掉訊號 | 觀察期本質是測試；漏掉訊號也是觀察數據（detection gap） |
| TA 不存在導致 TA 指標缺失 | Metrics collector 預留 TA stage，標記 `TA_SKIPPED` |
| SQLite 狀態檔損壞 | 使用 WAL mode（與 WorkQueue 一致）；損壞時可重建（觀察期數據在 AuditLedger 有完整副本） |
| 模擬倉行為與真倉不同 | 已知風險；真錢前有 go/no-go gate 把關 |

## Data Model

### ObservationState (SQLite)

```
observation_id: TEXT (UUID)
started_at: TEXT (ISO-8601)
ended_at: TEXT (ISO-8601, nullable)
status: TEXT (active | completed | insufficient_signals)
signals_processed: INTEGER
config_snapshot: TEXT (JSON of RuntimeConfig)
```

### ShadowMetric (AuditLedger event)

```
event_type: "shadow_metric.{stage}"  # e.g. shadow_metric.detection, shadow_metric.parse
data: {
  signal_id: str,
  stage: str,
  latency_ms: float,
  outcome: str,       # success | failure | timeout | stale | deferred | ta_skipped
  error_type: str?,   # only on failure/timeout
  timestamp: str (ISO-8601)
}
```

### DrillResult (file: runtime/incidents/YYYY-MM-DD-drill-kill-switch.md)

```markdown
# Kill Switch Drill — YYYY-MM-DD

- Type: kill_switch
- Started: HH:MM:SS
- Ended: HH:MM:SS
- Duration: N seconds
- Result: PASS | FAILED
- Failure Reason: (if failed)
- Alert Channel: console
- Operator Confirmation: (timestamp or "no response")
```

## API Contracts

Not applicable — Phase 5 不涉及 API surface changes。入口是 CLI command 和 Python module。
