## Why

Phase 4 完成了 executor 全棧（Webull adapter、order builder、execution gate、confirmation manager），但系統尚未在時間壓力下跑過完整 pipeline。需要一個觀察期，用模擬倉跑實戰等級測試，收集延遲/錯誤/穩定性數據，作為真錢前的 go/no-go 依據。

## What Changes

- 新增 shadow observation runner：整合現有 pipeline（detection → parse → sizing → execution gate → broker），以模擬倉模式執行，收集每個階段的延遲和結果指標
- 新增 shadow metrics collector：記錄 detection latency、parse latency、TA latency、stale signal rate、NEEDS_REVIEW rate、duplicate prevented count、reconcile mismatch count
- 新增 alert drill infrastructure：端到端 kill switch 演練框架，驗證 alert channel 能在異常時通知 operator
- 觀察期門檻：1 週 + 10 個訊號，最長 4 週
- 觀察期結束後自動產生 shadow run summary（帶日期 note）

## Capabilities

### New Capabilities
- `shadow-observation`: 端到端觀察期 runner，整合現有 pipeline 並在模擬倉執行，追蹤觀察期進度（時間 + 訊號計數），產生 shadow run summary
- `shadow-metrics`: Pipeline 各階段延遲/錯誤/穩定性指標收集與聚合，stale signal 判定（≤5% 閾值），觀察期結束後的指標報告
- `alert-drill`: Kill switch 端到端演練框架，模擬異常觸發 → alert 送達 → operator 確認處理，記錄演練結果

### Modified Capabilities
<!-- 無 — Phase 5 是新增觀察層，不修改現有 spec 行為 -->

## Impact

- `src/` 新增 `shadow/` 模組（observation runner、metrics collector、alert drill）
- `runtime/` 新增 incident note 和 shadow run summary 輸出路徑
- 依賴現有模組：`src/executor/`、`src/portfolio/`、`src/safety/`、`src/state/`、`src/analyzer/`、`src/config/`
- 不修改任何現有 spec 的行為

## GitHub Issue

- Parent: https://github.com/ricoyudog/chirtian-bot/issues/29
- 4 Task Groups: #30 #31 #32 #33
