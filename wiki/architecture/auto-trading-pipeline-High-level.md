---
type: wiki
created: 2026-05-18
updated: 2026-05-20
tags: [architecture, trading, pipeline, mcp, substack, webull]
status: active
---

# Auto Trading Pipeline — 系統架構

> 自動跟單 Christian 交易的完整 pipeline：爬蟲 → 解析 → 風控 → 下單

## 一句話

30 秒輪詢 Christian 的 Substack，解析交易指令，AI 風控評估後，自動透過 Webull MCP 下單（預設沙盒）。

---

## 架構總覽

```
┌───────────────────────────────────────────────────────────────────┐
│                  christian-bot (Python daemon)                     │
│                                                                    │
│  ┌───────────┐  new_post   ┌────────────────┐  ParsedInstruction  │
│  │  Poller    │ ──────────→ │ Instruction     │ ────────────────┐  │
│  │ (Module 1) │   event     │ Parser          │                  │  │
│  └───────────┘              └────────────────┘                  │  │
│       │ saves                    │ pure LLM                     │  │
│       │ christian log/           │ + 例子集合作為上下文          │  │
│       │              ┌────────────────────────┐                  │  │
│       │              │ TradingAgents          │  APPROVE /       │  │
│       │              │ (Module 2)             │  REJECT /        ▼  │
│       │              │ 12-Agent Deep Analysis │  MODIFY    ┌──────┐│
│       │              │ Bull↔Bear 辯論         │            │Gate  ││
│       │              │ 風控辯論               │───────────→│      ││
│       │              │ Portfolio Manager      │            │  ▼   ││
│       │              └────────────────────────┘            │Exec  ││
│       │                                                    │utor  ││
│       │              REJECT → log & skip                   │(Mod 3││
│       │              MODIFY → human review                 │      ││
│       │                                                    └──────┘│
│  ┌──────────────────────────────────────────┐                      │
│  │   Config, State & Portfolio Ledger       │                      │
│  │   config.yaml / state.json / portfolio/  │                      │
│  └──────────────────────────────────────────┘                      │
└───────────────────────────────────────────────────────────────────┘

TradingAgents 詳見：[[wiki/research/tradingagents-multiagent]]
```

---

## Module 1: Poller（Substack 爬蟲）

### 職責
每 30 秒輪詢 `christian1hedge.substack.com`，偵測新帖文，存入 `christian log/`。

### 核心組件

| 組件 | 職責 |
|------|------|
| `SubstackClient` | 包裝 `mcp-substack` MCP server，抓取帖文列表 + 全文 |
| `PostDetector` | 比對 `state.json.last_known_post_date` vs Substack feed，偵測新帖 |
| `PostSaver` | 將新帖文寫入 `christian log/YYYY-MM/DD/標題.md`（含 YAML frontmatter） |
| `PollerScheduler` | 30 秒事件循環，錯誤時指數退避（30s → 60s → 120s → 300s cap） |

### 新帖偵測邏輯
1. 讀 `state.json` → `last_known_post_date`
2. 呼叫 `mcp-substack` → 取得最近帖文列表
3. 過濾 `publish_date > last_known_post_date` 的帖文
4. 對每篇新帖：下載全文 → 存檔 → 更新 state → 發出 event

### Event 格式
```json
{
  "type": "new_post",
  "timestamp": "2026-05-18T22:30:00+08:00",
  "post_title": "2026年5月18日美股港股",
  "post_url": "https://christian1hedge.substack.com/p/2026518",
  "file_path": "christian log/2026-05/18/2026年5月18日美股港股.md",
  "raw_content": "..."
}
```

### 依賴
- `mcp-substack` MCP server（已安裝在 `.mcp.json`）
- 需已登入付費帳號

---

## Module 2a: Instruction Parser（交易指令解析器）

### 職責
解析帖文中的交易指令，輸出結構化的 `ParsedInstruction`，並決定是否觸發下游研究。

### 核心設計：純 LLM + 語言模式參考

