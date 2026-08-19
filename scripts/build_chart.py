"""
Build the carrier volume comparison chart from the cleaned, normalized data.
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def build_carrier_chart(df: pd.DataFrame, out_path: str, top_n: int = 8):
    top_carriers = df["carrier_clean"].value_counts().head(top_n).index
    subset = df[df["carrier_clean"].isin(top_carriers)]

    pivot = subset.groupby(["carrier_clean", "port"]).size().unstack(fill_value=0)
    pivot = pivot.loc[top_carriers]  # keep sorted by overall volume

    fig, ax = plt.subplots(figsize=(9, 5.5))
    pivot.plot(kind="barh", stacked=True, ax=ax, color=["#1f77b4", "#ff7f0e"])
    ax.set_xlabel("Number of vessel calls")
    ax.set_ylabel("")
    ax.set_title("Top Carriers by Port — Georgia vs. Virginia\n(after normalizing inconsistent carrier names)")
    ax.legend(title="Port")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    return pivot


if __name__ == "__main__":
    df = pd.read_csv("../data/processed/combined_ports_clean.csv")
    pivot = build_carrier_chart(df, "../output/carrier_volume_by_port.png")
    print("Chart saved to ../output/carrier_volume_by_port.png")
    print()
    print(pivot)
