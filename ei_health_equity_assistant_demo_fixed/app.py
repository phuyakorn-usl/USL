
import os, json, random, time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="EI Health Equity Assistant (Demo)", page_icon="🌏")

# -----------------------------
# Load seed knowledge
# -----------------------------
@st.cache_data
def load_pack():
    with open("data/ei_pack.json", "r", encoding="utf-8") as f:
        return json.load(f)
pack = load_pack()

INDICATORS = pd.read_csv("data/indicators.csv")

# -----------------------------
# Optional: LLM shim (vendor-agnostic)
# -----------------------------
def llm_available():
    return bool(os.getenv("OPENAI_API_KEY"))

def llm_reply(system_prompt: str, user_prompt: str) -> str:
    """
    Minimal placeholder for an LLM call.
    To wire up: use openai, anthropic, etc. Here we simulate latency + a pseudo reply.
    """
    # If no key set, fall back to rule-based below
    if not llm_available():
        return None

    # Placeholder deterministic "LLM-like" summary (replace with real API call).
    # This keeps the demo vendor-agnostic and runnable without keys.
    reply = f"""(LLM draft)\nBased on the SDHE/BROM context for Southeast Asia:\n- {user_prompt}\n- Remember: SDHE domains include {", ".join([d["domain"] for d in pack["sdhe_domains"][:3]])}, etc.\n- Use BROM for beneficiary-reported outcomes and short-form indices.\n"""
    return reply

# -----------------------------
# Simple rule-based Q&A
# -----------------------------
def keyword_answer(q: str) -> str:

# -----------------------------
# Intent helpers for common EI queries
# -----------------------------
def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def detect_intent(q: str) -> str:
    qn = normalize(q)
    if ("indicator" in qn or "kpi" in qn) and ("climate justice" in qn or "climate" in qn):
        return "indicators_climate_justice"
    if ("communicate" in qn or "showcase" in qn or "present" in qn) and ("outcome" in qn or "impact" in qn):
        return "comms_showcase"
    if ("beneficiaries" in qn or "women" in qn) and ("low-income" in qn or "poor" in qn) and ("tool" in qn or "measure" in qn or "impact" in qn):
        return "tools_women_low_income"
    return "general"

def answer_by_intent(intent: str) -> str:
    if intent == "indicators_climate_justice":
        items = pack.get("project_indicator_presets", {}).get("climate justice", [])
        if not items:
            return keyword_answer("indicators")
        lines = [f"- {it['name']} — {it['metric']} ({it['domain']})" for it in items]
        return "Recommended indicators for a *climate justice* project:\n" + "\n".join(lines) + "\nPair at least one SDHE exposure metric with one BROM outcome."
    if intent == "comms_showcase":
        pb = pack.get("comms_playbook", {}).get("outcome_showcase", {})
        arts = "\n".join([f"- {a}" for a in pb.get("artifacts", [])])
        cad = "\n".join([f"- {c}" for c in pb.get("cadence", [])])
        tips = "\n".join([f"- {t}" for t in pb.get("tips", [])])
        return f"**How to communicate & showcase outcomes**\n\nArtifacts:\n{arts}\n\nCadence:\n{cad}\n\nTips:\n{tips}"
    if intent == "tools_women_low_income":
        rec = pack.get("impact_tools_by_group", {}).get("women low-income", {})
        p = "\n".join([f"- {x}" for x in rec.get("primary", [])])
        s = "\n".join([f"- {x}" for x in rec.get("supplementary", [])])
        n = "\n".join([f"- {x}" for x in rec.get("notes", [])])
        return f"**Impact tools for women from low-income groups**\n\nPrimary:\n{p}\n\nSupplementary:\n{s}\n\nNotes:\n{n}"
    return None

    ql = q.lower()
    # FAQs
    for k,v in pack["faq"].items():
        if k in ql:
            return v

    # SDHE domains mention
    if "sdhe" in ql or "determinant" in ql:
        doms = "\n".join([f"- {d['domain']}: {', '.join(d['examples'][:2])}" for d in pack["sdhe_domains"]])
        return f"Key SDHE domains we use:\n{doms}\nPick 2–3 domains most relevant to the target group and align indicators."

    if "brom" in ql or "beneficiary-reported" in ql:
        return "BROM are short, recurring beneficiary-reported outcome measures (e.g., stress, safety, access). Keep it <2 mins, repeat quarterly, and triangulate with program data."

    if "indicator" in ql or "kpi" in ql:
        sample = INDICATORS.sample(3, random_state=0)
        rows = "\n".join([f"- {r.name}: {r.metric} ({r.domain})" for r in sample.itertuples(index=False)])
        return f"Sample indicators:\n{rows}\nUse both outcome (BROM) and exposure/structural indicators (SDHE)."

    if "privacy" in ql or "pdpa" in ql or "irb" in ql or "ethics" in ql:
        return pack["faq"]["privacy"]

    # Country mentions
    for country, notes in pack["country_notes"].items():
        if country.lower() in ql:
            return f"{country} notes:\n- " + "\n- ".join(notes)

    # fallback
    return "I can help with SDHE domains, BROM design, indicators, and impact comms. Try: 'suggest indicators for low-income families in Bangkok' or 'draft impact statement for housing upgrades'."