**不使用 Regex**。直接用 LLM 解析，並將 `christian-trading-language.md`（從 1297 篇帖文中收集到的所有例子和模式）
作為 **LLM 的參考上下文**（few-shot examples），讓 LLM 理解 Christian 的語言習慣。

> **注意**：`christian-trading-language.md` 不是預先打包好的 skill，
> 而是我們從 `christian log/` 中找到的所有 Christian 交易語言的例子集合。
> 未來可能會做成正式的 skill，但目前就是純粹的參考資料。

```
帖文文字
  │
  ▼
LLM (Claude) + christian-trading-language.md 作為上下文
  → 參考收集到的例子理解 Christian 的語言模式
  → 只提取已發生的交易操作（忽略分析、預期、條件句式）
  → 輸出 ParsedInstruction[] 或 no-op
```

### 為什麼純 LLM 而非 Regex？

| 面向 | Regex-first（舊方案） | 純 LLM + 例子參考（新方案） |
|------|----------------------|--------------------------|
| 開發成本 | 高 — 需維護 ~40 條 regex 模板 | 低 — 例子已收集好 |
| 格式變化容忍度 | 低 — 遇新變體要改 regex | 高 — LLM 天然泛化 |
| 準確率 | 高（已知模板）/ 0（未知格式） | 高（全面） |
| 維護成本 | 高 — Christian 格式持續演進 | 低 — 持續補充例子即可 |
| 執行速度 | 快（ms 級） | 稍慢（~1-2s API 呼叫） |
| 成本 | 免費 | ~$0.01/次 Claude 呼叫 |

> **關鍵洞察**：我們已經從 1297 篇帖文中收集了 Christian 所有交易語言的例子，
> 這些例子本身就是最好的 LLM prompt — 不需要額外翻譯成 regex。

### 參考材料的內容

`christian-trading-language.md` 目前收集了：
1. **做多例子** — 18 種表述方式（含具體日期和原文）
2. **做空例子** — 9 種表述方式
3. **平倉例子** — 14 種表述方式
4. **期權例子** — 8 種表述方式
5. **市場標識符** — `美股`/`港股`/`adr`
6. **時間修飾語** — `開盤後`/`收盤前`/`下午` 等
7. **倉位管理詞彙** — `輕倉`/`重倉`/`清倉`/`調倉`
8. **條件觸發句式** — `逢低加倉`/`逢高減倉`/`如果...會...`
9. **倍數 ETF 映射** — `amdl` = 2x AMD, `nvdl` = 2x NVDA 等
10. **帖文標題格式演進** — 2025-03 ~ 2026-05 的格式變化

### 解析範圍：只管操作，不管分析

**只提取已發生的交易操作**，忽略：

| 類型 | 範例 | 處理 |
|------|------|------|
| ✅ **具體操作** | `加倉 nvda 1%`、`賣出全部 tsla`、`cover short pltr` | 提取 |
| ✅ **無操作通知** | `今天沒有操作` | 標記 no-op |
| ❌ **市場分析** | `總體看漲美股`、`投資往回看都是確定性` | 跳過 |
| ❌ **未來預期** | `準備下週做空泡泡瑪特`、`等回調後重新建倉` | 跳過 |
| ❌ **條件意圖** | `逢低加倉做多 nvda`、`如果明天弱勢會削減 nvdl` | 跳過 |
| ❌ **月度總結** | `3月-8月總結` | 跳過 |
| ❌ **解釋性文字** | `(short call是做空的意思)`、風險管理建議 | 跳過 |

### 解析後的結構化指令
```json
{
  "action": "buy|sell|short|cover|option_place|option_cover",
  "symbol": "NVDA",
  "side": "long|short",
  "quantity_pct": 1.0,
  "market": "US|HK",
  "order_type": "MARKET|LIMIT",
  "time_modifier": "immediate|open|close|scheduled",
  "instrument_type": "EQUITY|OPTION|ETF",
  "option_details": {
    "type": "call|put",
    "option_side": "long|short",
    "expiry": "2026-07-17",
    "strike": 270.0
  },
  "raw_text": "今天加倉 nvda 1%"
}
```

