"""
Standardize the cleaned Georgia dataset and the Virginia dataset into
one common schema so they can be merged and compared.

Important known limitation (see README): Georgia's export separates
estimated vs. actual arrival/departure times in the same row. Virginia's
export is a live snapshot with a single Arrival/Departure Time field
whose meaning depends on Phase -- an estimate if the vessel hasn't
arrived yet, an actual time once it has. That means schedule "delay"
(actual minus estimated) can be computed directly for Georgia, but not
for Virginia from this file alone.
"""

import pandas as pd
from load_georgia import load_georgia_csv


def combine_date_time(date_series, time_series):
    """Combine separate date and time string columns into one datetime column."""
    combined = (date_series.astype(str).str.strip() + " " + time_series.astype(str).str.strip())
    return pd.to_datetime(combined, format="%m/%d/%y %H:%M", errors="coerce")


def standardize_georgia(georgia: pd.DataFrame) -> pd.DataFrame:
    # Create the output frame with the same index as the source data FIRST.
    # (Assigning a scalar to a brand-new empty DataFrame locks in a 0-row
    # index, so every column added afterward silently fails to align --
    # that bug is exactly what produced an all-NaN "port" column below.)
    out = pd.DataFrame(index=georgia.index)
    out["port"] = "Georgia"
    out["terminal"] = georgia["terminal"]
    out["vessel_name"] = georgia["name"]
    out["carrier"] = georgia["vsl_operator"]
    out["berth"] = georgia["berth"]
    out["service"] = georgia["service"]
    out["inbound_voyage"] = georgia["in_voyage"]
    out["outbound_voyage"] = georgia["out_voyage"]

    out["estimated_arrival"] = combine_date_time(georgia["eta_date"], georgia["eta_time"])
    out["actual_arrival"] = combine_date_time(georgia["ata_date"], georgia["ata_time"])
    out["estimated_departure"] = combine_date_time(georgia["etd_date"], georgia["etd_time"])
    out["actual_departure"] = combine_date_time(georgia["atd_date"], georgia["atd_time"])

    out["status"] = georgia["status"]
    out["vessel_class"] = georgia["vessel_class"]
    return out


def standardize_virginia(va: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=va.index)
    out["port"] = "Virginia"
    out["terminal"] = va["Terminal"]
    out["vessel_name"] = va["Vessel"]
    out["carrier"] = va["Shipline Name"]
    out["berth"] = va["Berth"]
    out["service"] = va["Service"]
    out["inbound_voyage"] = va["I-B Voyage"]
    out["outbound_voyage"] = va["O-B Voyage"]

    arrival_dt = pd.to_datetime(va["Arrival Time"], format="%m/%d/%Y %H:%M", errors="coerce")
    departure_dt = pd.to_datetime(va["Departure Time"], format="%m/%d/%Y %H:%M", errors="coerce")

    # A vessel that hasn't arrived yet (Phase == Inbound) only has an estimate.
    # A vessel that has already arrived (Working/Departed) -- the single
    # Arrival Time field is treated as the actual time; the original
    # estimate isn't preserved in this export.
    already_arrived = va["Phase"].isin(["Working", "Departed"])

    out["estimated_arrival"] = arrival_dt.where(~already_arrived)
    out["actual_arrival"] = arrival_dt.where(already_arrived)

    already_departed = va["Phase"] == "Departed"
    out["estimated_departure"] = departure_dt.where(~already_departed)
    out["actual_departure"] = departure_dt.where(already_departed)

    out["status"] = va["Status"]
    out["vessel_class"] = None  # Virginia's export has no equivalent field
    return out


if __name__ == "__main__":
    gct = load_georgia_csv("../data/raw/Georgia_Garden_City_Vessel_Schedule.csv")
    ot = load_georgia_csv("../data/raw/Georgia_Ocean_Terminal_Vessels.csv")
    georgia = pd.concat([gct, ot], ignore_index=True, sort=False)

    va = pd.read_csv("../data/raw/Virginia_Vessel_Schedule.csv")

    georgia_std = standardize_georgia(georgia)
    va_std = standardize_virginia(va)

    combined = pd.concat([georgia_std, va_std], ignore_index=True)

    # Delay is only meaningful where we genuinely have both an estimate
    # and an actual time in the SAME record -- true for Georgia arrivals
    # that have already happened, not derivable for Virginia from this file.
    combined["arrival_delay_hours"] = (
        (combined["actual_arrival"] - combined["estimated_arrival"]).dt.total_seconds() / 3600
    )

    print("Combined standardized dataset shape:", combined.shape)
    print()
    print("Rows by port:")
    print(combined["port"].value_counts())
    print()
    print("Rows where arrival_delay_hours could be computed, by port:")
    print(combined.groupby("port")["arrival_delay_hours"].apply(lambda s: s.notna().sum()))
    print()
    print(combined.head(10))

    combined.to_csv("../data/processed/combined_ports.csv", index=False)
    print()
    print("Saved to combined_ports.csv")
