"""
Data Processing Module.
Handles Excel file parsing, pandas DataFrame operations, shortage analysis,
and database synchronization.
"""
import os
import io
from pathlib import Path
import pandas as pd
from core.database import DatabaseManager, get_db_headers
from core.i18n import t

def detect_structure(file_path: str) -> dict:
    """Reads Excel and returns a dict: {sheet_name: [columns]}."""
    try:
        xl = pd.ExcelFile(file_path)
        structure = {}
        for sheet in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet, nrows=0)
            structure[sheet] = df.columns.tolist()
        return structure
    except Exception as e:
        raise RuntimeError(t("error_excel_structure", e=e))

def load_sheet(file_path: str, sheet_name: str) -> pd.DataFrame:
    """Loads a specific sheet from Excel."""
    return pd.read_excel(file_path, sheet_name=sheet_name)

def migrate_inventory(file_path: Path, db_path: Path, mapping: dict):
    """
    Migrates data from Excel to SQLite 'stok' table with dynamic schema sync.
    Evolves the database structure to include all headers found in the Excel file.
    """
    df = load_sheet(str(file_path), mapping["bom_sheet"])
    df.columns = df.columns.str.strip()
    id_col = mapping["bom_id_col"]
    qty_col = mapping["bom_qty_col"]
    
    # --- Schema Synchronization ---
    with DatabaseManager(db_path) as cursor:
        cursor.execute("PRAGMA table_info(stok)")
        existing_cols = [row[1].lower() for row in cursor.fetchall()]
        
        for col in df.columns:
            # We map the ID and QTY columns to internal names
            if col == id_col or col == qty_col:
                continue
            
            # Check if column exists (case-insensitive)
            if col.lower() not in existing_cols:
                cursor.execute(f"ALTER TABLE stok ADD COLUMN [{col}] TEXT")
                print(f"[SCHEMA_SYNC] New column added: {col}")

    # --- Dynamic Aggregation ---
    agg_dict = {qty_col: "sum"}
    for col in df.columns:
        if col in [id_col, qty_col]: continue
        if "designator" in col.lower():
            agg_dict[col] = lambda x: ", ".join(sorted(list(set(filter(None, map(str, x))))))
        else:
            agg_dict[col] = "first"

    df_agg = df.groupby(id_col).agg(agg_dict).reset_index()
    
    # --- Dynamic Upsert ---
    with DatabaseManager(db_path) as cursor:
        for _, row in df_agg.iterrows():
            part_no_val = str(row[id_col]).strip()
            if not part_no_val or part_no_val.lower() == "nan": continue
            
            # Internal columns: part_no and quantity
            data_cols = ["part_no", "quantity"]
            data_vals = [part_no_val, float(row[qty_col])]
            
            # External columns from Excel
            for col in df.columns:
                if col not in [id_col, qty_col]:
                    data_cols.append(col)
                    data_vals.append(str(row.get(col, "")) if pd.notna(row.get(col)) else "")

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

def get_inventory_from_db(db_path: Path):
    """Fetches all inventory data from SQLite."""
    cols = get_db_headers(db_path)
    with DatabaseManager(db_path) as cursor:
        cursor.execute("SELECT * FROM stok")
        # Convert sqlite3.Row objects to plain tuples for pandas compatibility
        rows = [tuple(r) for r in cursor.fetchall()]
        df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
        df.columns = df.columns.str.strip()
        return df

def calculate_shortages(
    bom_df: pd.DataFrame,
    inv_df: pd.DataFrame,
    bom_id_col: str,
    inv_id_col: str,
    bom_qty_col: str,
    inv_qty_col: str,
) -> pd.DataFrame:
    """
    Merges BOM and Inventory on Part ID.
    Preserves ALL original BOM columns in output.
    Calculates shortage = Required - Available.
    Handles parts completely missing from Inventory.
    """
    # Force plain object dtype to avoid PyArrow string conflicts during merge
    bom_df = bom_df.dropna(subset=[bom_id_col]).copy()
    inv_df = inv_df.dropna(subset=[inv_id_col]).copy()
    
    for col in bom_df.columns:
        bom_df[col] = bom_df[col].astype(object)
    for col in inv_df.columns:
        inv_df[col] = inv_df[col].astype(object)

    # Normalise ID columns: strip whitespace, uppercase
    bom_df[bom_id_col] = bom_df[bom_id_col].astype(str).str.strip().str.upper()
    inv_df[inv_id_col] = inv_df[inv_id_col].astype(str).str.strip().str.upper()

    # Drop rows where the ID is empty
    bom_df = bom_df[bom_df[bom_id_col] != ""]
    inv_df = inv_df[inv_df[inv_id_col] != ""]

    # Coerce quantity columns to numeric
    bom_df[bom_qty_col] = pd.to_numeric(bom_df[bom_qty_col], errors="coerce").fillna(0)
    inv_df[inv_qty_col] = pd.to_numeric(inv_df[inv_qty_col], errors="coerce").fillna(0)

    # Aggregate BOM: sum qty, keep 'first' for all metadata columns
    meta_cols = [c for c in bom_df.columns if c not in (bom_id_col, bom_qty_col)]
    agg_spec  = {bom_qty_col: "sum", **{c: "first" for c in meta_cols}}
    bom_agg   = bom_df.groupby(bom_id_col, as_index=False).agg(agg_spec)
    bom_agg.rename(columns={bom_qty_col: "Required_Qty"}, inplace=True)

    # Aggregate Inventory: only qty needed for the join, add explicit flag
    inv_agg = inv_df.groupby(inv_id_col, as_index=False)[inv_qty_col].sum()
    inv_agg.rename(columns={inv_qty_col: "Available_Qty"}, inplace=True)

    # Merge: Left join (keep all items in the BOM)
    report = pd.merge(bom_agg, inv_agg, left_on=bom_id_col, right_on=inv_id_col, how="left")

    # Handle parts not in inventory
    report["Available_Qty"] = report["Available_Qty"].fillna(0)
    
    # Calculate shortage
    report["Shortage"] = (report["Required_Qty"] - report["Available_Qty"]).clip(lower=0)

    # Return only items with a real shortage
    shortage_report = report[report["Shortage"] > 0].copy()
    shortage_report.sort_values("Shortage", ascending=False, inplace=True)
    shortage_report.reset_index(drop=True, inplace=True)

    return shortage_report, report  # (filtered, full)


