"""Interactive dashboard for ranked NSE opportunities."""

import json
from pathlib import Path
from typing import cast

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def _latest_report(root: Path) -> Path | None:
    """Return the most recently generated ranked Parquet report."""
    reports = sorted((root / "reports").glob("ranked_*.parquet"))
    return reports[-1] if reports else None


def _analysis(root: Path, symbol: str) -> dict[str, str]:
    """Load persisted trend and pattern analysis when it exists."""
    path = root / "processed" / "patterns" / f"{symbol.replace('^', 'index_')}.json"
    if not path.exists():
        return {}
    return cast(dict[str, str], json.loads(path.read_text())[0])


def run() -> None:
    """Render the AlphaScanner dashboard."""
    st.set_page_config(page_title="AlphaScanner", layout="wide")
    st.title("AlphaScanner")
    st.caption("Professional Quantitative Positional Trading Scanner for NSE")
    root = Path("data")
    report_path = _latest_report(root)
    if report_path is None:
        st.info("No ranked report exists. Generate a report before opening the dashboard.")
        return
    report = pd.read_parquet(report_path)
    search = st.sidebar.text_input("Search symbol", "")
    minimum_score = st.sidebar.slider("Minimum score", 0, 100, 0)
    selected = st.sidebar.multiselect(
        "Symbols", report["symbol"].tolist(), default=report["symbol"].tolist()
    )
    filtered = report[report["symbol"].isin(selected) & (report["score"] >= minimum_score)]
    if search:
        filtered = filtered[filtered["symbol"].str.contains(search.upper(), case=False, na=False)]
    analyses = {symbol: _analysis(root, symbol) for symbol in filtered["symbol"]}
    filtered = filtered.assign(
        trend=[analyses[symbol].get("trend", "unknown") for symbol in filtered["symbol"]],
        patterns=[analyses[symbol].get("signals", "") for symbol in filtered["symbol"]],
    )
    metrics = st.columns(3)
    metrics[0].metric("Opportunities", len(filtered))
    metrics[1].metric(
        "Average score", f"{filtered['score'].mean():.1f}" if not filtered.empty else "—"
    )
    metrics[2].metric("Top score", f"{filtered['score'].max():.1f}" if not filtered.empty else "—")
    st.dataframe(
        filtered.sort_values("score", ascending=False), use_container_width=True, hide_index=True
    )
    chart = go.Figure(go.Bar(x=filtered["symbol"], y=filtered["score"], marker_color="#2563eb"))
    chart.update_layout(
        title="Opportunity Scores", yaxis_range=[0, 100], xaxis_title="", yaxis_title="Score"
    )
    st.plotly_chart(chart, use_container_width=True)
    distribution = go.Figure(go.Histogram(x=filtered["score"], nbinsx=10, marker_color="#0f766e"))
    distribution.update_layout(title="Score Distribution", xaxis_title="Score", yaxis_title="Count")
    st.plotly_chart(distribution, use_container_width=True)
    if not filtered.empty:
        st.bar_chart(filtered["trend"].value_counts())
        st.bar_chart(filtered["patterns"].replace("", "none").value_counts())
    symbol = st.selectbox("Inspect symbol", filtered["symbol"].tolist())
    if symbol:
        path = root / "processed" / "indicators" / f"{symbol.replace('^', 'index_')}.parquet"
        if path.exists():
            indicators = pd.read_parquet(path)
            price_chart = go.Figure(
                go.Candlestick(
                    x=indicators.index,
                    open=indicators["open"],
                    high=indicators["high"],
                    low=indicators["low"],
                    close=indicators["close"],
                )
            )
            price_chart.add_scatter(x=indicators.index, y=indicators["sma_20"], name="SMA 20")
            price_chart.add_scatter(x=indicators.index, y=indicators["sma_50"], name="SMA 50")
            price_chart.add_hline(
                y=indicators["rolling_high_20"].iloc[-1],
                line_dash="dot",
                annotation_text="Resistance",
            )
            price_chart.add_hline(
                y=indicators["rolling_low_20"].iloc[-1], line_dash="dot", annotation_text="Support"
            )
            st.plotly_chart(price_chart, use_container_width=True)
            st.line_chart(indicators[["rsi_14", "macd", "macd_signal"]].tail(120))
            st.caption(f"Detected patterns: {_analysis(root, symbol).get('signals', 'none')}")


if __name__ == "__main__":
    run()
