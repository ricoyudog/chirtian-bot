---
type: wiki
created: 2026-05-18
updated: 2026-05-20
tags: [research, trading, multi-agent, langgraph, deepseek]
status: active
---

# TradingAgents 多 Agent 交易分析框架

> 開源多 Agent 框架，用於深度股票分析。基於 LangGraph + LangChain，支援多種 LLM Provider。目前版本 **v0.2.5**。

## 一句話

12 個 LLM Agent 分 5 個團隊接力分析一支股票：4 分析師 → 多輪辯論 → Trader → 風控辯論 → 最終決策。

---

## 快速啟動

### CLI 互動式（推薦新手）

```bash
cd /Users/chunsingyu/softwares/TradingAgents
source .venv/bin/activate
tradingagents
```

互動式 8 步選單：

| 步驟 | 選項 | 最深設定 |
|------|------|---------|
| 1. Ticker | 輸入股票代碼 | 如 `NVDA`, `0700.HK` |
| 2. Date | 分析日期 YYYY-MM-DD | 當日或歷史日期 |
| 3. Language | 報告語言 | Chinese |
| 4. Analysts | 分析師（可多選） | 全選（按 `a`） |
| 5. Research Depth | 辯論輪數 | **Deep** (= 5 輪) |
| 6. LLM Provider | AI 供應商 | DeepSeek（官方 API） |
| 7. Thinking Agents | 模型選擇 | Deep: V4 Pro, Quick: V4 Pro |
| 8. Effort | 推理強度 | max（PackyAPI 時自動啟用，官方 API 不需要） |

### Python 程式化（推薦整合）

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from dotenv import load_dotenv

load_dotenv()

config = DEFAULT_CONFIG.copy()

# === 最深分析設定 ===
config["llm_provider"] = "deepseek"
config["deep_think_llm"] = "deepseek-v4-pro"      # 關鍵決策用
config["quick_think_llm"] = "deepseek-v4-pro"      # 分析 & 辯論用
config["max_debate_rounds"] = 5                    # Bull/Bear 辯論 5 輪
config["max_risk_discuss_rounds"] = 5              # 風控辯論 5 輪
config["output_language"] = "Chinese"

ta = TradingAgentsGraph(
    selected_analysts=["market", "social", "news", "fundamentals"],
    debug=True,
    config=config,
)

_, decision = ta.propagate("NVDA", "2026-05-20")
print(decision)
```

---

## Agent 流程

```
START
  │
  ▼
┌─────────────────────────────────────────────┐
│  I. Analyst Team（4 位，quick_think_llm）    │
│                                               │
│  Market → Social → News → Fundamentals       │
│  每位：LLM 分析 → tool_calls → Tool Node     │
│  → 生成報告 → 清 messages → 下一位            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  II. Research Team（多輪辯論）               │
│                                               │
│  Bull Researcher ⟷ Bear Researcher           │
│     循環 max_debate_rounds 次                │
│     （Deep=5 時共 10 次對話）                │
│                                               │
│  → Research Manager（deep_think_llm）         │
│    結構化輸出：recommendation + rationale     │
│    + strategic_actions                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  III. Trader（quick_think_llm）               │
│  結構化輸出：action + entry_price             │
│  + stop_loss + position_sizing               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  IV. Risk Management（多輪辯論）             │
│                                               │
│  Aggressive ⟷ Conservative ⟷ Neutral         │
│     循環 max_risk_discuss_rounds 次           │
│     （Deep=5 時共 15 次對話）                │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  V. Portfolio Manager（deep_think_llm）       │
│  最終結構化決策：                             │
│  rating: Buy/Overweight/Hold/Underweight/Sell │
│  + executive_summary + investment_thesis      │
│  + price_target + time_horizon               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
                  END
