# Primary sources and related work

Checked during project construction on 27 October 2026. API contracts can change; a dated source reference
is not proof of future endpoint access. Code fixtures test documented shapes; the real pilot separately
records what was actually reachable in the build environment.

| Source | Relevance to this project | Limits of the claim |
|---|---|---|
| Halawi et al., [Approaching Human-Level Forecasting with Language Models](https://arxiv.org/abs/2402.18563), 2024 | Prior retrieval/reasoning/aggregation forecasting pipeline | Do not claim RAG forecasting or forecast aggregation is new |
| Karger et al., [ForecastBench](https://arxiv.org/abs/2409.19839), 2024/2025 | Dynamic future-event evaluation addresses contamination | Its benchmark results are not results for this project |
| Ye et al., [Hindcast: Replaying Prediction Markets to Evaluate LLM Forecasters](https://arxiv.org/abs/2607.14051), 2026 | Closely related historical Polymarket replay with archived social evidence | Read its full methodology before claiming methodological novelty; timestamp filtering alone does not prove clean model weights |
| [Polymarket Data API v2 overview](https://docs.polymarket.com/api-reference/data-api/overview) | Versioned data host and history availability | Real coverage must be measured by market/window |
| [Token price history](https://docs.polymarket.com/api-reference/markets/get-a-tokens-price-history) | Cursor/window contract, grain metadata and settlement rows | Historical data is not automatically admitted to strict replay |
| [Prices and order books](https://docs.polymarket.com/market-data/prices-order-books) | Token identifiers and quote semantics | Current order books do not reconstruct old order books |
| [Resolution state](https://docs.polymarket.com/api-reference/markets/get-resolution-state) | Final status/payout lookup | Disputes, fractional settlement and unavailable fields need review |
| [Predictions changelog](https://docs.polymarket.com/changelog/predictions) | Migration of price history and new API details | Adapter support is explicit, not universal |
| [GDELT DOC API example](https://blog.gdeltproject.org/doc-2-0-api-llms-summarizing-headlines-turkish-investment-inflation-the-niger-coup/) | News headline discovery | Headline results are not full article text or guaranteed archival access |
| [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html) | Calibration concepts and data separation | A logistic combiner is not automatically well calibrated |
| [SQLite appropriate uses](https://www.sqlite.org/whentouse.html) | Local single-writer architecture choice | Multi-machine write concurrency may need a server database |

These sources inform the framework. The original planning report supplies the project goal and D1–D4
deliverables, including the ten-week schedule. This repository's architecture, implementation choices,
failure guards and recovery plan are proposed work for this specific project.

## Literature work still needed for the dissertation

Expand this starting matrix into a proper review: precise datasets, time cutoffs, information sets, model
versions, aggregation methods, calibration methods, baselines, statistical uncertainty and limitations.
Read the full papers, record exactly what each permits as a comparison, and cite them in your department's
required style. A bibliography of titles alone does not complete Week 1's literature review academically.
