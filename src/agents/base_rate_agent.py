from pathlib import Path


def forecast(client, context, cfg):
    prompt = (Path(cfg['llm']['prompt_dir'])/'base_rate_agent.md').read_text()
    return client.predict(prompt, {**context, 'documents': []}, role='base_rate_agent')