# -----------------------------
# Prompting
# -----------------------------
def build_system_prompt(meta: dict) -> str:
    return f"""You are a Health Equity assistant for Southeast Asia.
- Use SDHE domains and BROM.
- Tailor to location={meta.get('location')} and group={meta.get('group')}.
- Answer concisely, suggest 3–5 indicators, and one short BROM question.
- Emphasize equity rationales and feasible next steps.
"""

def answer_question(question: str, meta: dict) -> str:
    system_prompt = build_system_prompt(meta)
    # Try intent shortcuts first
    intent = detect_intent(question)
    intent_reply = answer_by_intent(intent)
    if intent_reply:
        return intent_reply

    # Then try LLM if available
    draft = llm_reply(system_prompt, question)
    if draft:
        return draft.strip()
    # fallback
    return keyword_answer(question)

# -----------------------------
# Text generators
# -----------------------------
def gen_impact_statement(meta: dict) -> str:
    tpl = pack["templates"]["impact_statement"]
    domains = ", ".join(meta.get("domains", []))
    return tpl.format(
        project_title = meta.get("title", "Untitled Project"),
        location = meta.get("location", "Southeast Asia"),
        group = meta.get("group", "Vulnerable population"),
        domains = domains or "SDHE-aligned (housing, environment, access to care)",
        problem = meta.get("problem", "Describe the inequity and the structural drivers (SDHE)."),
        actions = meta.get("actions", "List practical interventions, e.g., housing safety upgrades; AQHI risk communication; primary care outreach."),
        outcomes = meta.get("outcomes", "BROM: stress ↓, perceived safety ↑; Indicators: AQHI exposure days ↓, commute time ↓, % HH within 1km of primary care ↑."),
        equity_rationale = meta.get("equity_rationale", "Why these actions reduce unfair, avoidable gaps for the group in this place."),
        next_steps = meta.get("next_steps", "Pilot in 2 sites; collect baseline BROM; publish a 1-pager; plan for scale with local govt.")
    )

def gen_one_pager(meta: dict) -> str:
    tpl = pack["templates"]["one_pager"]
    indicators_text = "\n".join([f"- {r.name} — {r.metric} ({r.domain})" for _, r in INDICATORS.sample(4, random_state=1).iterrows()])
    return tpl.format(
        project_title = meta.get("title", "Health Equity Pilot"),
        location = meta.get("location", "Bangkok / Metro SEA"),
        group = meta.get("group", "Low-income families / at-risk households"),
        goal = meta.get("goal", "Reduce inequities in exposure (AQHI/heat), access (primary care), and safety (housing)."),
        equity_case = meta.get("equity_case", "Target structural drivers using SDHE; measure perceived change via BROM; co-design with local partners."),
        workstream_1 = meta.get("ws1", "Community data & baseline (SDHE + BROM)"),
        workstream_2 = meta.get("ws2", "Targeted interventions (e.g., housing UD modules, risk comms)"),
        workstream_3 = meta.get("ws3", "Policy & scaling with municipal partners"),
        indicators = meta.get("indicators", indicators_text),
        comms_plan = meta.get("comms", "Quarterly briefs, dashboard snapshots, and beneficiary stories with safeguards.")
    )

