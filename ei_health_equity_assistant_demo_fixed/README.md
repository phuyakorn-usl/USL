# EI Health Equity Assistant — Demo

A minimal Streamlit chatbot + assistant to help EI Fellows integrate a Health Equity framework (SDHE, BROM) for Southeast Asia, and to capture/communicate impact.

## Features
- **Chat**: Q&A over seed knowledge (SDHE, BROM, SEA context). Optional LLM if you set an API key.
- **Generators**: Impact statement & one-pager scaffolds with SDHE/BROM indicators.
- **Seed data**: `data/ei_pack.json` and `data/indicators.csv` — replace/expand for your project.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app.py
```

## Optional: Use an LLM
Set your provider key as an environment variable before running:
```bash
export OPENAI_API_KEY=sk-...   # macOS/Linux
setx OPENAI_API_KEY "sk-..."   # Windows (new shell)
```

The app will fall back to a simple rule-based answer when no key is available.

## Customize
- Edit `data/ei_pack.json` to add countries, domains, FAQs, and templates.
- Drop your indicators in `data/indicators.csv`.
- Modify the prompt in `app.py` under `build_system_prompt()`.

## Notes
This is a demo. Validate content with local stakeholders and IRB/ethics requirements before field use.
