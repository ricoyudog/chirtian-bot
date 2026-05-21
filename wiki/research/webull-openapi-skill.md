---
type: wiki
created: 2026-05-17
updated: 2026-05-17
tags: [research, webull, trading, sdk, mcp]
status: active
---

# Webull OpenAPI Skill — 技術研究

> 探索日期：2026-05-17 | 來源：`webull-openapi-skills-main.zip` + `webull-openapi-python-sdk-main.zip`

## 一句話總結

AI Agent 可用的 Webull 交易 Skill，封裝了官方 Python SDK，提供 CLI + MCP Server 兩種使用模式，支援美股/港股/日股 的行情查詢與下單操作。

---

## 兩個 ZIP 的關係

| ZIP | 名稱 | 角色 |
|-----|------|------|
| `webull-openapi-python-sdk-main.zip` | 底層 SDK | Webull 官方 Python SDK（`webull-openapi-python-sdk==2.0.7`） |
| `webull-openapi-skills-main.zip` | AI Skill 層 | 包裝 SDK 為 AI Agent 可操作的 CLI / MCP Server |

Skill 的 `pyproject.toml` 透過 `dependencies` 自動安裝 SDK，**不需要分別安裝**。

---

## 架構（4 層設計）

```
┌─────────────────────────────────────┐
│  AI Agent (Claude / Cursor / ...)    │  ← MCP 或 CLI 呼叫
├─────────────────────────────────────┤
│  cli.py  (dispatch layer)           │  ← 解析 action，路由到對應 handler
├─────────────────────────────────────┤
│  guards.py / risk_engine.py         │  ← 下單前的驗證 & 風控
├─────────────────────────────────────┤
│  sdk_client.py                      │  ← 唯一觸碰 SDK 的層
├─────────────────────────────────────┤
│  webull-openapi-python-sdk          │  ← 官方 SDK（TradeClient / DataClient）
└─────────────────────────────────────┘
```

### 核心模組一覽

| 模組 | 職責 |
|------|------|
| `cli.py` | CLI 入口 + action 路由 dispatcher，三個子命令：`trading`, `market-data`, `auth` |
| `config.py` | `.env` 讀取、`SkillConfig` dataclass、配置驗證 |
| `sdk_client.py` | `SDKClient` — 管理 ApiClient / TradeClient / DataClient 生命週期 |
| `guards.py` | `OrderValidator` — 下單參數驗證（side, quantity, price, region 規則） |
| `risk_engine.py` | `RiskEngine` — 風控檢查（notional 上限、quantity 上限、symbol 白名單） |
| `result.py` | `OperationResult` — 統一回傳結構（ok/detail/payload） |
| `formatters.py` | 輸出格式化（含 region-aware 免責聲明） |
| `audit.py` | 稽核日誌（訂單操作記錄） |
| `region_config.py` | 各 region 的合法 order types / TIF / trading sessions |
| `constants.py` | Enum 常數定義 |
| `env_router.py` | UAT 環境端點路由 |
| `trading/` | 帳戶、持倉、股票/期權/期貨/加密貨幣/事件合約 下單 |
| `market_data/` | 行情快照、K 線、tick、深度、screener、watchlist |

---

## 使用方式

### 1. 安裝

```bash
# 解壓 skills ZIP
unzip webull-openapi-skills-main.zip
cd webull-openapi-skills-main

# 建立虛擬環境（建議）
python3 -m venv .venv
source .venv/bin/activate

# 安裝（會自動安裝 SDK 依賴）
pip install -e .
```

### 2. 配置

```bash
cp .env.example .env
# 編輯 .env，填入：
#   WEBULL_APP_KEY=<your_key>
#   WEBULL_APP_SECRET=<your_secret>
#   WEBULL_REGION_ID=us   # 或 hk, jp
#   WEBULL_ENVIRONMENT=uat  # 沙盒，改 prod 為實盤
```

### 3. 認證（首次使用）

```bash
webull-skill auth
# 在 Webull App 確認 2FA
```

### 4. CLI 操作範例