### 依賴
- `wiki/research/christian-trading-language.md` — 收集到的語言例子，作為 LLM 上下文
- Claude API（`ANTHROPIC_API_KEY`）

---

## Module 2b: TradingAgents（深度交易分析）

### 職責
使用開源 TradingAgents 框架對目標股票進行 12-Agent 深度分析，輸出最終交易決策。

> **完整文件**：[[wiki/research/tradingagents-multiagent]]
> **原始碼**：`/Users/chunsingyu/softwares/TradingAgents/`

### 為什麼用 TradingAgents 而不是自建？

| 面向 | 自建 RiskEvaluator | TradingAgents |
|------|--------------------|---------------|
| 分析深度 | 單一 LLM 呼叫 | 12 Agent × 多輪辯論 |
| 市場覆蓋 | 只有 Webull 即時行情 | Market + Social + News + Fundamentals |
| 風控 | 硬編碼規則 | 3 位風控 Agent 辯論（Aggressive / Conservative / Neutral） |
| 決策品質 | 基礎 | Bull↔Bear 對抗 + Portfolio Manager 結構化輸出 |
| 記憶 | 無 | 自動記錄歷史決策 & 計算 realized return |

### 整合方式

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "deepseek"
config["deep_think_llm"] = "deepseek-v4-pro"
config["quick_think_llm"] = "deepseek-v4-pro"
config["max_debate_rounds"] = 5
config["max_risk_discuss_rounds"] = 5
config["output_language"] = "Chinese"

ta = TradingAgentsGraph(
    selected_analysts=["market", "social", "news", "fundamentals"],
    debug=False,
    config=config,
)

# 從 ParsedInstruction 取 symbol → 餵入 TradingAgents
_, decision = ta.propagate(parsed.symbol, analysis_date)
# decision = PortfolioDecision：rating / price_target / investment_thesis ...
```

### 在 Pipeline 中的角色

```
ParsedInstruction (symbol, action)
       │
       ▼
TradingAgents.propagate(symbol, date)
       │
       │  Agent 流程（~15-30 min Deep 模式）：
       │  Market Analyst → Social Analyst → News Analyst → Fundamentals Analyst
       │  → Bull↔Bear 辯論 (5 輪) → Research Manager
       │  → Trader → 風控辯論 (5 輪) → Portfolio Manager
       │
       ▼
PortfolioDecision
  ├── rating: Buy / Overweight / Hold / Underweight / Sell
  ├── price_target: 180.0
  ├── investment_thesis: "..."
  └── executive_summary: "..."
       │
       ▼
