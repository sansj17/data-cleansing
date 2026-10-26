"""ERP migration readiness dashboard. Run: uv run streamlit run dashboard/app.py"""

import shutil
import sys
import tempfile
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import cleanse  # noqa: E402

TABLES = ("vendors", "purchase_orders", "invoices")
# The first statement of profile.sql is the one-row-per-check summary.
PROFILE = (ROOT / "sql" / "profile.sql").read_text().split(";")[0]

st.set_page_config(page_title="ERP migration readiness", layout="wide")


@st.cache_resource
def cleansed():
    """Raw tables plus clean_*, quarantine_* and review outputs, built on a copy so the real database is never written."""
    tmp = Path(tempfile.mkdtemp()) / "suppliers.duckdb"
    shutil.copy(ROOT / "suppliers.duckdb", tmp)
    con = duckdb.connect(str(tmp))
    cleanse.run(con)
    return con


con = cleansed()
if st.sidebar.button("Re-run cleansing rules"):
    cleansed.clear()
    st.rerun()
st.sidebar.caption("Copies the raw database and applies sql/cleanse/*.sql again, so a rule change shows up here.")


def q(sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


def profile(prefix: str) -> pd.DataFrame:
    """Run the profile checks on raw (prefix '') or cleansed ('clean_') tables."""
    scratch = duckdb.connect()
    for t in TABLES:
        df = q(f"SELECT * FROM {prefix}{t}")  # noqa: F841 - read by the scratch connection
        scratch.register(t, df)
    return scratch.execute(PROFILE).df().set_index("check")["n"]


st.title("Supplier data: ERP migration readiness")
st.caption("Synthetic data. Raw tables are never modified; every raw row ends up in exactly one place.")

flow, quality, held, business = st.tabs(["Where every row went", "Quality: before vs after", "Quarantine & review", "Business view"])

with flow:
    n = {t: q(f"SELECT count(*) n FROM {t}").n[0] for t in TABLES}
    clean = {t: q(f"SELECT count(*) n FROM clean_{t}").n[0] for t in TABLES}
    quar = {t: q(f"SELECT count(*) n FROM quarantine_{t}").n[0] for t in ("purchase_orders", "invoices")}
    merged = n["vendors"] - clean["vendors"]
    outcomes = {"Loaded": [clean["vendors"], clean["purchase_orders"], clean["invoices"]],
                "Merged away": [merged, 0, 0],
                "Quarantined": [0, quar["purchase_orders"], quar["invoices"]]}
    labels = ["Vendors", "Purchase orders", "Invoices", *outcomes]
    src, dst, val = [], [], []
    for j, vals in enumerate(outcomes.values()):
        for i, v in enumerate(vals):
            if v:
                src.append(i)
                dst.append(3 + j)
                val.append(v)
    fig = go.Figure(go.Sankey(node=dict(label=labels, pad=20), link=dict(source=src, target=dst, value=val)))
    st.plotly_chart(fig, width="stretch")

    recon = pd.DataFrame({
        "raw": n,
        "loaded": clean,
        "merged away": {"vendors": merged, "purchase_orders": 0, "invoices": 0},
        "quarantined": {"vendors": 0, **quar},
    })
    recon["balanced"] = recon["raw"] == recon[["loaded", "merged away", "quarantined"]].sum(axis=1)
    st.subheader("Reconciliation")
    st.dataframe(recon, width="stretch")
    if not recon["balanced"].all():
        st.error("Row counts do not add up: a record vanished or was duplicated.")

with quality:
    before, after = profile(""), profile("clean_")
    cmp = pd.DataFrame({"before (raw)": before, "after (clean)": after})
    cmp["fixed"] = cmp["before (raw)"] - cmp["after (clean)"]
    st.dataframe(cmp, width="stretch")
    st.metric("Issues remaining", int(cmp["after (clean)"].sum()), delta=-int(cmp["fixed"].sum()), delta_color="inverse")
    st.caption("Same checks as sql/profile.sql, run on raw and on clean_* tables. Checks that stay above 0 have no rule yet or need a human.")

with held:
    st.subheader("Quarantine")
    for t in ("purchase_orders", "invoices"):
        df = q(f"SELECT * FROM quarantine_{t}")
        st.markdown(f"**{t}**: {len(df)} rows, {df['amount'].sum():,.2f} total amount (mixed currencies for POs)")
        if df.empty:
            st.info("Nothing quarantined yet: the quarantine rules are not built.")
        else:
            reason = st.multiselect(f"Reason ({t})", sorted(df.reason.unique()), default=sorted(df.reason.unique()))
            shown = df[df.reason.isin(reason)]
            st.dataframe(shown, width="stretch")
            st.download_button("Download CSV", shown.to_csv(index=False), f"quarantine_{t}.csv")
    st.subheader("Needs a human decision")
    review = q("SELECT * FROM review_items")
    st.dataframe(review, width="stretch")
    if not review.empty:
        st.download_button("Download CSV", review.to_csv(index=False), "review_items.csv")

with business:
    source = st.radio("Data", ["clean", "raw"], horizontal=True)
    p = "clean_" if source == "clean" else ""
    po = q(f"SELECT po_id, po_date::DATE po_date, currency, amount FROM {p}purchase_orders")
    inv = q(f"SELECT i.invoice_id, i.invoice_date::DATE invoice_date, i.paid, p.po_date::DATE po_date "
            f"FROM {p}invoices i LEFT JOIN {p}purchase_orders p USING (po_id)")
    # Edge months are partial (invoices trail their PO by up to 60 days), so the charts stop at the last complete month.
    monthly = pd.concat({
        "purchase orders": po.set_index(pd.to_datetime(po.po_date)).resample("MS").size(),
        "invoices": inv.set_index(pd.to_datetime(inv.invoice_date)).resample("MS").size(),
    }, axis=1).loc["2020-03":"2024-12"]
    st.plotly_chart(go.Figure([go.Scatter(x=monthly.index, y=monthly[c], name=c) for c in monthly]).update_layout(title="Volume per month"),
                    width="stretch")
    lag = (pd.to_datetime(inv.invoice_date) - pd.to_datetime(inv.po_date)).dt.days.dropna()
    c1, c2, c3 = st.columns(3)
    c1.metric("Median days PO → invoice", int(lag.median()))
    c2.metric("Invoices paid", f"{inv.paid.mean():.0%}")
    c3.metric("POs with an invoice", f"{po.po_id.isin(q(f'SELECT po_id FROM {p}invoices').po_id).mean():.0%}")
    st.plotly_chart(go.Figure(go.Histogram(x=lag, nbinsx=40)).update_layout(title="Days from PO to invoice"), width="stretch")
    st.caption("Amounts are in USD, CAD and MXN with no exchange rates, so this view counts records and never adds money across currencies.")
