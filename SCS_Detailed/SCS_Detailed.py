import datetime
import pathlib
import zoneinfo
from collections.abc import Iterable
from datetime import tzinfo
from pathlib import Path
from typing import Final, final

import ibis
from ibis import Table
from ibis.backends import BaseBackend
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

    CM: Final[frozenset[str]] = frozenset(
        [
            "CASE MANAGEMENT",
            "CASE MANAGEMENT COLLATERAL",
            "CASE MANAGEMENT COLLATERAL, PSR INDIVIDUAL",
            "CASE MANAGEMENT, CASE MANAGEMENT COLLATERAL",
            "CASE MANAGEMENT, PSR INDIVIDUAL",
            "CTP JAIL",
            "PSR INDIVIDUAL",
        ]
    )
    SE: Final[frozenset[str]] = frozenset(
        [
            "SE JOB DEVELOPMENT",
            "SE JOB DEVELOPMENT, SE JOB PLACEMENT",
            "SE JOB PLACEMENT",
        ]
    )
    RES: Final[frozenset[str]] = frozenset(
        ["INDEPENDENT RESIDENTIAL SERVICE", "RESIDENTIAL NON-BILLABLE"]
    )

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


def initialize_ibis() -> BaseBackend:
    ibis.options.interactive = True
    ibis.options.verbose = False
    return ibis.duckdb.connect()


def ingest_latest_input_file(con: BaseBackend) -> Table:
    most_recent_file: Path = max(
        (f for f in CONST.INPUT_DIR.iterdir() if f.is_file()),
        key=lambda x: x.stat().st_mtime_ns,
    )
    table: Table = con.read_csv(most_recent_file, encoding="utf-16", ignore_errors=True)
    table = table.drop(
        "Patient Primary Carrier Name", "Patient Status Description"
    ).rename(
        cid="Patient Chart Number",
        name="Patient Name (Last, First)",
        app="Appointment Type",
        date="Appointment Start Date",
    )
    return table


def get_appointment_types(table: Table) -> Iterable[str]:
    return (
        table.drop("cid", "name", "date")
        .distinct()
        .order_by("app")
        .to_pyarrow()
        .to_pydict()["app"]
    )


def split_old(table: Table) -> tuple[Table, Table]:
    old = table.filter(table["date"] > (ibis.now() - ibis.interval(years=1)))
    return (old, table.difference(old))


def split_department(cm_se_res_out, CONST.CM) -> tuple[Table, Table]: pass



def main() -> None:
    con: BaseBackend = initialize_ibis()
    table: Table = ingest_latest_input_file(con)
    print(table)
    # Use to get types manually to add to CONST CM SE RES
    # app_types: Iterable[str] = get_appointment_types(table)
    # print(app_types)
    (old, cm_se_res_out) = split_old(table)
    print(cm_se_res_out)
    print(old)
    (cm, se_res_out) = split_department(cm_se_res_out, CONST.CM)
    # (se, res_out) = split_department(se_res_out)
    # (res, out) = split_department(res_out)


if __name__ == "__main__":
    main()
