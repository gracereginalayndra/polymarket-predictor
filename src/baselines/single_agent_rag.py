from pathlib import Path


def forecast(client, context, cfg, replicate=0):
    prompt = (Path(cfg['llm']['prompt_dir'])/'single_agent_rag.md').read_text()
    return client.predict(prompt, context, role='single_agent_rag', replicate=replicate)