結合 Christian 的原始指令 + PortfolioDecision → 最終 Recommendation
```

### 決策融合邏輯

| Christian 指令 | TradingAgents 評級 | 最終決策 |
|----------------|---------------------|----------|
| BUY | Buy / Overweight | ✅ APPROVE |
| BUY | Hold | ⚠️ MODIFY（縮小倉位 / 需確認） |
| BUY | Underweight / Sell | ❌ REJECT（AI 認為不應買） |
| SELL | Buy / Overweight | ⚠️ MODIFY（建議持有 / 需確認） |
| SELL | Underweight / Sell | ✅ APPROVE |
| 任何 | — | 風控上限檢查仍適用 |

### 基本風控檢查（仍保留）

| 檢查 | 預設值 |
|------|--------|
| 單筆 notional 上限 | $10,000 USD |
| 單筆 quantity 上限 | 1,000 股 |
| Symbol whitelist | 全部允許 |
| 單一持倉集中度上限 | 10% |
| 重複單偵測窗口 | 5 分鐘 |
| 交易時段檢查 | 美股/港股 交易時段內 |

### Recommendation 輸出
```json
{
  "decision": "APPROVE|REJECT|MODIFY|SKIP|NEEDS_REVIEW",
  "confidence": 0.85,
  "christian_action": "BUY",
  "ta_rating": "Buy",
  "ta_price_target": 180.0,
  "ta_thesis": "...",
  "reason": "Christian 買入 + TradingAgents Buy，方向一致",
  "risk_assessment": { "notional_usd": 500, "within_limits": true },
  "sizing": {
    "target_pct": 1.0,
    "basis": "portfolio_equity",
    "target_notional_usd": 500,
    "estimated_price": 180.0,
    "order_quantity": 2,
    "unfilled_residual_usd": 140.0,
    "sizing_decision": "EXECUTABLE"
  }
}
```

### 依賴
- TradingAgents 原始碼：`/Users/chunsingyu/softwares/TradingAgents/`
- DeepSeek API（`DEEPSEEK_API_KEY`）
- `.env` 位置：`/Users/chunsingyu/softwares/TradingAgents/.env`

---

## Module 2c: Portfolio State & Sizing（本地倉位簿 + 下單換算）

### 職責
把 Christian 的 `quantity_pct`（例如 1%）轉換成「本帳戶現在可執行的訂單數量」，並在本地維護一份可審計的倉位/資金狀態。

> 核心原則：**百分比是目標風險/倉位，不等於保證下單成功。**
> SizingEngine 必須同時考慮總資產、可用購買力、現有持倉、最小交易單位、價格快照和風控上限。

### 為什麼需要本地紀錄？
Webull 是真實來源（source of truth），但本地仍需要 Portfolio Ledger：

| 需求 | 原因 |
|------|------|
| 重啟後知道已處理/待成交訂單 | 避免重複下單或漏補狀態 |
| 快速計算 Christian 的 1% 對應金額 | 不必每一步都重新推導 |
| 保存每次 sizing 的理由 | 之後 audit「為什麼買 1 股而不是 2 股」 |
| 對帳 | Webull 回報、成交事件、本地預期不一致時可告警 |
| 支援 paper/UAT | 沒有真實成交時也能跑完整 pipeline |

### 資料來源優先級

1. **Webull account balance / positions / orders** — 啟動時與下單前同步，是真實來源。
2. **本地 `portfolio/ledger.jsonl`** — append-only 事件簿，記錄 signal、sizing、order、fill、reconcile。
3. **本地 `portfolio/snapshot.json`** — 由 ledger + 最近一次 Webull sync 產生的快照，只作快取，可重建。
4. **`state.json.pending_orders`** — 只保留 pipeline 佇列狀態，不承擔完整倉位簿職責。

### 核心組件

| 組件 | 職責 |
|------|------|
| `PortfolioSync` | 啟動時/下單前查 Webull balance、positions、open orders，更新 snapshot |
| `PortfolioLedger` | append-only 記錄 signal、sizing decision、order request、fill、cancel、reconcile |
| `BuyingPowerCalculator` | 取得可用現金/購買力，按市場與帳戶類型做保守折扣 |
| `SizingEngine` | 將 `quantity_pct` 轉成目標 notional、股數、餘額殘差與 sizing decision |
| `Reconciler` | 比對本地 snapshot 與 Webull 實際持倉；不一致則暫停自動下單 |

### Sizing 基準

預設用 **portfolio equity** 計算 Christian 的百分比，而不是只用 cash：

```text
target_notional = portfolio_equity_usd * quantity_pct / 100
cash_cap        = available_buying_power_usd * buying_power_buffer
risk_cap        = min(max_notional_usd, concentration_remaining_usd, cash_cap)
executable_notional = min(target_notional, risk_cap)
```

預設參數：

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `sizing_basis` | `portfolio_equity` | 1% = 總資產 1%，不是剩餘現金 1% |
| `buying_power_buffer` | `0.98` | 保留 2% 給價格滑點、匯率、費用 |
| `min_residual_notional_usd` | `25` | 殘差小於此值不補單 |
| `price_slippage_buffer_pct` | `0.5` | 市價/限價估算加 buffer |
| `rounding_mode` | `floor` | 不因四捨五入而超買 |
| `fractional_shares_enabled` | `false` | 初期不假設支援碎股；可由帳戶 permission 開啟 |

### 百分比 → 股數演算法

```python
def size_order(instruction, portfolio, quote, config):
    target_notional = portfolio.equity_usd * instruction.quantity_pct / 100
    max_spend = min(
        target_notional,
        portfolio.buying_power_usd * config.buying_power_buffer,
        config.risk.max_notional_usd,
        concentration_remaining_usd(instruction.symbol, portfolio, config),
    )

    effective_price = quote.ask_or_last * (1 + config.price_slippage_buffer_pct / 100)
    min_qty = instrument_min_quantity(instruction.symbol, instruction.market)
    lot_size = instrument_lot_size(instruction.symbol, instruction.market)

    if config.fractional_shares_enabled and instrument_allows_fractional(instruction):
        qty = floor_to_increment(max_spend / effective_price, min_qty)
    else:
        qty = floor(max_spend / effective_price / lot_size) * lot_size

    if qty < min_qty:
        return SizingDecision("SKIP_TOO_SMALL", target_notional, max_spend, qty)

    return SizingDecision("EXECUTABLE", target_notional, qty * effective_price, qty)