```

---

## 深度對照表

| 設定 | Shallow | Medium | **Deep** |
|------|---------|--------|----------|
| `max_debate_rounds` | 1 | 3 | **5** |
| `max_risk_discuss_rounds` | 1 | 3 | **5** |
| 分析師 | 1-4 | 4 | **4** |
| Bull/Bear 對話次數 | 2 | 6 | **10** |
| 風控對話次數 | 3 | 9 | **15** |
| 總 LLM 調用估計 | ~10 | ~25 | **~40+** |
| 預計耗時 | 2-5 min | 5-15 min | **15-30 min** |

---

## API Key 配置

`.env` 檔案路徑：`/Users/chunsingyu/softwares/TradingAgents/.env`

```bash
# 目前已設定
DEEPSEEK_API_KEY=sk-0213...        # DeepSeek 官方 API（api.deepseek.com）

# 可補設
OPENAI_API_KEY=                   # GPT-5.5 系列
ANTHROPIC_API_KEY=                # Claude Opus 4.7 系列
GOOGLE_API_KEY=                   # Gemini 3.x 系列
XAI_API_KEY=                      # Grok 4.20 系列
DASHSCOPE_API_KEY=                # Qwen 系列（阿里雲 DashScope）
ZHIPU_API_KEY=                    # GLM 系列（智譜）
MINIMAX_GROUP_ID=                 # MiniMax 系列
MINIMAX_API_KEY=                  # MiniMax 系列
OPENROUTER_API_KEY=               # OpenRouter（聚合多模型）
```

### DeepSeek 官方 API

目前使用 DeepSeek 官方 API 端點：
- `backend_url = "https://api.deepseek.com"`（預設，無需手動設定）
- 支援 `deepseek-v4-pro`, `deepseek-v4-flash`, `deepseek-chat` (V3.2), `deepseek-reasoner` (V3.2 thinking)
- v0.2.5 已修正 DeepSeek V4 的結構化輸出問題

> **歷史備註**：先前曾使用 PackyAPI 代理（`packyapi.com/v1`），已切回官方 API。本地仍有未提交的 PackyAPI 相關修改（stash 中的代碼）。

---

## 支援的 Provider & 模型

### DeepSeek（官方 API）

| 用途 | 模型 | 說明 |
|------|------|------|
| Quick | `deepseek-v4-pro` | V4 Pro，最強 |
| Quick | `deepseek-v4-flash` | V4 快速版 |
| Deep | `deepseek-v4-pro` | 關鍵決策用（Research Manager, Portfolio Manager） |
| Deep | `deepseek-reasoner` | V3.2 thinking 模型 |

### OpenAI

| 用途 | 模型 | 說明 |
|------|------|------|
| Quick | `gpt-5.4-mini` | 快速版 |
| Quick | `gpt-5.5` | 最新旗艦 |
| Deep | `gpt-5.5` | 最新旗艦，1M context |
| Deep | `gpt-5.5-pro` | 最強（$30/$180 per 1M tokens） |

### Anthropic

| 用途 | 模型 | 說明 |
|------|------|------|
| Quick | `claude-sonnet-4-6` | 速度與智能平衡 |
| Deep | `claude-opus-4-7` | 最新旗艦，長任務 agent |

### Google

| 用途 | 模型 | 說明 |
|------|------|------|
| Quick | `gemini-3-flash-preview` | 新一代快速 |
| Deep | `gemini-3.1-pro-preview` | 推理優先 |

### xAI

| 用途 | 模型 | 說明 |
|------|------|------|
| Quick | `grok-4.20-non-reasoning` | 最新，速度優化 |
| Deep | `grok-4.20-reasoning` | 最新旗艦推理 |

### MiniMax（v0.2.5 新增）

| 用途 | 模型 | 說明 |
|------|------|------|
| Quick | `MiniMax-M2.7-highspeed` | ~100 TPS，204K ctx |
| Deep | `MiniMax-M2.7` | 旗艦，coding/agent SOTA |

---

## 輸出結構

### Portfolio Manager 最終決策（結構化）

```json
{
  "rating": "Buy|Overweight|Hold|Underweight|Sell",
  "executive_summary": "入場策略、倉位、風控、時間範圍",
  "investment_thesis": "基於辯論的詳細推理",
  "price_target": 180.0,
  "time_horizon": "3-6 months"
}
```

### 結構化輸出的 3 個節點

| 節點 | Schema | 欄位 |
|------|--------|------|
| Research Manager | `ResearchPlan` | recommendation, rationale, strategic_actions |
| Trader | `TraderProposal` | action, reasoning, entry_price, stop_loss, position_sizing |
| Portfolio Manager | `PortfolioDecision` | rating, executive_summary, investment_thesis, price_target, time_horizon |

---

## 結果儲存位置

```
~/.tradingagents/
├── logs/
│   └── {TICKER}/
│       └── TradingAgentsStrategy_logs/
│           └── full_states_log_{date}.json
├── cache/
│   └── checkpoints/          # checkpoint 恢復用
└── memory/
    └── trading_memory.md     # 歷史決策 & 反思
