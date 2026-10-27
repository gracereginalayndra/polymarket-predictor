# Design decision log

| Date | Decision | Reason / consequence |
|---|---|---|
| 2026-10-27 | Implement the requested package without placing trades | Matches the planning report's research scope |
| 2026-10-27 | Distinguish implementation completion from empirical completion | Missing credentials, clean history and mature labels cannot be fabricated |
| 2026-10-27 | Use SQLite, immutable JSON and CSV manifests | Fits a single-machine student project and supports auditing |
| 2026-10-27 | Keep observation and availability separate | Publication dates and present metadata are insufficient for historical replay |
| 2026-10-27 | Default historical API downloads to unverified provenance | Prevents silent look-ahead from a successful API response |
| 2026-10-27 | Implement Data API v2 and explicitly selectable legacy history separately | Current docs describe migration; silent endpoint switching would alter semantics |
| 2026-10-27 | Exclude settlement points and ambiguous binary mappings | Prevents labels masquerading as input prices |
| 2026-10-27 | Move discovery from newest ID to recent trading volume | First real pilot found empty books on newly created markets; research selection still needs freezing |
| 2026-10-27 | Use prospective RSS summaries as baseline news source | Real pilot succeeded; GDELT returned 503 and is not treated as guaranteed access |
| 2026-10-27 | Use stateless sparse retrieval before trying dense embeddings | Avoids extra cost and future-corpus vocabulary/IDF fitting; leaves semantic retrieval as a measurable extension |
| 2026-10-27 | Keep market prices out of independent agent contexts | Makes AI incremental information clearer and reduces anchoring |
| 2026-10-27 | Include repeated-call single-agent comparator | Extra LLM calls alone could explain an apparent multi-agent gain |
| 2026-10-27 | Primary aggregation is regularized logistic stacking | Simple, inspectable and easier to fit with limited labelled data |
| 2026-10-27 | Add Bayesian logistic correction as a sensitivity model | Meets the proposed Bayesian direction without mislabelling ordinary logistic regression |
| 2026-10-27 | Use event-balanced loss and group-purged time splits | Repeated horizons/contracts are not independent observations |
| 2026-10-27 | Require label maturity at fit boundaries | An earlier forecast date alone does not make its future outcome a valid training label |
| 2026-10-27 | Include a synthetic offline backend with strict labels | Enables reproducible end-to-end testing without paid APIs; cannot support scientific conclusions |
| 2026-10-27 | Leave actual categories and split dates for informed selection | Available market coverage and observation windows have not yet been established |
| 2026-10-27 | Version config, prompts and source code in run identity | Avoids mixing predictions produced by materially different experiments |

Append dated decisions when changing market scope, prompts, model, data access, timestamp rules or
statistical methods. Record changes before looking at affected test outcomes. Retain prior versions in Git.