```

### 邊界情境處理

| 情境 | 例子 | 決策 |
|------|------|------|
| 1% 金額不足一股/一手 | 總資產 $5,000，NVDA $180，1%=$50 | `SKIP_TOO_SMALL` 或如開啟碎股則買碎股 |
| 可用購買力不足 | 1%=$500，但 buying power 只剩 $210 | 降到可買整數股；若不足最小單位則 `SKIP_INSUFFICIENT_BUYING_POWER` |
| 只能買一手 | 港股 lot size=100，目標金額只夠 60 股 | 不追高補足；`SKIP_TOO_SMALL_LOT`，除非策略允許升級到一手且仍在風控內 |
| 買入後集中度超過 10% | 現有 NVDA 已佔 9.8%，再買 1% 會到 10.8% | 裁剪到剩餘 0.2%；不足最小單位則 `MODIFY_OR_SKIP` |
| Christian 說加倉但本地沒有該持倉 | `加倉 TSLA 1%`，snapshot TSLA=0 | 視為新建倉，但 `reason` 標記 `ADD_WITH_ZERO_POSITION` 供審核 |
| Christian 說減倉/賣出但持倉不足 | 要賣 1%，實際只剩 0.4% | 只賣現有可賣數量；不足最小單位則 `SKIP_NO_POSITION` |
| open order 未成交 | 上一筆同 symbol BUY 還在掛單 | 暫停新單或合併計算 exposure，避免重複加倉 |
| Webull 與本地不一致 | Webull position != snapshot | `NEEDS_RECONCILIATION`，禁止 auto 下單 |
| 報價過舊 | quote timestamp 超過上限 | `NEEDS_FRESH_QUOTE`，重新拉 quote |
| FX 不確定 | 港股 HKD、美股 USD 混合 | 統一轉 USD equity 計算，使用最新 FX；缺 FX 則 `NEEDS_REVIEW` |

### SizingDecision 輸出

```json
{
  "sizing_decision": "EXECUTABLE|MODIFY_SIZE|SKIP_TOO_SMALL|SKIP_INSUFFICIENT_BUYING_POWER|NEEDS_RECONCILIATION|NEEDS_REVIEW",
  "basis": "portfolio_equity",
  "portfolio_equity_usd": 50000,
  "available_buying_power_usd": 1200,
  "target_pct": 1.0,
  "target_notional_usd": 500,
  "capped_notional_usd": 500,
  "estimated_price": 180.0,
  "lot_size": 1,
  "min_quantity": 1,
  "order_quantity": 2,
  "estimated_order_notional_usd": 360,
  "unfilled_residual_usd": 140,
  "reason_codes": ["ROUNDED_DOWN_TO_LOT_SIZE", "RESIDUAL_BELOW_NEXT_SHARE"]
}
```

### Pipeline 位置

```
Recommendation (APPROVE/MODIFY candidate)
  → PortfolioSync.refresh()
  → Reconciler.assert_consistent()
  → SizingEngine.size(instruction, portfolio_snapshot, quote)
      → EXECUTABLE       → Executor
      → MODIFY_SIZE      → confirmation / log
      → SKIP_*           → AuditLogger.log_skip()
      → NEEDS_*          → human review
