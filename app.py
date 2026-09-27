import os
import logging
import gradio as gr
from google import genai

# ---- 1. SET YOUR API KEY ----
API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_KEY_HERE")
client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.0-flash"

# ---- Logger (server-side technical detail capture) ----
logger = logging.getLogger("tradepass")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---- 2. SOURCE SNIPPETS (your "RAG corpus") ----
SOURCES = [
    {
        "id": "AfCFTA-ROO-1",
        "title": "AfCFTA Rules of Origin Guide (AfCFTA Secretariat)",
        "text": (
            "To qualify for AfCFTA preferential tariffs, a product must meet the applicable Rule of Origin: "
            "either wholly obtained in Africa, or sufficiently processed/transformed there (e.g. a minimum "
            "percentage of value added, or a change in tariff heading). Processed food products generally "
            "need proof that key inputs were sourced or transformed within an AfCFTA member state, plus a "
            "valid Certificate of Origin issued by an approved exporter or customs authority in the exporting country."
        ),
    },
    {
        "id": "AfCFTA-QA-1",
        "title": "AfCFTA Q&A for MSMEs (AfCFTA Secretariat)",
        "text": (
            "A trader must apply for a Certificate of Origin BEFORE export, submitting an invoice, packing list, "
            "and evidence of origin (e.g. supplier declarations) to the customs/trade authority. Without this "
            "certificate, the shipment will be charged the standard (non-preferential) tariff rate at the border."
        ),
    },
    {
        "id": "KRA-EAC-1",
        "title": "Kenya Revenue Authority - EAC/COMESA Export Basics",
        "text": (
            "For exports from Kenya to Uganda (both EAC and AfCFTA members), a trader typically needs: a KRA PIN, "
            "an export entry declaration via the Customs system, a Certificate of Origin (EAC or AfCFTA), "
            "a commercial invoice, a packing list, and for processed foods, a health/phytosanitary certificate "
            "from the Kenya Bureau of Standards (KEBS) or the relevant food safety authority."
        ),
    },
    {
        "id": "UBOS-1",
        "title": "Uganda Revenue Authority - Import Requirements (general)",
        "text": (
            "Goods entering Uganda require a customs import declaration, and processed food imports typically "
            "require a certificate of conformity or import permit from the Uganda National Bureau of Standards (UNBS), "
            "in addition to standard commercial documents (invoice, packing list, certificate of origin)."
        ),
    },
    {
        "id": "NTB-1",
        "title": "tralac Trade Law Centre - AfCFTA Non-Tariff Barriers",
        "text": (
            "Common barriers traders face at African borders include inconsistent application of rules of origin, "
            "unclear or changing documentation requirements, and delays at customs posts. Traders are advised to "
            "confirm current requirements directly with customs authorities before shipping, since rules can change "
            "and may be applied inconsistently at different border posts."
        ),
    },
]


def build_context():
    return "\n\n".join(f"[{s['id']}] {s['title']}:\n{s['text']}" for s in SOURCES)


SYSTEM_PROMPT = """You are TradePass, an AI assistant that helps small traders in Africa understand what \
documents they need and whether their product likely qualifies for AfCFTA preferential tariffs.
You must ONLY use the SOURCE SNIPPETS given below. Do not invent tariff rates, laws, or requirements that are \
not in the sources.
Rules:
1. Always answer in this structure:
   - **Documents likely needed:** (bullet list)
   - **AfCFTA origin qualification:** (short paragraph: likely yes / likely no / unclear, and why)
   - **Next step:** (one practical action, e.g. which office/authority to confirm with)
   - **Sources used:** (list the [source-id] tags you relied on)
2. If the sources do not clearly cover the question, say so honestly: "I don't have enough information on this \
in my current sources — please confirm with your local customs authority or trade office." Do not guess.
3. Keep the tone practical and simple, for someone who may not be a trade expert.
4. This is general guidance, not legal or customs advice — always end with that one-line disclaimer.
SOURCE SNIPPETS:
{context}
"""


def format_history(history):
    """Turn Gradio chat history into a transcript the model can read."""
    if not history:
        return ""
    lines = []
    for user_msg, assistant_msg in history:
        if user_msg:
            lines.append(f"TRADER (previous): {user_msg}")
        if assistant_msg:
            lines.append(f"TRADEPASS (previous): {assistant_msg}")
    if not lines:
        return ""
    return "\n\nCONVERSATION SO FAR:\n" + "\n".join(lines) + "\n"


def format_error(e):
    """Categorize API/SDK exceptions into user-friendly messages; log full detail server-side."""
    msg = str(e).lower()
    logger.exception("Gemini API call failed")

    if "api key" in msg or "unauthenticated" in msg or "401" in msg or "403" in msg:
        return (
            "⚠️ **Authentication failed**\n\n"
            "Your Gemini API key is missing, invalid, or lacks permission. "
            "Set the `GEMINI_API_KEY` environment variable to a valid key and restart the app.\n\n"
            "_Technical details have been logged._"
        )
    if "rate limit" in msg or "429" in msg or "quota" in msg or "resource_exhausted" in msg:
        return (
            "⚠️ **Rate limit reached**\n\n"
            "You've hit the Gemini API quota or rate limit. Please wait a minute and try again. "
            "If this keeps happening, check your plan/billing in Google AI Studio.\n\n"
            "_Technical details have been logged._"
        )
    if any(k in msg for k in ["connection", "timeout", "network", "unreachable", "dns"]):
        return (
            "⚠️ **Connection problem**\n\n"
            "Couldn't reach the AI service. Check your internet connection and try again.\n\n"
            "_Technical details have been logged._"
        )
    if "safety" in msg or "blocked" in msg or "recitation" in msg:
        return (
            "⚠️ **Response blocked**\n\n"
            "The AI couldn't safely answer that request. Try rephrasing your question.\n\n"
            "_Technical details have been logged._"
        )
    # Fallback
    return (
        "⚠️ **Something went wrong**\n\n"
        "TradePass couldn't generate a response. Please try again. "
        "If the problem persists, contact the app administrator.\n\n"
        f"_Technical details (for admins):_ `{e}`"
    )


def answer_question(user_question, history):
    if not user_question or not user_question.strip():
        return "Please describe what you want to export (product, quantity, from-country, to-country)."

    system_prompt = SYSTEM_PROMPT.format(context=build_context())
    history_block = format_history(history)
    full_prompt = f"{system_prompt}{history_block}\n\nTRADER QUESTION:\n{user_question}"

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
        )
        return response.text
    except Exception as e:
        return format_error(e)


with gr.Blocks(title="TradePass") as demo:
    gr.Markdown(
        """
        # 🌍 TradePass
        **Ask what you need to export your product across African borders — get a document checklist,
        an AfCFTA qualification check, and a next step. Powered by AI, grounded in official trade sources.**
        *Prototype scope: Kenya ↔ Uganda corridor, processed food products. Not legal or customs advice.*
        """
    )
    chatbot = gr.Chatbot(label="TradePass", height=420)
    msg = gr.Textbox(
        label="Describe your export",
        placeholder="e.g. I want to export 200kg of processed avocado oil from Kenya to Uganda",
    )
    clear = gr.Button("Clear")

    def respond(user_message, chat_history):
        chat_history = chat_history or []
        answer = answer_question(user_message, chat_history)
        chat_history.append((user_message, answer))
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)


if __name__ == "__main__":
    demo.launch()
