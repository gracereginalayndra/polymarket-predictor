# Verification artifacts

Every file named synthetic_* is an artificial software demonstration, not an empirical FYP result.
The saved synthetic_models.joblib is supplied only to inspect the fitted demonstration; regenerate it with run_demo.
Do not use it as a trained real-world forecaster. Only load joblib files from trusted sources.

The live pilot contains 8 market identities, 2 usable quote snapshots and 44 news records. It has no
resolved labels and no LLM forecasts. live_market_baseline_predictions.csv contains raw market and
constant-50% predictions only. live_pilot_status.json retains both successful and failed requests.

The archive also includes data/live_pilot so the small real collection is inspectable; it is Git-ignored.
Original raw_ref values retain their collection-machine path. After extraction, locate the identical
raw-response basename in data/live_pilot/raw. These path strings are provenance, not an instruction
to create the original workspace directory. Run IDs/config hashes likewise retain original run paths;
regenerate an experiment in your own checkout rather than mixing relocated model/config identities.
