"""
Carrier name normalization.

The two ports name the same real-world shipping companies differently --
Georgia's export tends to use short operational names (e.g. "MSC"),
Virginia's tends to use full legal names (e.g. "Mediterranean Shipping
Company S.A."), and both sources have some internal inconsistency too
(e.g. "MAERSK" vs "MAERSK INC" vs "MAERSK LINE").

Without this step, a carrier like Maersk gets split into multiple rows
in any groupby/count, understating its true volume and overstating the
number of distinct carriers serving each port.

Rules are substring-matched, case-insensitive, and ordered so more
specific patterns are checked first.
"""

import pandas as pd

CARRIER_RULES = [
    (["MAERSK"], "Maersk"),
    (["MSC", "MEDITERRANEAN SHIPPING"], "MSC"),
    (["CMA CGM", "CMA (AMERICA)", "CMA LINE"], "CMA CGM"),
    (["COSCO"], "COSCO"),
    (["EVERGREEN"], "Evergreen"),
    (["OCEAN NETWORK EXPRESS", "ONE -"], "ONE (Ocean Network Express)"),
    (["OOCL", "ORIENT OVERSEAS"], "OOCL"),
    (["WAN HAI"], "Wan Hai"),
    (["YANG MING"], "Yang Ming"),
    (["ZIM"], "ZIM"),
    (["JAMES RIVER BARGE"], "James River Barge"),
    (["HMM"], "HMM"),
    (["HAPAG"], "Hapag-Lloyd"),
]


def normalize_carrier(raw_name):
    if pd.isna(raw_name):
        return raw_name
    upper = str(raw_name).upper()
    for keywords, canonical in CARRIER_RULES:
        if any(kw in upper for kw in keywords):
            return canonical
    return str(raw_name).strip()


if __name__ == "__main__":
    df = pd.read_csv("../data/processed/combined_ports.csv")
    before_count = df["carrier"].nunique()

    df["carrier_clean"] = df["carrier"].apply(normalize_carrier)
    after_count = df["carrier_clean"].nunique()

    print(f"Unique carrier names before normalization: {before_count}")
    print(f"Unique carrier names after normalization:  {after_count}")
    print()
    print("Top carriers after normalization:")
    print(df["carrier_clean"].value_counts().head(12))

    df.to_csv("../data/processed/combined_ports_clean.csv", index=False)
    print()
    print("Saved to combined_ports_clean.csv")