```bash
# 查帳戶
webull-skill trading --action account-list

# 查行情
webull-skill market-data --action stock-snapshot --symbols AAPL,TSLA

# 下單（建議用 --order-file 避免 shell 引號問題）
echo '{"symbol":"AAPL","side":"BUY","order_type":"LIMIT","limit_price":180,"quantity":10,"instrument_type":"EQUITY","market":"US","time_in_force":"DAY","entrust_type":"QTY","support_trading_session":"CORE","combo_type":"NORMAL"}' > /tmp/order.json
webull-skill trading --action place --account-id <id> --order-file /tmp/order.json
```

### 5. MCP Server 模式（給 AI Agent 用）

```bash
webull-skill mcp
```

設定檔範例（Claude Code `.mcp.json`）：
```json
{
  "mcpServers": {
    "webull": {
      "command": "webull-skill",
      "args": ["mcp"],
      "env": {
        "WEBULL_APP_KEY": "your_app_key",
        "WEBULL_APP_SECRET": "your_app_secret",
        "WEBULL_REGION_ID": "us"
      }
    }
  }
}
```

---

## 支援的操作

### Trading（交易）

| 分類              | Actions                                                                                      | Region     |
| --------------- | -------------------------------------------------------------------------------------------- | ---------- |
| **帳戶**          | `account-list`, `balance`, `position`                                                        | US, HK, JP |
| **股票下單**        | `place`, `preview`, `replace`                                                                | US, HK, JP |
| **Combo Order** | `batch-place` (OTO/OCO/OTOCO)                                                                | US only    |
| **期權下單**        | `option-place`, `option-preview`, `option-replace`, `option-strategy-place`                  | US, HK     |
| **期貨下單**        | `futures-place`, `futures-replace`                                                           | US only    |
| **加密貨幣**        | `crypto-place`                                                                               | US only    |
| **事件合約**        | `event-place`, `event-replace`                                                               | US only    |
| **Algo Order**  | `algo-place` (TWAP/VWAP/POV)                                                                 | US only    |
| **訂單管理**        | `cancel`, `open`, `history`, `detail`                                                        | US, HK, JP |
| **Instrument**  | `instrument-stock`, `instrument-crypto`, `instrument-futures-*`, `instrument-event-*`        | varies     |
| **基本面**         | `instrument-company-profile`, `instrument-analyst-rating`, `instrument-analyst-target-price` | US, HK, JP |

### Market Data（行情）

| 分類 | Actions | Region |
|------|---------|--------|
| **股票** | `stock-snapshot`, `stock-bars`, `stock-batch-bars`, `stock-tick`, `stock-quotes`, `stock-footprint` | US, HK, JP |
| **期貨** | `futures-snapshot`, `futures-bars`, `futures-tick`, `futures-depth`, `futures-footprint` | US only |
| **加密貨幣** | `crypto-snapshot`, `crypto-bars` | US only |
| **事件合約** | `event-snapshot`, `event-depth`, `event-bars`, `event-tick` | US only |
| **Screener** | `stock-gainers-losers`, `stock-most-active` | US, HK, JP |
| **Watchlist** | `watchlist-list`, `watchlist-create`, `watchlist-delete`, ... | US, HK, JP |
| **NOII** | `stock-noii-bars`, `stock-noii-snapshot` | US, HK, JP |

---

## 安全機制

1. **預設沙盒** — `WEBULL_ENVIRONMENT=uat`（paper trading）
2. **風控引擎** — `RiskEngine` 檢查 notional/quantity/symbol whitelist
3. **下單驗證** — `OrderValidator` 檢查 region-specific 規則
4. **MCP 安全規則** — 所有 mutating 操作需使用者確認才能執行（定義在 `SKILL.md`）
5. **AK/SK 不暴露** — 只透過 `.env` 載入，不進 logs 或 output
6. **稽核日誌** — 所有訂單操作記錄，可設 `WEBULL_AUDIT_LOG_FILE`

---

## 配置參數