```

### 本地 portfolio 檔案

```text
portfolio/
├── ledger.jsonl       # append-only，不手改；每行一個事件
├── snapshot.json      # 可重建快照；啟動時可被 Webull sync 覆蓋
└── reconciliations/   # 每次對帳差異報告
```

`ledger.jsonl` 事件範例：

```json
{"ts":"2026-05-20T22:30:00+08:00","type":"sizing_decision","symbol":"NVDA","target_pct":1.0,"target_notional_usd":500,"order_quantity":2,"decision":"EXECUTABLE","reason_codes":["ROUNDED_DOWN_TO_LOT_SIZE"]}
```

### 不變式（hard invariants）

1. **永遠不超過可用購買力**：買入 notional 必須小於 `buying_power * buffer`。
2. **永遠不超過風控上限**：notional、quantity、concentration 任一超限都要裁剪或拒絕。
3. **永遠向下取整**：未開碎股時，股數只能 `floor` 到 lot size，不可四捨五入超買。
4. **本地與 Webull 不一致時不自動下單**：先 reconcile，再恢復 auto。
5. **所有 sizing 都要可審計**：即使 SKIP，也寫入 ledger 與 audit log。

---

## Module 3: Executor（Webull 下單器）

### 職責
將 APPROVED 的交易指令轉換為 Webull 訂單並執行。

### 核心組件

| 組件 | 職責 |
|------|------|
| `WebullMCPClient` | 透過 `webull-skill mcp` 下單 / 預覽 / 查帳戶 |
| `OrderBuilder` | 將 ParsedInstruction 轉為 Webull order JSON |
| `ExecutionGate` | 環境檢查 + 人員確認閘門 + 重複單擋 |
| `AuditLogger` | 所有下單嘗試 & 結果的稽核日誌 |

### 下單流程
```
Recommendation (APPROVE)
  → ExecutionGate
      → 環境檢查（預設必須 UAT）
      → 人員確認（confirmation_mode: confirm / auto / skip）
      → 重複單檢查
  → OrderBuilder
      → SizingDecision → Webull order JSON
      → 不再自行把百分比換股數；只接受已驗證的 order_quantity
  → WebullMCPClient.preview_order()
  → WebullMCPClient.place_order()
  → AuditLogger.log()
```

### Webull Order JSON 格式
```json
{
  "symbol": "AAPL",
  "side": "BUY",
  "order_type": "LIMIT",
  "limit_price": 180.0,
  "quantity": 10,
  "instrument_type": "EQUITY",
  "market": "US",
  "time_in_force": "DAY",
  "entrust_type": "QTY",
  "support_trading_session": "CORE",
  "combo_type": "NORMAL"
}
```

### 安全機制
- **預設 UAT 沙盒** — `WEBULL_ENVIRONMENT=uat`
- **人員確認閘門** — 所有 mutating 操作預設需確認
- **風控上限** — notional / quantity / symbol whitelist
- **稽核日誌** — 所有訂單操作記錄
- **AK/SK 不暴露** — 只透過 `.env`

### 依賴
- `webull-skill mcp` MCP server（待安裝配置）
- Webull API credentials（APP_KEY + APP_SECRET）
- 技術研究：[[wiki/research/webull-openapi-skill]]

---

## Config & State

### `config.yaml`（專案根目錄）
```yaml
poller:
  interval_seconds: 30
  substack_publication: "christian1hedge"
  save_path: "christian log"

parser:
  mode: "llm_context"          # 純 LLM + 語言模式例子作為上下文
  context_source: "wiki/research/christian-trading-language.md"  # 收集到的例子集合
  confidence_threshold: 0.7    # 低於此值標記 NEEDS_REVIEW