def create_updated_inventory(
    inv_df: pd.DataFrame,
    bom_df: pd.DataFrame,
    inv_id_col: str,
    inv_qty_col: str,
    bom_id_col: str,
    bom_qty_col: str,
    output_path: str | None = None,
) -> pd.DataFrame:
    """
    Calculates remaining stock after BOM consumption.
    New_Qty = Available_Qty - Required_Qty  (clipped at 0).
    All original Inventory columns are preserved.
    Saves to Updated_Inventory.xlsx.
    """
    # Drop pure NaNs BEFORE converting to string
    inv_work = inv_df.dropna(subset=[inv_id_col]).copy()
    bom_work = bom_df.dropna(subset=[bom_id_col]).copy()

    # Normalise both ID columns for consistent matching
    inv_work[inv_id_col] = inv_work[inv_id_col].astype(str).str.strip().str.upper()
    bom_work[bom_id_col] = bom_work[bom_id_col].astype(str).str.strip().str.upper()

    # Drop empty strings
    inv_work = inv_work[inv_work[inv_id_col] != ""]
    bom_work = bom_work[bom_work[bom_id_col] != ""]

    # Aggregate BOM quantities per part (sum duplicates) using a TEMP_KEY to avoid column collisions
    TEMP_KEY = "__TEMP_BOM_JOIN_KEY__"
    bom_agg = (
        bom_work[[bom_id_col, bom_qty_col]]
        .copy()
        .assign(**{TEMP_KEY: bom_work[bom_id_col]})
    )
    bom_agg[bom_qty_col] = pd.to_numeric(bom_agg[bom_qty_col], errors="coerce").fillna(0)
    bom_agg = bom_agg.groupby(TEMP_KEY, as_index=False)[bom_qty_col].sum()
    bom_agg.rename(columns={bom_qty_col: "_Required_Qty"}, inplace=True)

    # Left merge: keep ALL inventory rows, attach required qty where matched
    merged = pd.merge(
        inv_work,
        bom_agg,
        how="left",
        left_on=inv_id_col,
        right_on=TEMP_KEY,
    )

    # Fill unmatched parts (not in BOM) with 0 required
    merged["_Required_Qty"] = merged["_Required_Qty"].fillna(0)

    # Coerce inventory qty to numeric
    merged[inv_qty_col] = pd.to_numeric(merged[inv_qty_col], errors="coerce").fillna(0)

    # New quantity = available − required, never below 0
    merged["New_Qty"] = (merged[inv_qty_col] - merged["_Required_Qty"]).clip(lower=0)

    # Drop the temporary BOM ID column and required qty
    merged.drop(columns=["_Required_Qty", TEMP_KEY], inplace=True, errors="ignore")

    # Reorder: put New_Qty right after the original qty column
    cols = merged.columns.tolist()
    if inv_qty_col in cols and "New_Qty" in cols:
        cols.remove("New_Qty")
        insert_at = cols.index(inv_qty_col) + 1
        cols.insert(insert_at, "New_Qty")
    merged = merged[cols]

    try:
        if output_path:
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                merged.to_excel(writer, sheet_name="Updated_Inventory", index=False)
                ws = writer.sheets["Updated_Inventory"]
                for col in ws.columns:
                    max_len = max((len(str(cell.value)) for cell in col if cell.value), default=10)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)
            print(f"[SUCCESS] New inventory levels saved to → {output_path}")
        
        return merged
    except Exception as exc:
        raise RuntimeError(f"[FATAL] Could not process Updated_Inventory: {exc}")


