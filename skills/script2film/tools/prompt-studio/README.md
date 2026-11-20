# Prompt Studio

A single HTML file that turns one idea into storyboard or single-shot prompts you can paste into VideoExpress. [繁體中文](./README.zh-TW.md)

The full introduction, screenshots and an online copy are on the Prompt Studio page of the project website ([`docs/studio.html`](../../docs/studio.html)). This README only covers how to open it and how to work on it.

## Open it

- Open [`prompt-studio.html`](prompt-studio.html) in any browser. Nothing to install, no account.
- To expand prompts with a local Ollama model, start it with the launcher instead: double-click `PromptStudio.command` (macOS) or `PromptStudio.bat` (Windows). It serves this folder on `http://localhost:8765`, because Ollama does not accept requests from a page opened as a file.

## Working on it

Run these in this folder:

```bash
node snapshot-test.js        # snapshot test of the generated prompts; no network, no key
node eval.js --list          # list the LLM eval cases; sends nothing
node eval.js --run           # calls a language model: needs GEMINI_API_KEY (or GROQ_API_KEY / NVIDIA_API_KEY / OPENROUTER_API_KEY)
node check-links.mjs README.md README.zh-TW.md   # local links in these READMEs point to files that exist
```

The website serves a copy of the tool at `docs/studio/app.html`. After changing `prompt-studio.html`, run from the repository root:

```bash
python3 tools/site/sync_studio.py
```

`tools/site/tests/test_site_studio_copy.py` fails when the copy is out of date.

## License

[MIT](../../LICENSE). The screenwriting rules are condensed from the MIT-licensed [AI-drama-pound](https://github.com/POUND0423/AI-drama-pound); see [`NOTICE.md`](../../NOTICE.md).
