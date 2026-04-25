import os
import sys
import io
import traceback
import json
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import set_key

# Capture stdout/stderr redirection for Streamlit logging inside terminal, 
# since core modules heavily print to console.
from core.processor import (
    detect_structure, load_sheet, calculate_shortages, 
    process_restocking, export_report, create_updated_inventory,
    migrate_inventory, get_inventory_from_db
)
from core.llm import ask_llm_to_map, ask_llm_to_map_restock
from core.database import init_db, DatabaseManager, get_db_headers
from core.i18n import t, get_lang, LANG_OPTIONS

# --- Database Initialization ---
DB_PATH = Path(__file__).resolve().parent / "inventory.db"
init_db(DB_PATH)

# --- Session State: Language ---
if "lang" not in st.session_state:
    st.session_state.lang = "tr"

st.set_page_config(
    page_title=t("page_title"),
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS (Cyberpunk Corporate Dark) ---
_base_css = """
    <style>
    /* Global Background and Text */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* Force visibility for all labels and markdown */
    .stMarkdown, .stRadio, label, p, li {
        color: #FFFFFF !important;
    }
    
    /* Title Styling */
    .main-title {
        background: linear-gradient(90deg, #4CAF50 0%, #2E7D32 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem !important;
        font-weight: 800;
        margin-bottom: 0.1rem;
        text-align: center;
        letter-spacing: -1px;
    }
    .title-underline {
        height: 4px;
        width: 120px;
        background: #4CAF50;
        margin: 0 auto 2.5rem auto;
        border-radius: 2px;
        box-shadow: 0 0 15px rgba(76, 175, 80, 0.4);
    }

    /* Card Styling */
    .custom-card {
        background-color: #262730;
        padding: 2.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        margin-bottom: 2rem;
        border: 1px solid #444;
    }

    /* File Uploader Customization */
    [data-testid="stFileUploader"] {
        border: 1px solid #444;
        border-radius: 10px;
        padding: 10px;
        background-color: #1a1c24;
    }

    /* Button Styling - Emerald Accent */
    .stButton>button {
        border-radius: 8px;
        padding: 0.6rem 2.5rem;
        font-weight: 600;
        background-color: #4CAF50 !important;
        color: #FFFFFF !important;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        background-color: #66BB6A !important;
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.4);
    }
    
    /* Primary (Shutdown) Button */
    button[kind="primary"] {
        background-color: #FF5252 !important;
    }

    /* Sidebar Styling - Clean Contrast */
    [data-testid="stSidebar"] {
        background-color: #1a1c24;
        border-right: 1px solid #333;
    }
    [data-testid="stSidebar"] * {
        color: #A0A0A0 !important;
    }
    [data-testid="stSidebar"] .stButton>button {
        background-color: #31333F !important;
        color: #FFFFFF !important;
        border: 1px solid #444;
    }

    /* Input Fields */
    .stTextInput>div>div>input {
        background-color: #0E1117;
        color: white;
        border: 1px solid #444;
    }

    /* Header Styling */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Fixed Shutdown Button Styling */
    div.fixed-shutdown {
        position: fixed;
        top: 60px;
        left: 15px;
        z-index: 1000;
    }
    div.fixed-shutdown button {
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        background-color: #FF5252 !important;
        color: white !important;
        border: none !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 24px !important;
        box-shadow: 0 4px 12px rgba(255, 82, 82, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    div.fixed-shutdown button:hover {
        background-color: #D32F2F !important;
        transform: scale(1.1) !important;
        box-shadow: 0 0 15px rgba(255, 82, 82, 0.7) !important;
    }
    </style>
"""

# --- RTL CSS Injection for Arabic ---
_rtl_css = """
    <style>
    /* RTL overrides for Arabic locale */
    .stApp {
        direction: rtl;
        text-align: right;
    }
    .main-title {
        text-align: center;  /* Keep title centred even in RTL */
    }
    /* Keep data tables LTR for readability */
    [data-testid="stDataFrame"],
    [data-testid="stDataEditor"],
    .stDataFrame,
    table {
        direction: ltr !important;
        text-align: left !important;
    }
    /* Flip the shutdown button to the right side */
    div.fixed-shutdown {
        left: auto;
        right: 15px;
    }
    /* Selectbox and input alignment */
    .stSelectbox, .stTextInput, .stNumberInput {
        text-align: right;
    }
    </style>
"""

if get_lang() == "ar":
    st.markdown(_base_css + _rtl_css, unsafe_allow_html=True)
else:
    st.markdown(_base_css, unsafe_allow_html=True)


def check_and_fix_mapping(df, mapped_col):
    if mapped_col in df.columns:
        return mapped_col
    # Case-insensitive search
    match = next((c for c in df.columns if str(c).lower() == str(mapped_col).lower()), None)
    if match:
        return match
    raise ValueError(
        t("error_column_not_found", col=mapped_col, cols=df.columns.tolist())
    )

def get_col_safely(row, target_col, fallback_val=None):
    """Safely get a value from a Series/Row using case-insensitive column matching."""
    if target_col in row.index:
        return row[target_col]
    # Try case-insensitive
    match = next((c for c in row.index if str(c).lower() == str(target_col).lower()), None)
    if match:
        return row[match]
    return fallback_val

st.markdown(f'<h1 class="main-title">{t("main_heading")}</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-underline"></div>', unsafe_allow_html=True)

# --- Session State Initialization ---
if "processing_done" not in st.session_state:
    st.session_state.processing_done = False
if "shortage_df" not in st.session_state:
    st.session_state.shortage_df = None

def reset_session():
    st.session_state.processing_done = False
    st.session_state.shortage_df = None

# --- Fixed Floating Shutdown Button ---
st.markdown('<div class="fixed-shutdown">', unsafe_allow_html=True)
if st.button("🚫", help=t("btn_shutdown_help"), key="fixed_exit"):
    os._exit(0)
st.markdown('</div>', unsafe_allow_html=True)

# --- API Guard UI ---
groq_key = os.environ.get("GROQ_API_KEY", "").strip() or st.session_state.get("GROQ_API_KEY", "").strip()

if not groq_key:
    st.warning("⚠️ SmartInventory requires a Groq API Key to function.")
    with st.form("api_guard_form"):
        new_key = st.text_input("Enter Groq API Key:", type="password")
        if st.form_submit_button("Save"):
            if new_key.strip():
                env_path = Path(__file__).resolve().parent / ".env"
                set_key(str(env_path), "GROQ_API_KEY", new_key.strip())
                os.environ["GROQ_API_KEY"] = new_key.strip()
                st.session_state["GROQ_API_KEY"] = new_key.strip()
                from core import config
                config.reload_config()
                st.success("API Key saved! Reloading...")
                st.rerun()
    st.stop()

# --- Current Keys ---
current_groq = os.getenv("GROQ_API_KEY", "")
current_gemini = os.getenv("GEMINI_API_KEY", "")

# --- Tab Structure ---
tab_stok, tab_sevkiyat, tab_ayarlar = st.tabs([
    t("tab_stock"), t("tab_shipment"), t("tab_settings")
])

with tab_stok:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader(t("stock_subheader"))
    
    col_search, col_threshold = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(t("search_placeholder"), "", key="stok_search")
    with col_threshold:
        threshold = st.number_input(t("critical_threshold"), value=0, min_value=0)

    inventory_df = get_inventory_from_db(DB_PATH)
    
    if not inventory_df.empty:
        # --- Aggressive Data Type Normalization ---
        # Force EVERY cell to a native Python type (no numpy, no sqlite3.Row, no NaT)
        for col in inventory_df.columns:
            if col.lower() == "quantity":
                inventory_df[col] = pd.to_numeric(inventory_df[col], errors="coerce").fillna(0.0)
            else:
                # Convert column to object dtype first, then fill None/NaN, then str
                inventory_df[col] = inventory_df[col].where(inventory_df[col].notna(), "")
                inventory_df[col] = inventory_df[col].apply(lambda v: str(v) if v is not None and str(v) not in ("None", "nan", "NaT", "NaN") else "")

        if search_query:
            mask = inventory_df.apply(lambda row_s: search_query.lower() in str(row_s).lower(), axis=1)
            filtered_inventory_df = inventory_df[mask].copy()
        else:
            filtered_inventory_df = inventory_df.copy()

        # --- Build dynamic column_config for ALL columns ---
        col_config = {}
        for col in filtered_inventory_df.columns:
            if col.lower() == "part_no":
                col_config[col] = st.column_config.TextColumn(
                    t("col_manufacturer_part"), disabled=True
                )
            elif col.lower() == "quantity":
                col_config[col] = st.column_config.NumberColumn(
                    t("col_quantity"), min_value=0
                )
            elif col.lower() == "last_updated":
                col_config[col] = st.column_config.TextColumn(
                    t("col_last_updated"), disabled=True
                )
            else:
                col_config[col] = st.column_config.TextColumn(col)

        try:
            edited_df = st.data_editor(
                filtered_inventory_df,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key="stok_editor",
                column_config=col_config
            )
        except Exception as editor_err:
            st.error(t("error_table_display", e=editor_err))
            # Diagnostic dump
            for col in filtered_inventory_df.columns:
                unique_types = set(type(v).__name__ for v in filtered_inventory_df[col].values)
                st.caption(
                    t("caption_column_types", col=col, types=unique_types, dtype=filtered_inventory_df[col].dtype)
                )
            edited_df = filtered_inventory_df  # fallback

        
        if st.button(t("btn_save_db"), key="save_db"):
            try:
                with DatabaseManager(DB_PATH) as cursor:
                    for _, row in edited_df.iterrows():
                        # Build dynamic update query
                        # Find the actual part_no column (might be case-variant)
                        actual_id_col = next((c for c in inventory_df.columns if c.lower() == "part_no"), "part_no")
                        actual_date_col = next((c for c in inventory_df.columns if c.lower() == "last_updated"), "last_updated")
                        
                        upd_cols = [c for c in inventory_df.columns if c.lower() not in ["part_no", "last_updated"]]
                        set_clause = ", ".join([f"[{c}] = ?" for c in upd_cols])
                        
                        vals = []
                        for c in upd_cols:
                            vals.append(get_col_safely(row, c))
                        
                        id_val = get_col_safely(row, actual_id_col)
                        vals.append(id_val)
                        
                        sql = f"UPDATE stok SET {set_clause}, last_updated = CURRENT_TIMESTAMP WHERE [{actual_id_col}] = ?"
                        cursor.execute(sql, vals)
                st.success(t("success_db_updated"))
                st.rerun()
            except Exception as e:
                st.error(t("error_save", e=e))
        
        st.caption(t("caption_total_parts", count=len(filtered_inventory_df)))
    else:
        st.info(t("info_db_empty"))
    st.markdown('</div>', unsafe_allow_html=True)

with tab_sevkiyat:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader(t("shipment_subheader"))
    
    sevkiyat_mode = st.radio(
        t("radio_operation_type"),
        [t("radio_shortage_analysis"), t("radio_restock")],
        horizontal=True,
    )
    st.divider()

    if t("radio_shortage_analysis") in sevkiyat_mode:
        st.markdown(t("upload_center"))
        col1, col2 = st.columns([1, 1])
        with col1:
            bom_file = st.file_uploader(
                t("upload_bom"), 
                type=["xlsx"], 
                key="bom_up",
                help=t("upload_bom_help"),
            )
        with col2:
            inv_file = st.file_uploader(
                t("upload_external_stock"), 
                type=["xlsx"], 
                key="st_up",
                help=t("upload_external_stock_help"),
            )
            
        if bom_file:
            if st.button(t("btn_start_analysis"), key="start_analysis"):
                with st.spinner(t("spinner_analysing")):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_bom_file:
                            temp_bom_file.write(bom_file.getvalue())
                            bom_file_path = temp_bom_file.name
                        
                        bom_structure = detect_structure(bom_file_path)
                        
                        if inv_file:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_inv_file:
                                temp_inv_file.write(inv_file.getvalue())
                                inv_file_path = temp_inv_file.name
                            inv_structure = detect_structure(inv_file_path)
                        else:
                            inv_headers = get_db_headers(DB_PATH)
                            print(f"[LLM_DEBUG] Final Inv Headers (from SQL): {inv_headers}")
                            inv_structure = {"SQL_Database": inv_headers}
                        
                        mapping = ask_llm_to_map(bom_structure, inv_structure)
                        
                        if mapping["bom_sheet"] not in bom_structure:
                            mapping["bom_sheet"] = list(bom_structure.keys())[0]
                        
                        bom_df = load_sheet(bom_file_path, mapping["bom_sheet"])
                        
                        if inv_file:
                            if mapping["inv_sheet"] not in inv_structure:
                                mapping["inv_sheet"] = list(inv_structure.keys())[0]
                            inv_df = load_sheet(inv_file_path, mapping["inv_sheet"])
                        else:
                            mapping["inv_sheet"] = "SQL_Database"
                            inv_df = get_inventory_from_db(DB_PATH)

                        bom_id = check_and_fix_mapping(bom_df, mapping["bom_id_col"])
                        bom_qty = check_and_fix_mapping(bom_df, mapping["bom_qty_col"])
                        inv_id = check_and_fix_mapping(inv_df, mapping["inv_id_col"])
                        inv_qty = check_and_fix_mapping(inv_df, mapping["inv_qty_col"])
                        
                        # === DEBUG BLOCK (Analysis) ===
                        print(f"[TRACE] bom_df.columns = {bom_df.columns.tolist()}")
                        print(f"[TRACE] inv_df.columns = {inv_df.columns.tolist()}")
                        print(f"[TRACE] bom_id={bom_id}, bom_qty={bom_qty}, inv_id={inv_id}, inv_qty={inv_qty}")
                        print(f"[TRACE] inv_df dtypes = {inv_df.dtypes.to_dict()}")
                        # === END DEBUG ===
                        
                        shortage_df, full_df = calculate_shortages(bom_df, inv_df, bom_id, inv_id, bom_qty, inv_qty)
                        
                        st.session_state.shortage_df = shortage_df
                        st.session_state.bom_df = bom_agg if 'bom_agg' in locals() else bom_df
                        st.session_state.bom_id = bom_id
                        st.session_state.bom_qty = bom_qty
                        st.session_state.processing_done = True
                        st.rerun()

                    except Exception as e:
                        st.error(t("error_generic", e=e))
                        st.code(traceback.format_exc())
                    finally:
                        if 'bom_file_path' in locals(): Path(bom_file_path).unlink(missing_ok=True)
                        if 'inv_file_path' in locals(): Path(inv_file_path).unlink(missing_ok=True)

    elif t("radio_restock") in sevkiyat_mode:
        st.markdown(t("upload_center"))
        ship_file = st.file_uploader(t("upload_shipment"), type=["xlsx"], key="ship_up")
        if ship_file:
            if st.button(t("btn_update_stock"), key="start_restock"):
                with st.spinner(t("spinner_updating")):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_ship_file:
                            temp_ship_file.write(ship_file.getvalue())
                            ship_file_path = temp_ship_file.name
                        
                        inv_df = get_inventory_from_db(DB_PATH)
                        inv_headers = inv_df.columns.tolist()
                        print(f"[TRACE] Inv Headers (Restock): {inv_headers}")
                        print(f"[TRACE] Inv dtypes: {inv_df.dtypes.to_dict()}")
                        inv_structure = {"SQL_Database": inv_headers}
                        ship_structure = detect_structure(ship_file_path)
                        
                        mapping = ask_llm_to_map_restock(inv_structure, ship_structure)
                        mapping["inv_sheet"] = "SQL_Database"
                        if mapping["ship_sheet"] not in ship_structure:
                            mapping["ship_sheet"] = list(ship_structure.keys())[0]
                            
                        ship_df = load_sheet(ship_file_path, mapping["ship_sheet"])
                        
                        inv_id = check_and_fix_mapping(inv_df, mapping["inv_id_col"])
                        inv_qty = check_and_fix_mapping(inv_df, mapping["inv_qty_col"])
                        ship_id = check_and_fix_mapping(ship_df, mapping["ship_id_col"])
                        ship_qty = check_and_fix_mapping(ship_df, mapping["ship_qty_col"])
                        
                        # === DEBUG BLOCK (Restock) ===
                        print(f"[TRACE] inv_id={inv_id}, inv_qty={inv_qty}, ship_id={ship_id}, ship_qty={ship_qty}")
                        print(f"[TRACE] inv_df cols: {inv_df.columns.tolist()}")
                        print(f"[TRACE] ship_df cols: {ship_df.columns.tolist()}")
                        # === END DEBUG ===
                        
                        restocked_df, num_upd, num_new = process_restocking(inv_df, ship_df, inv_id, inv_qty, ship_id, ship_qty)
                        
                        print(f"[TRACE] restocked_df cols: {restocked_df.columns.tolist()}")
                        
                        # UPDATE DB (Fully Dynamic — NO hardcoded column names)
                        with DatabaseManager(DB_PATH) as cursor:
                            for _, row in restocked_df.iterrows():
                                # Use the ACTUAL mapped column names, not hardcoded 'part_no'
                                id_val = str(row[inv_id]).strip()
                                qty_val = float(row[inv_qty]) if pd.notna(row[inv_qty]) else 0.0
                                
                                data_cols = ["part_no", "quantity"]
                                data_vals = [id_val, qty_val]
                                
                                # Add other columns from restocked_df
                                for col in restocked_df.columns:
                                    if col not in [inv_id, inv_qty]:
                                        data_cols.append(col)
                                        val = row[col]
                                        data_vals.append(str(val) if pd.notna(val) else "")

                                cols_sql = ", ".join([f"[{c}]" for c in data_cols])
                                ques_sql = ", ".join(["?" for _ in data_vals])
                                upd_sql = ", ".join([f"[{c}] = excluded.[{c}]" for c in data_cols if c != "part_no"])
                                
                                sql = f"""
                                    INSERT INTO stok ({cols_sql}, last_updated)
                                    VALUES ({ques_sql}, CURRENT_TIMESTAMP)
                                    ON CONFLICT(part_no) DO UPDATE SET
                                        {upd_sql},
                                        last_updated = CURRENT_TIMESTAMP
                                """
                                cursor.execute(sql, data_vals)
                        
                        st.success(t("success_restock", updated=num_upd, new=num_new))
                        st.rerun()
                    except Exception as e:
                        st.error(t("error_generic", e=e))
                        st.code(traceback.format_exc())
                    finally:
                        if 'ship_file_path' in locals(): Path(ship_file_path).unlink(missing_ok=True)
    if st.session_state.processing_done and st.session_state.shortage_df is not None:
        st.write(t("label_analysis_result"))
        st.dataframe(st.session_state.shortage_df)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            if st.button(t("btn_consume"), key="consume_btn"):
                try:
                    bom_df_state = st.session_state.get("bom_df")
                    bom_id_state = st.session_state.get("bom_id")
                    bom_qty_state = st.session_state.get("bom_qty")
                    if bom_df_state is not None:
                        with DatabaseManager(DB_PATH) as cursor:
                            for _, row in bom_df_state.iterrows():
                                # Use safety fetch for ID and QTY
                                val_id = get_col_safely(row, bom_id_state)
                                if val_id is None: continue
                                
                                part_number = str(val_id).strip().upper()
                                
                                # Try bom_qty_state first, then 'Required_Qty', then 0
                                quantity_value = get_col_safely(row, bom_qty_state)
                                if quantity_value is None:
                                    quantity_value = get_col_safely(row, "Required_Qty", 0)
                                
                                try:
                                    quantity_value = float(quantity_value)
                                except ValueError:
                                    quantity_value = 0.0

                                cursor.execute("UPDATE stok SET quantity = MAX(0, quantity - ?), last_updated = CURRENT_TIMESTAMP WHERE UPPER(part_no) = ?", (quantity_value, part_number))
                        st.success(t("success_consumed"))
                        reset_session()
                        st.rerun()
                except Exception as e:
                    st.error(t("error_consumption", e=e))
        with col_res2:
            if st.button(t("btn_clear"), key="clear_res"):
                reset_session()
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

with tab_ayarlar:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader(t("settings_subheader"))

    # ── Language Selector (top of settings) ──────────────────────────────
    lang_labels = list(LANG_OPTIONS.keys())
    current_code = get_lang()
    # Find the index of the current language in the options list
    current_idx = next(
        (i for i, lbl in enumerate(lang_labels) if LANG_OPTIONS[lbl] == current_code),
        0,
    )
    selected_lang_label = st.selectbox(
        t("label_language"),
        lang_labels,
        index=current_idx,
        key="lang_selector",
    )
    new_lang_code = LANG_OPTIONS[selected_lang_label]
    if new_lang_code != current_code:
        st.session_state.lang = new_lang_code
        st.rerun()

    st.divider()
    
    # API Keys
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        new_groq = st.text_input("Groq API Key", type="password", value=current_groq, key="groq_set")
    with col_a2:
        new_gemini = st.text_input("Gemini API Key", type="password", value=current_gemini, key="gemini_set")
    
    if st.button(t("btn_save_keys"), key="save_keys"):
        env_path = Path(__file__).resolve().parent / ".env"
        set_key(str(env_path), "GROQ_API_KEY", new_groq)
        set_key(str(env_path), "GEMINI_API_KEY", new_gemini)
        # Reload config
        from core import config
        config.reload_config()
        st.success(t("success_keys_saved"))
    
    st.divider()
    st.subheader(t("data_transfer_subheader"))
    if st.button(t("btn_migration"), key="run_mig"):
        try:
            init_file = Path(__file__).resolve().parent / "data" / "1.xlsx"
            if init_file.exists():
                struct = detect_structure(str(init_file))
                st.info(t("info_detected_structure", struct=struct))
                mapping = {"bom_sheet": list(struct.keys())[0], "bom_id_col": "Manufacturer Part", "bom_qty_col": "Quantity"}
                migrate_inventory(init_file, DB_PATH, mapping)
                st.success(t("success_migration"))
                st.rerun()
            else:
                st.error(t("error_file_not_found"))
        except Exception as e:
            st.error(t("error_generic", e=e))
            st.code(traceback.format_exc())
    
    # --- DB Inspection Panel ---
    st.divider()
    st.subheader(t("db_status_subheader"))
    db_headers = get_db_headers(DB_PATH)
    st.write(t("label_columns", count=len(db_headers), cols=db_headers))
    try:
        df_check = get_inventory_from_db(DB_PATH)
        st.write(t("label_record_count", count=len(df_check)))
        if not df_check.empty:
            st.write(t("label_data_types"), df_check.dtypes.to_dict())
            # Show raw types of each value in first row
            first_row = df_check.iloc[0]
            raw_types = {col: type(first_row[col]).__name__ for col in df_check.columns}
            st.write(t("label_first_row_types"), raw_types)
    except Exception as db_err:
        st.warning(t("warning_db_read_error", e=db_err))

    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