def export_report(shortage_df: pd.DataFrame, full_df: pd.DataFrame, output_path: str) -> None:
    """Writes two sheets: 'Shortages' and 'Full_Comparison' to output_path."""
    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            shortage_df.to_excel(writer, sheet_name="Shortages", index=False)
            full_df.to_excel(writer, sheet_name="Full_Comparison", index=False)

            # Apply basic column width formatting
            for sheet_name in ["Shortages", "Full_Comparison"]:
                ws = writer.sheets[sheet_name]
                for col in ws.columns:
                    max_len = max((len(str(cell.value)) for cell in col if cell.value), default=10)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

        print(f"[SUCCESS] Shortage report saved → {output_path}")
        print(f"  Shortage rows: {len(shortage_df)}")
        print(f"  Total BOM rows compared: {len(full_df)}")
    except Exception as exc:
        raise RuntimeError(f"[FATAL] Could not write output file: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# RESTOCKING: INVENTORY UPDATE
# ──────────────────────────────────────────────────────────────────────────────
def process_restocking(
    inv_df: pd.DataFrame,
    ship_df: pd.DataFrame,
    inv_id_col: str,
    inv_qty_col: str,
    ship_id_col: str,
    ship_qty_col: str,
) -> tuple[pd.DataFrame, int, int]:
    """
    Updates Inventory quantities by adding Shipment quantities.
    Overwrites matching metadata with Shipment metadata.
    Appends completely new parts from Shipment.
    Returns (restocked_df, num_updated, num_new)
    """
    # 0. Force all columns to plain Python 'object' dtype to avoid
    #    PyArrow string dtype conflicts during .update() and assignment.
    inv_work = inv_df.dropna(subset=[inv_id_col]).copy()
    ship_work = ship_df.dropna(subset=[ship_id_col]).copy()
    
    for col in inv_work.columns:
        inv_work[col] = inv_work[col].astype(object)
    for col in ship_work.columns:
        ship_work[col] = ship_work[col].astype(object)

    # 1. Clean and normalize
    inv_work[inv_id_col] = inv_work[inv_id_col].astype(str).str.strip().str.upper()
    ship_work[ship_id_col] = ship_work[ship_id_col].astype(str).str.strip().str.upper()

    inv_work = inv_work[inv_work[inv_id_col] != ""]
    ship_work = ship_work[ship_work[ship_id_col] != ""]

    inv_work[inv_qty_col] = pd.to_numeric(inv_work[inv_qty_col], errors="coerce").fillna(0)
    ship_work[ship_qty_col] = pd.to_numeric(ship_work[ship_qty_col], errors="coerce").fillna(0)

    # 2. Aggregate shipment (sum quantities, take last for metadata)
    ship_meta = [c for c in ship_work.columns if c not in (ship_id_col, ship_qty_col)]
    agg_spec = {ship_qty_col: "sum", **{c: "last" for c in ship_meta}}
    ship_agg = ship_work.groupby(ship_id_col).agg(agg_spec)

    # 3. Index inventory
    inv_meta = [c for c in inv_work.columns if c not in (inv_id_col, inv_qty_col)]
    inv_agg_spec = {inv_qty_col: "sum", **{c: "first" for c in inv_meta}}
    inv_indexed = inv_work.groupby(inv_id_col).agg(inv_agg_spec)

    original_inv_parts = set(inv_indexed.index)
    shipment_parts = set(ship_agg.index)

    updated_parts = original_inv_parts.intersection(shipment_parts)
    new_parts = shipment_parts - original_inv_parts

    num_updated = len(updated_parts)
    num_new = len(new_parts)

    # 4. Overwrite overlapping metadata from shipment
    #    Cast overlap columns to object on BOTH sides to prevent Arrow dtype clash
    overlap_cols = [c for c in ship_agg.columns if c in inv_indexed.columns and c != ship_qty_col]
    if overlap_cols:
        for c in overlap_cols:
            inv_indexed[c] = inv_indexed[c].astype(object)
            ship_agg[c] = ship_agg[c].astype(object)
        inv_indexed.update(ship_agg[overlap_cols])

    # 5. Add quantities
    inv_qty_series = inv_indexed[inv_qty_col].fillna(0)
    ship_qty_series = ship_agg[ship_qty_col].fillna(0)
    inv_indexed[inv_qty_col] = inv_qty_series.add(ship_qty_series, fill_value=0)

    # 6. Add new metadata columns from shipment
    new_cols = [c for c in ship_agg.columns if c not in inv_indexed.columns and c != ship_qty_col]
    for c in new_cols:
        inv_indexed[c] = ship_agg[c].astype(object)

    # 7. Append entirely new rows
    if num_new > 0:
        new_rows = ship_agg.loc[list(new_parts)].copy()
        new_rows.rename(columns={ship_qty_col: inv_qty_col}, inplace=True)
        inv_indexed = pd.concat([inv_indexed, new_rows])

    inv_indexed.reset_index(inplace=True)

    # Reorder columns: put ID first, Qty second
    cols = inv_indexed.columns.tolist()
    if inv_qty_col in cols:
        cols.remove(inv_qty_col)
        cols.insert(1, inv_qty_col)
    inv_indexed = inv_indexed[cols]

    return inv_indexed, num_updated, num_new

