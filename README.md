# TradePass

**An AI assistant that helps small traders across Africa navigate cross-border documentation and AfCFTA tariff qualification.**

Built for GOMYCODE's *Come Build with AI* hackathon — 27 September 2026, Kenya.

---

## The problem

Small traders across Africa lose money and time at the border because trade rules are scattered across multiple authorities and hard to interpret. AfCFTA can eliminate tariffs on qualifying goods, but rules of origin, certificates, and documentation requirements are complex and vary by product and corridor. Getting it wrong means customs delays, paying the full non-preferential tariff, or a rejected shipment.

## What it does

A trader describes their export in plain language, for example:

> "I want to export 200kg of processed avocado oil from Kenya to Uganda"

TradePass returns:
- **Documents likely needed** — a practical checklist
- **AfCFTA origin qualification** — a reasoned assessment (likely yes / likely no / unclear)
- **Next step** — a concrete action, e.g. which authority to contact
- **Sources used** — the exact source snippets the answer relied on

If a question isn't covered by its sources, it says so honestly instead of guessing.

## Current scope

- **Corridor:** Kenya ↔ Uganda
- **Products:** avocado oil, tea, textiles
- This is a curated prototype, not a full retrieval pipeline — see [Limitations](#known-limitations) below.

## How it's built

| Layer | Choice |
|---|---|
| Language | Python |
| Interface | [Gradio](https://gradio.app/) |
| AI | LLM API (see [AI provider](#ai-provider) below) |
| Grounding | Manually curated snippets from AfCFTA Secretariat, Kenya Revenue Authority (KRA), Uganda Revenue Authority (UNBS), Kenya Bureau of Standards (KEBS), and tralac trade law resources |
| Deployment | [Render](https://render.com/) |

The model is instructed to answer **only** from the source snippets provided as context — it does not rely on its own general knowledge for tariff or document facts, and it explicitly states when a question isn't covered.

### AI provider

The product was originally built against Google's Gemini API. Due to a widely-reported, ongoing 503 (server overload) issue affecting Gemini's flash models, the app can fall back to [Groq](https://groq.com/) (hosted open models) as an alternative provider — one of the tools explicitly supported by the hackathon's "Build with Any AI" track. Check `app.py` for which provider is active.

## Reliability features

- **Honest fallback:** if the source snippets don't cover a question, the assistant says so rather than fabricating an answer.
- **Conversation memory:** follow-up questions (e.g. "what about tea instead?") retain context from earlier in the session.
- **Categorized error handling:** authentication, rate-limit, network, and safety-related failures are caught and shown as clear, user-friendly messages, with technical detail logged server-side for debugging.
- **Retry logic:** transient server-side (503) errors are automatically retried before falling back to an error message.

## Running locally

```bash
git clone https://github.com/susan-awori/tradeguide.git
cd tradeguide
pip install -r requirements.txt
```

Set your API key as an environment variable (do not hardcode it):

```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-key-here"
# or, if using Groq
$env:GROQ_API_KEY="your-key-here"
```

Then run:

```bash
python app.py
```

Open the local URL it prints (typically `http://127.0.0.1:7860`).

## Live demo

- **App:** https://tradeguide.onrender.com/
- **Note:** Render's free tier spins down after inactivity — the first request after idle time may take 30–60 seconds to respond.

## Example queries to try

```
I want to export 200kg of processed avocado oil from Kenya to Uganda
```
```
What documents do I need to export tea from Kenya?
```
```
What documents do I need?
```
(the last one is deliberately vague — it should trigger an honest "I don't have enough information" response)

## Known limitations

- The source corpus is a small, manually curated set — not a live-updating retrieval pipeline. It covers one corridor and three products.
- This is general guidance, **not legal or customs advice**. Rules can change, and requirements may be applied inconsistently at different border posts — always confirm with the relevant customs or trade authority before shipping.
- No integration with live customs, tariff, or payment systems.

## What's next

- Expand to more corridors and products across the eight participating hackathon countries (Tunisia, Algeria, Morocco, Senegal, Côte d'Ivoire, Nigeria, Kenya, Saudi Arabia)
- Replace the curated snippet set with a real document-retrieval pipeline over official sources
- Add voice input for accessibility

## AI/tool disclosure

- **AI inside the product:** an LLM (Gemini or Groq-hosted Llama, see [AI provider](#ai-provider)) interprets the trader's plain-language question and generates an answer grounded only in the provided source snippets.
- **AI used to help build this project:** coding assistance was used for boilerplate, debugging, and deployment configuration. All logic was reviewed, tested, and corrected by the team before use.
- **Data sources:** all source snippets are drawn from public information published by AfCFTA, national revenue and standards authorities, and trade law resources — no private or personal data is used or stored.
- **NVIDIA Brev:** not used.

## License / disclaimer

This is a hackathon prototype and is not legal, customs, or financial advice. Use at your own discretion and always confirm requirements with the relevant authority before shipping goods.