# -----------------------------
# UI
# -----------------------------
st.title("🌏 EI Health Equity Assistant (Demo)")
st.caption(pack["about"]["disclaimer"])

with st.sidebar:
    st.header("Project context")
    location = st.selectbox("Location", ["Bangkok (TH)", "Chiang Mai (TH)", "Valenzuela (PH)", "Manila (PH)", "Yangon/Mandalay (MM)", "Jakarta (ID)", "HCMC (VN)", "Other"], index=0)
    group = st.selectbox("Focus group", pack["vulnerable_groups"] + ["Other"], index=0)
    chosen_domains = st.multiselect("Key SDHE domains", [d["domain"] for d in pack["sdhe_domains"]], default=["Housing & Built Environment","Environment & Air Quality","Access to Health & Care"])
    st.divider()
    st.subheader("Seed knowledge")
    if st.button("Show indicators table"):
        st.dataframe(INDICATORS, use_container_width=True)

tab1, tab2, tab3 = st.tabs(["💬 Chat", "🛠️ Generators", "📒 Playbooks"])

# Chat tab
with tab1:
    if "chat" not in st.session_state:
        st.session_state.chat = []

    for role, content in st.session_state.chat:
        with st.chat_message(role):
            st.write(content)

    q = st.chat_input("Ask about SDHE, BROM, indicators, equity…")
    if q:
        meta = {"location": location, "group": group, "domains": chosen_domains}
        st.session_state.chat.append(("user", q))
        with st.chat_message("user"):
            st.write(q)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                time.sleep(0.4)
                a = answer_question(q, meta)
                st.write(a)
        st.session_state.chat.append(("assistant", a))

# Generators tab
with tab2:
    st.subheader("Impact statement")
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Project title", "Safe & Stable Homes x Clean Air")
        prob = st.text_area("Problem", "High AQHI exposure and unsafe housing compound stress and ill health for low-income families.")
        acts = st.text_area("Action", "Install UD modules (rails/ramps), risk comms on AQHI days, and primary care outreach.")
    with c2:
        outs = st.text_area("Early outcomes (BROM/metrics)", "BROM stress ↓2 points; AQHI exposure days ↓10%; % HH within 1km of primary care +15pp.")
        eqr = st.text_area("Equity rationale", "Targets unfair, avoidable exposure/access gaps for at-risk households.")
        nxt = st.text_area("Next steps", "Pilot in 2 districts; quarterly BROM; 1-pager to city partners.")

    if st.button("Generate impact statement"):
        meta = {"title": title, "location": location, "group": group, "domains": chosen_domains,
                "problem": prob, "actions": acts, "outcomes": outs, "equity_rationale": eqr, "next_steps": nxt}
        st.code(gen_impact_statement(meta), language="markdown")

    st.divider()
    st.subheader("One‑pager scaffold")
    goal = st.text_input("Goal", "Reduce inequities in exposure, access, and safety")
    eq_case = st.text_area("Why it matters", "Use SDHE to target structural drivers; use BROM for perceived change; respect PDPA/IRB.")
    ws1 = st.text_input("Workstream 1", "Community data & baseline (SDHE + BROM)")
    ws2 = st.text_input("Workstream 2", "Targeted interventions (UD modules, AQHI comms)")
    ws3 = st.text_input("Workstream 3", "Policy & scaling with municipal partners")
    comms = st.text_area("Comms plan", "Quarterly briefs, dashboard snapshots, beneficiary stories (with safeguards).")

    if st.button("Generate one‑pager"):
        meta = {"title": title, "location": location, "group": group, "goal": goal, "equity_case": eq_case,
                "ws1": ws1, "ws2": ws2, "ws3": ws3, "indicators": None, "comms": comms}
        st.code(gen_one_pager(meta), language="markdown")


# Playbooks tab
with tab3:
    st.subheader("Quick answers")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Indicators: Climate Justice"):
            st.info(answer_by_intent("indicators_climate_justice"))
    with c2:
        if st.button("How to showcase outcomes"):
            st.info(answer_by_intent("comms_showcase"))
    with c3:
        if st.button("Tools: Women (low-income)"):
            st.info(answer_by_intent("tools_women_low_income"))


st.markdown("---")
st.caption("Tip: set OPENAI_API_KEY to enable LLM drafting; otherwise the app uses a concise rule-based helper.")