```

---

## 進階功能

### 記憶系統

- 每次分析自動記錄決策到 `~/.tradingagents/memory/trading_memory.md`
- 下次分析同股票時，自動注入歷史教訓到 Portfolio Manager
- 自動計算 realized return（raw & alpha vs SPY）

### Checkpoint 恢復

```bash
# 啟用 checkpoint（crash 可恢復）
tradingagents analyze --checkpoint

# 清除所有 checkpoint
tradingagents analyze --clear-checkpoints
```

```python
config["checkpoint_enabled"] = True
```

---

## 原始碼位置

```
/Users/chunsingyu/softwares/TradingAgents/
├── tradingagents/
│   ├── graph/
│   │   ├── trading_graph.py      # 主入口：TradingAgentsGraph
│   │   ├── setup.py              # LangGraph workflow 定義
│   │   ├── analyst_execution.py  # 分析師執行規劃 & 計時（v0.2.5 新增）
│   │   ├── conditional_logic.py  # 辯論終止條件
│   │   └── propagation.py        # 初始狀態
│   ├── agents/
│   │   ├── analysts/             # 分析師（含 sentiment_analyst v0.2.5）
│   │   ├── researchers/          # Bull & Bear
│   │   ├── managers/             # Research Manager, Portfolio Manager
│   │   ├── trader/               # Trader
│   │   ├── risk_mgmt/            # Aggressive, Conservative, Neutral
│   │   ├── schemas.py            # Pydantic 結構化輸出 schema
│   │   └── utils/                # 工具函數、狀態定義
│   ├── dataflows/                # yfinance / Alpha Vantage / Reddit / StockTwits
│   ├── llm_clients/              # 多 Provider LLM 客戶端
│   │   ├── capabilities.py       # 模型能力偵測（v0.2.5 新增）
│   │   ├── api_key_env.py        # API key 環境變數管理（v0.2.5 新增）
│   │   └── model_catalog.py      # 模型目錄
│   └── default_config.py         # 預設配置（含 TRADINGAGENTS_* 環境變數覆蓋）
├── cli/                          # CLI 互動式介面
└── main.py                       # 範例入口
```

---

## v0.2.5 新功能（2026-05-20 更新）

- **Crypto 分析模式**：支援 BTC、ETH 等加密貨幣的分析（analysis-only mode）
- **Sentiment Analyst**：整合 Reddit + StockTwits 社群情緒數據
- **MiniMax Provider**：新增 MiniMax 模型支援（M2.7 旗艦，204K ctx）
- **模型目錄更新**：GPT-5.5、Claude Opus 4.7、Grok 4.20、Qwen 3.6、GLM-5-Turbo
- **DeepSeek V4 structured output 修正**：解決 v0.2.4 的結構化輸出問題
- **環境變數覆蓋 config**：`TRADINGAGENTS_*` 系列環境變數可直接覆蓋 `DEFAULT_CONFIG`
- **CLI 自動偵測 API key**：缺 key 時會提示並可自動存到 `.env`
- **Alpha benchmark 可配置**：非 US 股票可自訂 benchmark（如港股用恆指 `^HSI`）
- **Ollama 自訂端點**：`OLLAMA_BASE_URL` 環境變數支援遠端 Ollama
- **新聞參數可配置**：`news_article_limit`、`global_news_lookback_days` 等

---

## 測試結果（2026-05-18，v0.2.4 + PackyAPI）

### 測試設定

| 項目 | 值 |
|------|-----|
| **Ticker** | NVDA |
| **分析日期** | 2026-05-16 |
| **Provider** | PackyAPI DeepSeek |
| **Quick Model** | `deepseek-v4-flash` |
| **Deep Model** | `deepseek-v4-pro` |
| **深度** | Deep（debate=5, risk=5） |
| **耗時** | **21.3 分鐘**（1278 秒） |

### 各階段決策

| 階段 | 決策 | 重點 |
|------|------|------|
| **Market Analyst** | 📈 **BUY** | 三重均線多頭排列，MACD 金叉，RSI 64.7 甜蜜點，VWMA 量價配合。目標 $240-245，停損 $209 |
| **Social Analyst** | ➡️ HOLD | yfinance 新聞 API 無近期 NVDA 新聞（數據源限制） |
| **News Analyst** | ➡️ HOLD | 同上，新聞數據不足 |
| **Fundamentals Analyst** | 📈 **BUY** | PEG 0.72，Forward PE 19.5x，營收高增長，毛利率 >70%，淨利率 >55%，ROE >100% |
| **Research Manager** | ⚖️ **Underweight** | 辯論後轉向謹慎：估值依賴 134% 盈利增長預期，庫存增長 +112% 遠超營收增長 +66%，毛利率從 75% 降至 71% |
| **Trader** | 🔴 **SELL** | 減持 30-50%，市價賣一半、限價 $230-235 賣一半，現金等待回購 |
| **Portfolio Manager** | 🔴 **Underweight → SELL** | 最終建議減持，等待 200 SMA ($186) 或 50 SMA ($193) 回購 |

### 最終決策

> **Underweight / SELL** — 減持 NVDA 30-50%
> - 原因：估值脆弱（依賴 134% 盈利增速）、技術面動能衰退、基本面瑕疵（庫存暴增、毛利下滑）
> - 回購條件：價格回到 200 SMA ($186) 或 50 SMA ($193) 附近

### 發現的問題

1. **`deepseek-v4-pro` 不支援結構化輸出**：PackyAPI 將 `deepseek-v4-pro` 路由到 `deepseek-reasoner`，而 reasoner 不支援 `tool_choice`（structured output），導致 Research Manager、Trader、Portfolio Manager 都需 fallback 到純文字
2. **yfinance 新聞 API 無近期數據**：Social / News 分析師取不到近期新聞，影響分析品質
3. **debug 模式輸出重複**：Trader 的 SELL 建議被重複輸出多次（LangGraph streaming 的 side effect）

### 建議修正

- ✅ **已修正（v0.2.5）**：DeepSeek V4 結構化輸出問題已在官方版修復，官方 API 不需要 `deepseek_effort_level`
- **新聞數據**：v0.2.5 新增 `news_article_limit` 配置，也可改用 Alpha Vantage（需 API key）
- **社群情緒**：v0.2.5 新增 Sentiment Analyst，整合 Reddit + StockTwits，改善原本 Social Analyst 數據不足的問題
- **正式整合時不使用 debug 模式**，改用 `ta.graph.invoke()` 搭配 callback handler

---

## 環境變數快速配置（v0.2.5 新增）

```bash
# 透過環境變數直接覆蓋 DEFAULT_CONFIG，無需改代碼
export TRADINGAGENTS_LLM_PROVIDER=deepseek
export TRADINGAGENTS_DEEP_THINK_LLM=deepseek-v4-pro
export TRADINGAGENTS_QUICK_THINK_LLM=deepseek-v4-pro
export TRADINGAGENTS_OUTPUT_LANGUAGE=Chinese
export TRADINGAGENTS_MAX_DEBATE_ROUNDS=5
export TRADINGAGENTS_MAX_RISK_ROUNDS=5
export TRADINGAGENTS_CHECKPOINT_ENABLED=true
export TRADINGAGENTS_BENCHMARK_TICKER=SPY        # 非美股指定 alpha benchmark
```

---

## 參考

- GitHub: [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)
- 論文: [arXiv:2412.20138](https://arxiv.org/abs/2412.20138)
- 整合架構: [[wiki/architecture/auto-trading-pipeline-High-level|auto-trading-pipeline]]
- Webull 整合: [[wiki/research/webull-openapi-skill]]
