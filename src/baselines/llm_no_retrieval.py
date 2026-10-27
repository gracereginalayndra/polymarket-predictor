from pathlib import Path


def forecast(client, context, cfg):
    prompt = (Path(cfg['llm']['prompt_dir'])/'llm_no_retrieval.md').read_text()
    return client.predict(prompt, {**context, 'documents': []}, role='llm_no_retrieval')
