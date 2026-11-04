"""Load and normalize Vietnamese token counts from FrequencyWords (D25/D26)."""

from __future__ import annotations

import pandas as pd

from common import RAW, STAGING, normalize_vietnamese, write_csv


def main() -> None:
    source = pd.read_csv(
        RAW / "frequencywords-vi" / "vi_50k.txt",
        sep=r"\s+",
        names=["token", "count"],
        encoding="utf-8",
        keep_default_na=False,
        dtype={"token": str, "count": str},
    )
    source["token"] = source["token"].map(normalize_vietnamese)
    source["count"] = pd.to_numeric(source["count"], errors="raise").astype("int64")
    source = source.loc[source["token"] != ""].copy()
    frame = (
        source.groupby("token", as_index=False, sort=False)["count"]
        .sum()
        .sort_values(["count", "token"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    frame["token_rank"] = frame["count"].rank(method="dense", ascending=False).astype(int)
    write_csv(frame, STAGING / "frequencywords.csv")
    print(f"frequencywords: {len(source):,} input rows -> {len(frame):,} normalized tokens")


if __name__ == "__main__":
    main()
