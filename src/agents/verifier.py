from pathlib import Path


def forecast(client, context, drafts, cfg):
    prompt = (Path(cfg['llm']['prompt_dir'])/'verifier.md').read_text()
    # Keep original drafts auditable; the verifier result never overwrites them.
    return client.predict(prompt, {**context, 'drafts': drafts}, role='verifier')
