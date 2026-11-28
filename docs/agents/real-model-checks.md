# Real-model checks

Tests never call a real LLM. Run `stock-agent` against a real model only for a slice's manual check, and spend requests as if each one costs money: on the AI Studio free tier it does in quota, with a service account it does in someone's bill.

## Credentials

- **Service account (preferred):** `STOCK_AGENT_MODEL=google-cloud:<model>` and `GOOGLE_APPLICATION_CREDENTIALS=<path>`. The key file lives outside the repository; never read or print its contents.
- **API key:** `GOOGLE_API_KEY` in `.env` with a `google:<model>`. The free tier allows 5 requests per minute and 20 per day per model, and failed requests appear to count.

One question costs 2 to 4 model requests: a tool call, the answer, and a retry for each unavailable lookup or rejected answer.

## Running

- Ask each question once, at least 20 seconds apart. A 503 or 429 is a result to report, not a reason to loop: stop and tell the developer.
- Set `PYDANTIC_AI_NO_BANNER=1` to keep the output readable.

## Standard questions

| Question | Expected |
|---|---|
| What was Apple's latest revenue? | FY2026, period ended 2026-09-26, 478,834,000,000 USD, 10-K filed 2026-11-03 |
| 微軟去年的淨利是多少？ | Answer in Chinese: FY2026, period ended 2026-06-30, 133,749,000,000 USD |
| What was Tesla's revenue in 2025? | Says it is unavailable, lists AAPL and MSFT fiscal years, no Sources |
| 特斯拉去年營收多少？ | Same, in Chinese |

Add a row when a slice adds data or behaviour worth checking with a real model.
