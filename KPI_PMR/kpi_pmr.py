import datetime
import pathlib
import zoneinfo
from collections.abc import Iterable
from datetime import tzinfo
from pathlib import Path
from typing import Final, cast, final

import ibis
from ibis.backends import BaseBackend
from ibis.expr.api import Table
from msgspec import Struct


@final
class _Constants(Struct, frozen=True, kw_only=True):
    FILE_NAME: Final[str] = pathlib.Path(__file__).name
    DIRECTORY: Final[Path] = pathlib.Path(__file__).parent
    TIMEZONE: Final[tzinfo] = (
        datetime.datetime.now().astimezone().tzinfo
        or zoneinfo.ZoneInfo("America/New_York")
    )
    START_TIME: Final[str] = datetime.datetime.now(TIMEZONE).strftime(
        "📆 %Y／%m／%d ⋯ ⏰ %H：%M：%S"
    )
    LOG_FILE: Final[Path] = DIRECTORY / "_0_LOGS" / f"🗐{START_TIME}.log"
    INPUT_DIR: Final[Path] = DIRECTORY / "_1_INPUTS"
    OUTPUT_DIR: Final[Path] = DIRECTORY / "_2_OUTPUTS"

    KPI1_1: Final[Iterable[str]] = ("ADULT BHA", "SERVICE PLAN DEVELOPMENT")

    @final
    def __post_init__(self):
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @final
    def __repr__(self) -> str:
        return f"<_Constants file='{self.FILE_NAME}' start='{self.START_TIME}'>"

    @final
    def __str__(self) -> str:
        return self.__repr__()


CONST: Final[_Constants] = _Constants()


def most_recent_file(dir: Path, stem: str | Path | None = None) -> Path:
    match stem:
        case str():
            return max(
                dir.glob(f"*{stem}*"),
                key=lambda x: x.stat().st_mtime_ns,
            )
        case Path():
            return max(
                dir.glob(f"*{stem.stem}*"),
                key=lambda x: x.stat().st_mtime_ns,
            )
        case _:
            return max(
                (f for f in dir.iterdir() if f.is_file()),
                key=lambda x: x.stat().st_mtime_ns,
            )


def initialize_ibis() -> BaseBackend:
    ibis.options.interactive = True
    ibis.options.verbose = False
    return ibis.duckdb.connect()


def ingest_poe(con: BaseBackend, file: Path) -> Table:
    t: Table = (
        con.read_csv(file, ignore_errors=True)
        .drop("textbox11", "txtHeaderr0c0", "textbox13")
        .rename(name="txtHeaderr0c1", intake_date="textbox14")
    )
    t = t.mutate(name=t.name.replace("Patient Name: ", ""))
    t = t.filter(~t.name.upper().contains("TEST")).order_by("intake_date")

    return t


def ingest_visits(con: BaseBackend, file) -> Table:
    t: Table = (
        con.read_csv(file, encoding="utf-16", ignore_errors=True)
        .drop("Appointment Status", "Appointment Reason", "Visit Number")
        .rename(
            name="Patient Name (Last, First)",
            app_date="Appointment Start Date",
            app_type="Appointment Type",
        )
        .order_by("app_date")
    )

    return t


def join_poe_vists(table1: Table, table2: Table) -> Table:

    left = table1.mutate(join_name=table1.name.upper().replace(" ", ""))

    right = table2.mutate(join_name=table2.name.upper().replace(" ", ""))

    t: Table = (
        left.left_join(right, left.join_name == right.join_name)
        .select(table1.name, table1.intake_date, table2.app_date, table2.app_type)
        .order_by("app_date", "intake_date")
    )

    return t


def filter_combined_kpi1_1(table: Table) -> Table:
    table = table.filter(table.app_date >= table.intake_date).filter(
        table.app_type.isin(CONST.KPI1_1)
    )
    table = table.order_by(table.intake_date).filter(
        (table.intake_date + ibis.interval(days=7)) >= table.app_date
    )

    return table


def main() -> None:
    con: BaseBackend = initialize_ibis()
    point_of_entry: Table = ingest_poe(
        con, most_recent_file(CONST.INPUT_DIR, "PCD-Initial")
    )
    patient_visits: Table = ingest_visits(
        con, most_recent_file(CONST.INPUT_DIR, "KPI-Patient-Visits")
    )
    print(point_of_entry.count())
    print(patient_visits.count())
    combined: Table = join_poe_vists(point_of_entry, patient_visits)
    print(combined.count())
    total: int = cast(int, combined.distinct(on=combined.name).count().execute())
    print(total)
    kpi1_1: Table = filter_combined_kpi1_1(combined)
    print(kpi1_1.count())
    print(kpi1_1)
    kpi1_1.to_csv(CONST.OUTPUT_DIR / f"{CONST.START_TIME}.tsv", sep="\t")


if __name__ == "__main__":
    main()