tradingagents:
  source: "/Users/chunsingyu/softwares/TradingAgents"
  llm_provider: "deepseek"
  deep_think_llm: "deepseek-v4-pro"
  quick_think_llm: "deepseek-v4-pro"
  max_debate_rounds: 5
  max_risk_discuss_rounds: 5
  output_language: "Chinese"
  analysts: ["market", "social", "news", "fundamentals"]

analyzer:
  # 決策融合
  approve_on_agreement: true       # Christian + TA 同方向 → 自動 APPROVE
  reject_on_opposition: false      # 方向相反 → MODIFY（需確認），不自動 REJECT
  # 基本風控
  max_portfolio_concentration_pct: 10
  duplicate_window_seconds: 300

portfolio:
  sync_on_startup: true
  sync_before_order: true
  sizing_basis: "portfolio_equity"  # portfolio_equity | buying_power | cash
  buying_power_buffer: 0.98
  price_slippage_buffer_pct: 0.5
  rounding_mode: "floor"
  fractional_shares_enabled: false
  min_residual_notional_usd: 25
  require_reconcile_before_auto_order: true

executor:
  environment: "uat"          # uat | prod
  confirmation_mode: "confirm" # auto | confirm | skip
  risk:
    max_notional_usd: 10000
    max_quantity: 1000
    symbol_whitelist: []
```

### `state.json`（gitignored）
```json
{
  "last_known_post_date": "2026-05-18T00:00:00Z",
  "last_poll_timestamp": "2026-05-18T22:30:00+08:00",
  "processed_posts": ["2026518"],
  "pending_orders": [],
  "portfolio_sync": {
    "last_sync_timestamp": null,
    "last_reconcile_status": "unknown"
  }
}
```

### `.env`（gitignored）
```
WEBULL_APP_KEY=xxx
WEBULL_APP_SECRET=xxx
WEBULL_ENVIRONMENT=uat
WEBULL_REGION_ID=us
```

---

## 目錄結構

```
christian-bot/
├── src/
│   ├── main.py                  # Daemon 入口
│   ├── poller/
│   │   ├── client.py            # SubstackClient
│   │   ├── detector.py          # PostDetector
│   │   ├── saver.py             # PostSaver
│   │   └── scheduler.py         # PollerScheduler
│   ├── analyzer/
│   │   ├── parser.py            # InstructionParser (Module 2a) — 純 LLM + 例子上下文
│   │   ├── context_loader.py    # 載入 christian-trading-language.md 作為 LLM 上下文
│   │   ├── decision_fusion.py   # Christian vs TradingAgents 決策融合
│   │   └── risk.py              # 基本風控上限檢查
│   ├── portfolio/
│   │   ├── sync.py              # PortfolioSync — Webull balance/positions sync
│   │   ├── ledger.py            # PortfolioLedger — append-only local events
│   │   ├── sizing.py            # SizingEngine — pct → executable quantity
│   │   └── reconcile.py         # Reconciler — local vs Webull consistency
│   ├── executor/
│   │   ├── webull_client.py     # WebullMCPClient
│   │   ├── order_builder.py     # OrderBuilder
│   │   ├── gate.py              # ExecutionGate
│   │   └── audit.py             # AuditLogger
│   └── config/
│       └── settings.py          # Pydantic settings
├── config.yaml
├── state.json                   # gitignored
├── portfolio/                    # gitignored runtime ledger/snapshots
│   ├── ledger.jsonl
│   ├── snapshot.json
│   └── reconciliations/
├── .env                         # gitignored
├── tests/
│   ├── test_parser.py
│   ├── test_risk.py
│   ├── test_decision_fusion.py
│   ├── test_sizing.py
│   ├── test_reconcile.py
│   ├── test_order_builder.py
│   └── test_integration.py
├── pyproject.toml
└── christian log/               # (existing)

