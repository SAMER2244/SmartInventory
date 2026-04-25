"""
Large Language Model (LLM) Manager Module.
Handles fallback logic between Groq and Gemini and orchestrates the multi-stage
column mapping prompts for inventory management.
"""
import sys
import json
import re
import time
import traceback
from google.genai import types

# Import from local config module
from core import config

def _call_gemini_fallback(prompt: str, original_error: Exception = None) -> str:
    """
    Gemini fallback: retries on 429/503, then exits if still failing.
    Called only when Groq is exhausted or unavailable.
    """
    if not config.GEMINI_CLIENT:
        if original_error:
            raise RuntimeError(f"Groq primary failed, and Gemini fallback is missing. Groq Error: {original_error}")
        else:
            raise RuntimeError("No API keys provided for inference. Please configure Groq or Gemini.")

    print(f"[FALLBACK] Switching to Gemini ({config._get_gemini_model()})...")
    RETRYABLE = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")
    for attempt in range(1, 4):
        try:
            response = config.GEMINI_CLIENT.models.generate_content(
                model=config._get_gemini_model(),
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            return response.text.strip()
        except Exception as exc:
            err_str = str(exc)
            print(f"[DEBUG] Gemini Exception Details:\n{traceback.format_exc()}")
            if any(tag in err_str for tag in RETRYABLE):
                wait = 30 * attempt
                print(f"  [WARN] Gemini also rate-limited (attempt {attempt}/3). Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise RuntimeError(f"Gemini API Error: {exc}")
    raise RuntimeError("Both Groq and Gemini exhausted. Try again later.")


def _llm_call(prompt: str) -> str:
    """
    Unified LLM call. Groq (Llama-3-8B) is the primary engine.
    On Groq 429/failure after MAX_RETRIES → delegates to Gemini fallback.
    """
    RETRYABLE = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "rate_limit")

    if config.GROQ_CLIENT:
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                chat = config.GROQ_CLIENT.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a data engineer. "
                                "Return ONLY valid JSON. No markdown. No explanation."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                )
                return chat.choices[0].message.content.strip()

            except Exception as exc:
                err_str = str(exc).lower()
                print(f"[DEBUG] Groq Exception Details:\n{traceback.format_exc()}")
                if any(tag.lower() in err_str for tag in RETRYABLE):
                    wait = config.RETRY_BASE * attempt   # 10s, 20s, 30s …
                    print(
                        f"  [WARN] Groq rate limit (attempt {attempt}/{config.MAX_RETRIES}). "
                        f"Waiting {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    print(f"  [WARN] Groq primary failed: {exc}. Switching to Gemini fallback...")
                    return _call_gemini_fallback(prompt, original_error=exc)

        print("  [WARN] All Groq retries exhausted. Switching to Gemini fallback...")
        return _call_gemini_fallback(prompt, original_error=RuntimeError("Groq max retries exhausted"))

    # Groq not configured — go straight to Gemini
    return _call_gemini_fallback(prompt)


def _parse_json(raw: str, stage: str) -> dict:
    """Finds JSON block within response and parses it. Exits on failure."""
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise RuntimeError(f"[FATAL] {stage} — No JSON object found in response.\nRaw:\n{raw}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"[FATAL] {stage} — Invalid JSON.\nRaw:\n{raw}\nError: {exc}")


def _wait(stage_num: int) -> None:
    """Prints cooldown banner and sleeps STAGE_DELAY seconds."""
    print(f"[STAGE {stage_num}] Done. Waiting {config.STAGE_DELAY}s for next stage...")
    time.sleep(config.STAGE_DELAY)


def ask_llm_to_map(file_a_structure: dict, file_b_structure: dict) -> dict:
    """
    4-stage schema mapping via _llm_call() with 15s delays.
    Primary engine: Groq/Llama-3-8B. Fallback: Gemini.
    Returns combined mapping dict.
    """
    a_sheet_list = list(file_a_structure.keys())
    b_sheet_list = list(file_b_structure.keys())

    # ── STAGE 1: Find BOM sheet in FILE A ─────────────────────────────────────
    print("\n[PRIMARY: GROQ] Stage 1/4 — Identifying BOM sheet in FILE A...")
    prompt_1 = (
        f"FILE A has these Excel sheets: {a_sheet_list}.\n"
        "Which sheet is most likely the Bill of Materials (BOM) "
        "(parts list, components, required materials)?\n"
        "Return ONLY valid JSON, no markdown: {\"bom_sheet\": \"<exact sheet name>\"}"
    )
    response_1 = _parse_json(_llm_call(prompt_1), "STAGE 1")
    bom_sheet = response_1.get("bom_sheet") or a_sheet_list[0]
    _wait(1)

    # ── STAGE 2: Find Inventory sheet in FILE B ────────────────────────────────
    print("[PRIMARY: GROQ] Stage 2/4 — Identifying Inventory sheet in FILE B...")
    prompt_2 = (
        f"FILE B has these Excel sheets: {b_sheet_list}.\n"
        "Which sheet is most likely the Inventory or Stock list "
        "(current stock, available quantities, warehouse)?\n"
        "Return ONLY valid JSON, no markdown: {\"inv_sheet\": \"<exact sheet name>\"}"
    )
    response_2 = _parse_json(_llm_call(prompt_2), "STAGE 2")
    inv_sheet = response_2.get("inv_sheet") or b_sheet_list[0]
    _wait(2)

    # ── STAGE 3: Map BOM columns ───────────────────────────────────────────────
    print("[PRIMARY: GROQ] Stage 3/4 — Mapping columns in BOM sheet...")
    bom_headers = file_a_structure.get(bom_sheet, [])
    prompt_3 = (
        f"The BOM sheet has these column headers: {bom_headers}.\n"
        "Identify:\n"
        "  1. The Part ID / Part Number / Item Code column.\n"
        "  2. The Required Quantity column.\n"
        "Return ONLY valid JSON, no markdown:\n"
        "{\"bom_id_col\": \"<exact col name>\", \"bom_qty_col\": \"<exact col name>\"}"
    )
    response_3 = _parse_json(_llm_call(prompt_3), "STAGE 3")
    bom_id_col  = response_3.get("bom_id_col")  or bom_headers[0]
    bom_qty_col = response_3.get("bom_qty_col") or bom_headers[-1]
    _wait(3)

    # ── STAGE 4: Map Inventory columns ────────────────────────────────────────
    print("[PRIMARY: GROQ] Stage 4/4 — Mapping columns in Inventory sheet...")
    inv_headers = file_b_structure.get(inv_sheet, [])
    prompt_4 = (
        f"The Inventory sheet has these column headers: {inv_headers}.\n"
        "Identify:\n"
        "  1. The Part ID / Part Number / Item Code column.\n"
        "  2. The Available / In-Stock Quantity column.\n"
        "Return ONLY valid JSON, no markdown:\n"
        "{\"inv_id_col\": \"<exact col name>\", \"inv_qty_col\": \"<exact col name>\"}"
    )
    response_4 = _parse_json(_llm_call(prompt_4), "STAGE 4")
    inv_id_col  = response_4.get("inv_id_col")  or inv_headers[0]
    inv_qty_col = response_4.get("inv_qty_col") or inv_headers[-1]
    print("[PRIMARY: GROQ] Stage 4/4 complete.")

    # ── Assemble final mapping ─────────────────────────────────────────────────
    mapping = {
        "bom_sheet":   bom_sheet,
        "inv_sheet":   inv_sheet,
        "bom_id_col":  bom_id_col,
        "inv_id_col":  inv_id_col,
        "bom_qty_col": bom_qty_col,
        "inv_qty_col": inv_qty_col,
    }
    print(f"\n[INFO] Final mapping:\n{json.dumps(mapping, indent=2, ensure_ascii=False)}")
    return mapping


def ask_llm_to_map_restock(inv_structure: dict, ship_structure: dict) -> dict:
    """
    3-stage schema mapping for Restocking.
    Primary engine: Groq/Llama-3-8B. Fallback: Gemini.
    """
    inv_sheet_list = list(inv_structure.keys())
    ship_sheet_list = list(ship_structure.keys())

    # ── STAGE 1: Find Inventory sheet ──────────────────────────────────────────
    print("\n[PRIMARY: GROQ] Stage 1/3 — Identifying Inventory sheet...")
    prompt_1 = (
        f"FILE A has these Excel sheets: {inv_sheet_list}.\n"
        "Which sheet is most likely the current Inventory or Stock list?\n"
        "Return ONLY valid JSON, no markdown: {\"inv_sheet\": \"<exact sheet name>\"}"
    )
    response_1 = _parse_json(_llm_call(prompt_1), "STAGE 1")
    inv_sheet = response_1.get("inv_sheet") or inv_sheet_list[0]
    _wait(1)

    # ── STAGE 2: Find Shipment sheet ───────────────────────────────────────────
    print("[PRIMARY: GROQ] Stage 2/3 — Identifying Shipment sheet...")
    prompt_2 = (
        f"FILE B has these Excel sheets: {ship_sheet_list}.\n"
        "Which sheet is most likely the incoming Shipment, Receiving, or Delivery list?\n"
        "Return ONLY valid JSON, no markdown: {\"ship_sheet\": \"<exact sheet name>\"}"
    )
    response_2 = _parse_json(_llm_call(prompt_2), "STAGE 2")
    ship_sheet = response_2.get("ship_sheet") or ship_sheet_list[0]
    _wait(2)

    # ── STAGE 3: Map Columns ───────────────────────────────────────────────────
    print("[PRIMARY: GROQ] Stage 3/3 — Mapping columns in both sheets...")
    
    # Extract headers properly (Flatten dictionary to get the first sheet's headers if identified one fails)
    inv_headers = inv_structure.get(inv_sheet) or (next(iter(inv_structure.values())) if inv_structure else [])
    ship_headers = ship_structure.get(ship_sheet) or (next(iter(ship_structure.values())) if ship_structure else [])

    print(f"[LLM_DEBUG] Final Inv Headers: {inv_headers}")
    print(f"[LLM_DEBUG] Final Ship Headers: {ship_headers}")

    if not inv_headers or not ship_headers:
        raise RuntimeError("Hata: Dosya başlıkları okunamadı. Lütfen dosyanın boş olmadığından ve başlıkların ilk satırda olduğundan emin olun.")
    
    prompt_3 = (
        f"Inventory headers: {inv_headers}\n"
        f"Shipment headers: {ship_headers}\n"
        "Identify the Part ID and Quantity columns in both.\n"
        "Return ONLY valid JSON, no markdown:\n"
        "{\"inv_id_col\": \"<col>\", \"inv_qty_col\": \"<col>\", \"ship_id_col\": \"<col>\", \"ship_qty_col\": \"<col>\"}"
    )
    # Stage 3 Retry Logic
    for attempt in range(1, 3):
        try:
            response_3 = _parse_json(_llm_call(prompt_3), "STAGE 3")
            break
        except Exception as e:
            if attempt == 1:
                print(f"  [RETRY] Stage 3 failed: {e}. Waiting 20s for one last try...")
                time.sleep(20)
            else:
                raise e
    
    mapping = {
        "inv_sheet": inv_sheet,
        "ship_sheet": ship_sheet,
        "inv_id_col": response_3.get("inv_id_col") or (inv_headers[0] if inv_headers else "Unknown"),
        "inv_qty_col": response_3.get("inv_qty_col") or (inv_headers[-1] if inv_headers else "Unknown"),
        "ship_id_col": response_3.get("ship_id_col") or (ship_headers[0] if ship_headers else "Unknown"),
        "ship_qty_col": response_3.get("ship_qty_col") or (ship_headers[-1] if ship_headers else "Unknown"),
    }
    print("[PRIMARY: GROQ] Stage 3/3 complete.")
    print(f"\n[INFO] Final mapping:\n{json.dumps(mapping, indent=2, ensure_ascii=False)}")
    return mapping