| 變數 | 必要 | 預設 | 說明 |
|------|------|------|------|
| `WEBULL_APP_KEY` | ✅ | — | App Key |
| `WEBULL_APP_SECRET` | ✅ | — | App Secret |
| `WEBULL_ENVIRONMENT` | ❌ | `uat` | `uat`(沙盒) / `prod`(實盤) |
| `WEBULL_REGION_ID` | ❌ | `us` | `us` / `hk` / `jp` |
| `WEBULL_MAX_ORDER_NOTIONAL_USD` | ❌ | `10000` | 美股單筆上限 (USD) |
| `WEBULL_MAX_ORDER_NOTIONAL_HKD` | ❌ | `80000` | 港股單筆上限 (HKD) |
| `WEBULL_MAX_ORDER_NOTIONAL_CNH` | ❌ | `70000` | A股單筆上限 (CNH) |
| `WEBULL_MAX_ORDER_NOTIONAL_JPY` | ❌ | `1500000` | 日股單筆上限 (JPY) |
| `WEBULL_MAX_ORDER_QUANTITY` | ❌ | `1000` | 單筆最大數量 |
| `WEBULL_SYMBOL_WHITELIST` | ❌ | (無限制) | 白名單（逗號分隔） |
| `WEBULL_CONFIG_DIR` | ❌ | (專案根目錄) | 配置目錄（系統環境變數） |
| `WEBULL_TOKEN_DIR` | ❌ | `<config_dir>/conf/` | Token 存儲目錄 |
| `WEBULL_AUDIT_LOG_FILE` | ❌ | stderr only | 稽核日誌檔案路徑 |
| `WEBULL_LOG_LEVEL` | ❌ | `WARNING` | SDK 日誌等級 |

---

## Region 差異速查

| 功能 | US | HK | JP |
|------|:--:|:--:|:--:|
| 股票交易 | ✅ | ✅ | ✅ |
| 期權 | ✅ | ✅(僅US市場) | ❌ |
| 期貨 | ✅ | ❌ | ❌ |
| 加密貨幣 | ✅ | ❌ | ❌ |
| 事件合約 | ✅ | ❌ | ❌ |
| Combo Order | ✅ | ❌ | ❌ |
| Algo Order | ✅ | ❌ | ❌ |
| Screener | ✅ | ✅ | ✅ |
| Watchlist | ✅ | ✅ | ✅ |
| 基本面 | ✅ | ✅ | ✅ |

---

## 整合到 Christian Bot 的考量

### 方案 A：CLI 整合
- Christian Bot 透過 subprocess 呼叫 `webull-skill` CLI
- 優點：簡單、隔離清楚
- 缺點：每次呼叫都有 SDK 初始化開銷

### 方案 B：MCP Server 整合
- 在 `.mcp.json` 註冊 `webull-skill mcp`
- AI Agent 直接透過 MCP protocol 呼叫
- 優點：最原生的 AI Agent 整合方式
- 缺點：需要 MCP client 支援

### 方案 C：Python import 整合
- 直接 `from webull_skill.sdk_client import SDKClient`
- 在 Bot 的 runtime 中維持長連線 SDK 實例
- 優點：效能最好、可自訂最深
- 缺點：耦合度最高

### 前置需求
1. Webull Developer Account（[developer.webull.com](https://developer.webull.com/apis/home)）
2. API Credentials（App Key + App Secret）
3. Market Data Subscription（需額外訂閱行情）
4. Python 3.10+

---

## 檔案位置（已解壓）

- SDK：`/tmp/corgi-explore/webull-openapi-python-sdk-main/`
- Skill：`/tmp/corgi-explore/webull-openapi-skills-main/`
- 原始 ZIP：專案根目錄 `webull-openapi-python-sdk-main.zip`, `webull-openapi-skills-main.zip`

## 參考文件

- US API: https://developer.webull.com/apis/docs
- HK API: https://developer.webull.hk/apis/docs
- JP API: https://developer.webull.co.jp/apis/docs
- LLM-friendly (US): https://developer.webull.com/apis/llms.txt
- LLM-friendly (HK): https://developer.webull.hk/apis/llms.txt
- GitHub SDK: https://github.com/webull-inc/webull-openapi-python-sdk
- GitHub MCP Server: https://github.com/webull-inc/webull-mcp-server