# 外部依賴（Python import，非複製）
/Users/chunsingyu/softwares/TradingAgents/   # TradingAgents (Module 2b)
```

---

## 實作順序

| Phase | Module | 重點 |
|-------|--------|------|
| 1 | Scaffolding | pyproject.toml, config.yaml, settings, .env.example |
| 2 | Poller | mcp-substack 整合, 30s loop, 新帖偵測, 存檔 |
| 3 | Parser | 純 LLM + christian-trading-language 例子作為上下文, 單元測試 |
| 4 | TradingAgents 整合 | Python import TradingAgents, Deep 設定, 決策融合邏輯 |
| 5 | 風控 & 決策融合 | 基本上限檢查, Christian vs TA 對照表, Recommendation 輸出 |
| 6 | Portfolio State & Sizing | 本地 ledger/snapshot, Webull sync, 1%→股數, 一手/買力/集中度邊界測試 |
| 7 | Executor | Webull MCP 整合, OrderBuilder, ExecutionGate, AuditLog |
| 8 | Integration | main.py daemon, 全 pipeline 測試, 錯誤恢復 |
| 9 | Polish | wiki 更新, UAT 測試, operational runbook |

---

## 關鍵設計決策

| 決策 | 原因 |
|------|------|
| **Event-driven in-process** | 單人系統，不需要 message queue，直接 function call chain |
| **純 LLM + 例子上下文** | 從 1297 篇帖文中收集了所有 Christian 交易語言的例子，直接作為 LLM 上下文，無需維護 regex |
| **TradingAgents 取代自建風控** | 12-Agent 辯論 >> 單一 LLM 呼叫，已有完整的 Market/Social/News/Fundamentals 分析 + Bull↔Bear 對抗 + 3 人風控辯論（見 [[wiki/research/tradingagents-multiagent]]） |
| **決策融合（Christian × AI）** | 不是盲從 Christian，也不是盲從 AI。兩者方向一致才自動 APPROVE，衝突時需確認 |
| **Sizing 獨立成 Portfolio 層** | Christian 的 1% 是目標倉位；真正下單前必須按本地/券商持倉、買力、lot size、風控上限裁剪 |
| **MCP 整合** | Substack & Webull 都已有 MCP server，原生 AI Agent 支援 |
| **人員確認閘門** | 遵循 hard constraint：所有 mutating 操作需使用者確認 |
| **UAT-first** | 遵循 hard constraint：下單操作預設沙盒 |

---

## 錯誤處理

| 錯誤 | 模組 | 處理方式 |
|------|------|---------|
| Substack auth 過期 | Poller | 暫停輪詢 → 通知使用者 |
| Substack rate limit | Poller | 指數退避（30s → 300s cap） |
| 解析失敗 | Parser | 標記 `NEEDS_REVIEW` → 跳過執行 |
| TradingAgents 超時 | TradingAgents | Deep 模式 ~30 min 上限，超時 → fallback 到 Medium 或直接用 Parser 結果 + 基本風控 |
| TradingAgents API 錯誤 | TradingAgents | 重試 1 次 → fallback 同上 |
| Webull API 不可用 | Executor | 佇列 → 重試 3 次 → 通知 |
| 本地與 Webull 持倉不一致 | Portfolio | `NEEDS_RECONCILIATION` → 暫停 auto 下單 → 對帳 |
| 1% 不足最小交易單位 | Portfolio | `SKIP_TOO_SMALL` / `SKIP_TOO_SMALL_LOT` + audit log |
| 購買力不足 | Portfolio | 向下裁剪到可買數量；不足最小單位則 SKIP |
| 風控超限 | Analyzer/Portfolio | 自動 REJECT 或裁剪成 `MODIFY_SIZE` + 原因 |
| 重複訂單 | Executor | 跳過 + log warning |

---

## 參考

- Christian 交易語言模式：[[wiki/research/christian-trading-language]]
- **TradingAgents 框架**：[[wiki/research/tradingagents-multiagent]] — Module 2b 核心引擎
- Webull OpenAPI Skill 研究：[[wiki/research/webull-openapi-skill]]
- 現有帖文資料：`christian log/`（2025-03 至 2026-05）
