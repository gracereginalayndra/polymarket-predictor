from pathlib import Path


def forecast(client, context, cfg):
    prompt = (Path(cfg['llm']['prompt_dir'])/'news_agent.md').read_text()
    return client.predict(prompt, context, role='news_agent')
