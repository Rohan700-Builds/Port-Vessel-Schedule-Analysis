"""
Georgia Ports (Garden City + Ocean Terminal) CSV loader.

Both source files have a real data quality issue: certain text fields
contain unquoted commas, which breaks naive CSV parsing because the
parser can't tell those commas apart from real column separators.

Two known causes, found by inspecting mismatched rows:
  1. vessel_class sometimes lists multiple crane classes, e.g. "A, B, C"
  2. vsl_operator (and some carrier names) sometimes include a corporate
     suffix like ", INC" or ", LLC" that wasn't quoted in the source

Fix strategy:
  Step 1 - Pre-process the raw text: remove commas that appear directly
           before a known corporate suffix (INC, LLC, CO, CORP, S.A., etc.)
           since these are never real column delimiters.
  Step 2 - Parse with the csv module. For any row that's still longer
           than expected, assume the excess came from vessel_class
           (the only remaining known source) and re-merge those fields.
  Step 3 - Verify: raise an error if any row still doesn't match the
           expected column count, rather than silently loading bad data.
"""

import csv
import re
import pandas as pd

SUFFIX_PATTERN = re.compile(
    r",\s*(INC|LLC|LTD|CO|CORP|S\.A\.|AGENCY|LIMITED)\b(?=[,\r\n])",
    re.IGNORECASE,
)


def _strip_corporate_suffix_commas(raw_text: str) -> str:
    """Remove the comma right before a corporate suffix like ', INC'."""
    return SUFFIX_PATTERN.sub(lambda m: " " + m.group(1), raw_text)


def load_georgia_csv(path: str) -> pd.DataFrame:
    with open(path, encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_text = _strip_corporate_suffix_commas(raw_text)

    reader = csv.reader(cleaned_text.splitlines())
    rows = list(reader)
    header = rows[0]
    expected_len = len(header)
    vc_idx = header.index("vessel_class")

    fixed_rows = []
    still_bad = []
    for line_num, r in enumerate(rows[1:], start=2):
        extra = len(r) - expected_len
        if extra > 0:
            merged_class = ", ".join(x.strip() for x in r[vc_idx:vc_idx + extra + 1])
            r = r[:vc_idx] + [merged_class] + r[vc_idx + extra + 1:]
        if len(r) != expected_len:
            still_bad.append((line_num, len(r)))
            continue
        fixed_rows.append(r)

    if still_bad:
        raise ValueError(
            f"{len(still_bad)} rows in {path} still don't match the expected "
            f"{expected_len} columns after cleaning: {still_bad[:5]} ..."
        )

    df = pd.DataFrame(fixed_rows, columns=header)
    return df


if __name__ == "__main__":
    gct = load_georgia_csv("../data/raw/Georgia_Garden_City_Vessel_Schedule.csv")
    ot = load_georgia_csv("../data/raw/Georgia_Ocean_Terminal_Vessels.csv")

    print("Garden City:", gct.shape)
    print("Ocean Terminal:", ot.shape)
    print()
    print("vessel_class values now (Garden City):")
    print(gct["vessel_class"].value_counts())
    print()
    print("vsl_operator values containing INC/LLC now parse cleanly, e.g.:")
    print(gct[gct["vsl_operator"].str.contains("INC|LLC", case=False, na=False)]["vsl_operator"].unique())
