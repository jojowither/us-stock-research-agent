# Roadmap

美股研究 Agent：用 SEC 財報、股價和新聞回答美股研究問題的 LLM agent。

- 部署：GHCR + Render
- 主力 LLM：Gemini（AI Studio 免費層）；Claude 為選配比較組

---

## 技能清單

| 工具 | 角色 | 重點 |
|---|---|---|
| Pydantic AI | Agent 框架 | deps 注入、結構化輸出、多 agent、`TestModel` 測試 |
| MCP | 資料查詢 server | tools / resources / prompts、stdio 與 Streamable HTTP、tool 設計 |
| Langfuse | 觀測與 prompt 管理 | OTel tracing、prompt 版本、datasets、experiments |
| LLM Evaluation | 品質把關 | golden dataset、分層 eval、judge 校準、CI gate |
| Docker | 本機與部署環境 | multi-stage、compose 多服務、self-host Langfuse |
| GitHub Actions | CI/CD | PR 檢查、service container、eval gate、部署 |
| Gemini | 主力 LLM 與 embedding | AI Studio 免費層 |
| Postgres + pgvector | 唯一資料庫 | hybrid search（向量 + 全文） |
| Airflow | 本機 ingestion | 排程與重跑 |
| FastAPI、Pytest、uv、ruff | API 與工程基礎 | |
| SEC EDGAR、Tiingo、Finnhub | 資料來源 | 財報、股價、新聞 |
| GHCR、Render、Neon、Streamlit Cloud | 部署（免費） | |

---

## 切片（草案）

每一片都是從頭到尾打通、可以 demo 的 tracer bullet。內容會在每片開始時用 `/grill-with-docs` 和 `/to-tickets` 定案。

| 切片 | 內容 | 主要技能 | 狀態 |
|---|---|---|---|
| 1 | 寫死一筆財報數字 → MCP tool → Pydantic AI agent → CLI 回答；pytest 與 CI | MCP、Pydantic AI、Pytest、GitHub Actions | ⬜ |
| 2 | 換成真實 SEC 財報資料，存進 Docker 裡的 Postgres | Docker、Postgres、SEC EDGAR | ⬜ |
| 3 | 每次對話都有 trace；prompt 版本管理 | Langfuse | ⬜ |
| 4 | 第一批 eval 題目，在 CI 中把關 | LLM Evaluation、GitHub Actions | ⬜ |
| 5 | 10-K 文字的 RAG（hybrid search） | pgvector、Gemini embedding | ⬜ |
| 6 | 股價資料與排程 ingestion | Tiingo、Airflow | ⬜ |
| 7 | API、前端與部署 | FastAPI、GHCR、Render、Streamlit | ⬜ |
