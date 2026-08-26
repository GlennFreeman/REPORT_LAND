from re import S
import datetime
import pathlib
import zoneinfo
from collections.abc import Iterable
from datetime import tzinfo
from pathlib import Path
from typing import Final, cast, final

import ibis
import xlsxwriter
from ibis import Table
from ibis.backends import BaseBackend
from msgspec import Struct
from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet


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

    DEPARTMENT_SHORT_NAMES: Iterable[str] = ("CM", "SE", "RES", "OUT", "OLD")
    DEPARTMENT_FULL_NAMES: Iterable[str] = (
        "Case Mangement",
        "Supportive Employement",
        "Residential",
        "Outpatient",
        "Older than 12 Months",
    )

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
    old: Table = table.filter(table["date"] > (ibis.now() - ibis.interval(years=1)))
    return (old, table.difference(old))


def split_department(table: Table, items: frozenset[str]) -> tuple[Table, Table]:
    department: Table = table.filter(table.app.isin(items))
    return (department, table.difference(department))


def deduplicate_clients(table: Table, *filter_tables: Table) -> Table:
    for ft in filter_tables:
        table = table.filter(table.name.notin(ft.name))
    return table.drop("app", "date").distinct()


def make_summary_page(wb: Workbook, departments: Iterable[Table]) -> None:
    summary: Worksheet = wb.add_worksheet("Summary")
    summary.set_page_view(view=1)
    summary.center_horizontally()
    summary.set_default_row(hide_unused_rows=True)

    time: str = f"Generated at: {datetime.datetime.now(CONST.TIMEZONE).strftime('%Y/%m/%d %H:%M')}"
    title: str = "State Contracted Services Detailed Report"
    company: str = "ONE Community Health Solution"
    summary.set_header(f"&L{time}&C{title}&R{company}")

    percent_format: Format = wb.add_format({"num_format": "0.00%"})
    title_format: Format = wb.add_format(
        {"bold": True, "align": "center", "valign": "center"}
    )

    summary.merge_range("A1:C1", "SCS - Summary", title_format)

    data: list[tuple[str, int, float]] = []
    total: int = 0
    for department in departments:
        total += department.count().execute()

    for i, department in enumerate(departments):
        data.append(
            (
                list(CONST.DEPARTMENT_FULL_NAMES)[i],
                num := cast(int, department.count().execute()),
                num / total,
            )
        )

    summary.add_table(
        1,
        0,
        len(data) + 2,  # +1 for offset, +2 for header and total
        len(data[0]) - 1,
        {
            "data": data,
            "name": "Summary",
            "first_column": True,
            "total_row": True,
            "style": "Table Style Medium 5",
            "columns": [
                {"header": "Department", "total_string": "Totals:"},
                {"header": "Count", "total_function": "sum"},
                {
                    "header": "Percentage",
                    "total_function": "sum",
                    "format": percent_format,
                },
            ],
        },
    )

    summary.set_column("D:XFD", None, None, {"hidden": True})
    summary.autofit()


def make_department_pages(wb: Workbook, departments: Iterable[Table]) -> None:
    pass


def excelize_tables(*tables) -> None:
    wb: Workbook = xlsxwriter.Workbook(
        CONST.OUTPUT_DIR / (CONST.FILE_NAME + CONST.START_TIME + ".xlsx")
    )
    make_summary_page(wb, tables)
    make_department_pages(wb, tables)
    wb.close()


def main() -> None:
    con: BaseBackend = initialize_ibis()
    table: Table = ingest_latest_input_file(con)

    # Use to get types manually to add to CONST CM SE RES
    # app_types: Iterable[str] = get_appointment_types(table)
    # print(app_types)

    (old, cm_se_res_out) = split_old(table)
    (cm, se_res_out) = split_department(cm_se_res_out, CONST.CM)
    (se, res_out) = split_department(se_res_out, CONST.SE)
    (res, out) = split_department(res_out, CONST.RES)

    cm = deduplicate_clients(cm)
    se = deduplicate_clients(se, cm)
    res = deduplicate_clients(res, cm, se)
    out = deduplicate_clients(out, cm, se, res)
    old = deduplicate_clients(old, cm, se, res, out)

    excelize_tables(cm, se, res, out, old)


if __name__ == "__main__":
    main()
