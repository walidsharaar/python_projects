"""
Source simulators: the test data must be realistic, contain exactly the planned problems
and be identical on every run. No database: Company A is built in memory.
"""
import random
from collections import Counter
from datetime import date

import pandas as pd
import pytest
from faker import Faker

from generator import company_a_b1 as a
from generator import company_b_csv as b
from generator import sustainability_excel as x
from generator.common import HISTORY_START, REFERENCE_DATE, market, price_factor, weighted_dates


# ---------------------------------------------------------------- common
def test_market_is_identical_on_every_call():
    assert market() == market()
    assert len(market()) == 280


def test_market_does_not_touch_the_global_random_state():
    random.seed(1)
    expected = random.random()
    random.seed(1)
    market()
    assert random.random() == expected


@pytest.mark.parametrize("d, factor", [(date(2023, 6, 1), 1.0), (date(2024, 1, 1), 1.03),
                                       (date(2026, 12, 31), 1.03 ** 3), (date(2022, 12, 1), 1 / 1.03)])
def test_price_factor(d, factor):
    assert price_factor(d) == pytest.approx(factor)


def test_weighted_dates_within_history_and_sorted():
    random.seed(1)
    dates = weighted_dates(3000, [1.0] * 12, 0.0)
    assert dates == sorted(dates)
    assert HISTORY_START <= dates[0] and dates[-1] <= REFERENCE_DATE


def test_weighted_dates_few_on_weekends():
    random.seed(1)
    dates = weighted_dates(5000, [1.0] * 12, 0.0)
    assert sum(d.weekday() >= 5 for d in dates) / len(dates) < 0.06


def test_weighted_dates_follow_the_season():
    random.seed(1)
    season = [1.0] * 12
    season[7] = 5.0                                      # August
    months = Counter(d.month for d in weighted_dates(5000, season, 0.0))
    assert months.most_common(1)[0][0] == 8


def test_weighted_dates_grow_over_time():
    random.seed(1)
    years = Counter(d.year for d in weighted_dates(8000, [1.0] * 12, 0.30))
    assert years[2023] < years[2024] < years[2025]


# ---------------------------------------------------------------- Company A (SAP B1)
@pytest.fixture(scope="module")
def sap():
    """Build Company A exactly as main() does, without writing to a database."""
    Faker.seed(a.SEED)
    random.seed(a.SEED)
    customers = a.make_customers()
    customers = pd.concat([customers, a.make_special_customers(customers)], ignore_index=True)
    items = a.make_items()
    ordr, rdr1 = a.make_orders(customers, items, a.N_ORDERS)
    oinv, inv1 = a.make_invoices(ordr, rdr1, items)
    return {"ocrd": customers, "oitm": items, "ordr": ordr, "rdr1": rdr1, "oinv": oinv, "inv1": inv1}


def test_sap_is_reproducible(sap):
    Faker.seed(a.SEED)
    random.seed(a.SEED)
    again = a.make_customers()
    pd.testing.assert_frame_equal(again, sap["ocrd"].iloc[:len(again)])


def test_sap_row_counts(sap):
    assert len(sap["ocrd"]) == 203                     # 200 + 2 group companies + 1 duplicate
    assert len(sap["oitm"]) == 45
    assert len(sap["ordr"]) == 3600


def test_sap_keys_are_unique(sap):
    assert sap["ocrd"]["cardcode"].is_unique
    assert sap["oitm"]["itemcode"].is_unique
    assert not sap["rdr1"].duplicated(["docentry", "linenum"]).any()
    assert not sap["inv1"].duplicated(["docentry", "linenum"]).any()


def test_sap_lines_numbered_from_zero(sap):
    first = sap["rdr1"].groupby("docentry")["linenum"].agg(["min", "max", "count"])
    assert (first["min"] == 0).all() and (first["max"] == first["count"] - 1).all()


def test_sap_header_total_equals_lines(sap):
    lines = sap["rdr1"].groupby("docentry")["linetotal"].sum().round(2)
    totals = sap["ordr"].set_index("docentry")["doctotal"]
    assert (abs(totals - lines) < 0.01).all()


def test_sap_planned_problem_missing_and_duplicate_ean(sap):
    ean = sap["oitm"]["codebars"]
    assert ean.isna().sum() == 4                       # 8 % of 45
    assert ean.dropna().duplicated().sum() == 1        # exactly one EAN used twice


def test_sap_planned_problem_unknown_customer(sap):
    unknown = (sap["ordr"]["cardcode"] == "C99999").mean()
    assert 0.003 < unknown < 0.02
    assert "C99999" not in set(sap["ocrd"]["cardcode"])


def test_sap_planned_problem_duplicate_customer(sap):
    names = sap["ocrd"].set_index("cardcode")["cardname"]
    assert names["C10999"] == names["C10001"].upper()


def test_sap_dates_inside_history(sap):
    assert sap["ordr"]["docdate"].min() >= HISTORY_START
    assert sap["ordr"]["docdate"].max() <= REFERENCE_DATE
    open_orders = sap["ordr"][sap["ordr"]["docstatus"] == "O"]
    assert (open_orders["docduedate"] > REFERENCE_DATE).all()


def test_sap_lost_customer_stops_after_march_2026(sap):
    lost = sap["ordr"][sap["ordr"]["cardcode"] == a.LOST]
    assert len(lost) > 20 and lost["docdate"].max() <= a.LOST_AFTER


def test_sap_grower_buys_more_in_2026(sap):
    grower = sap["ordr"][sap["ordr"]["cardcode"] == a.GROWER]
    per_year = Counter(d.year for d in grower["docdate"])
    assert per_year[2026] > 2 * per_year[2025]


def test_sap_prices_rise_every_year(sap):
    lines = sap["rdr1"].merge(sap["ordr"][["docentry", "docdate"]], on="docentry")
    lines["year"] = [d.year for d in lines["docdate"]]
    avg = lines.groupby(["itemcode", "year"])["price"].mean().unstack()
    assert (avg[2026] > avg[2023]).mean() > 0.9


def test_sap_invoices_only_for_delivered_orders(sap):
    ordr = sap["ordr"].set_index("docentry")
    base = ordr.loc[sap["inv1"]["baseentry"].unique()]
    assert (base["canceled"] == "N").all()
    assert (base["docduedate"] <= REFERENCE_DATE).all()


def test_sap_invoice_lines_point_to_order_lines(sap):
    keys = set(zip(sap["rdr1"]["docentry"], sap["rdr1"]["linenum"], strict=True))
    links = set(zip(sap["inv1"]["baseentry"], sap["inv1"]["baseline"], strict=True))
    assert links <= keys
    assert (sap["inv1"]["basetype"] == 17).all()


def test_sap_never_delivers_more_than_ordered(sap):
    merged = sap["inv1"].merge(sap["rdr1"], left_on=["baseentry", "baseline"],
                               right_on=["docentry", "linenum"], suffixes=("", "_order"))
    assert (merged["quantity"] <= merged["quantity_order"]).all()


def test_sap_supply_problem_aug_sep_2025(sap):
    merged = sap["inv1"].merge(sap["rdr1"], left_on=["baseentry", "baseline"],
                               right_on=["docentry", "linenum"], suffixes=("", "_order"))
    merged = merged.merge(sap["ordr"][["docentry", "docduedate"]], left_on="baseentry", right_on="docentry")
    in_window = merged["docduedate"].between(*a.SUPPLY_PROBLEM)
    partial = merged["quantity"] < merged["quantity_order"]
    assert partial[in_window].mean() > 3 * partial[~in_window].mean()


# ---------------------------------------------------------------- Company B (CSV export)
@pytest.fixture(scope="module")
def erp_b():
    Faker.seed(b.SEED)
    random.seed(b.SEED)
    customers = b.make_customers()
    items = b.make_items()
    return {"kunden": customers, "artikel": items, "verkaeufe": b.make_sales(customers, items)}


@pytest.mark.parametrize("draw, expected", [(0.1, "MÜLLER & CO"), (0.4, "Müller und Co"),
                                            (0.6, "Müller & Co "), (0.9, "Müller & Co")])
def test_vary_name(monkeypatch, draw, expected):
    monkeypatch.setattr(b.random, "random", lambda: draw)
    assert b.vary_name("Müller & Co") == expected


def test_b_customers(erp_b):
    k = erp_b["kunden"]
    assert len(k) == 141 and k["Kundennr"].is_unique
    assert k["Kundennr"].iloc[0] == "K-4001"
    assert "Nordwerk Haushalt GmbH" in set(k["Kundenname"])        # intercompany customer


def test_b_planned_postcode_typo(erp_b):
    typo = erp_b["kunden"].set_index("Kundennr").loc["K-4011", "PLZ"]
    real = market()[150]["zipcode"]
    assert typo != real and sorted(typo) == sorted(real)


def test_b_units_differ_from_a(erp_b):
    assert set(erp_b["artikel"]["Einheit"]) <= {"Rolle", "Karton", "Palette"}


def test_b_credit_notes_are_negative(erp_b):
    v = erp_b["verkaeufe"]
    gs = v[v["Belegart"] == "GS"]
    assert len(gs) > 0 and (gs["Menge"] < 0).all() and (gs["Nettobetrag"] < 0).all()


def test_b_line_amount_is_quantity_times_price(erp_b):
    v = erp_b["verkaeufe"]
    assert (abs(v["Menge"] * v["Einzelpreis"] - v["Nettobetrag"]) < 0.01).all()


def test_b_planned_duplicate_rows(erp_b):
    assert erp_b["verkaeufe"].duplicated().sum() == 45


def test_b_csv_is_written_like_a_german_erp(erp_b, tmp_path, monkeypatch):
    monkeypatch.setattr(b, "OUTPUT_DIR", tmp_path)
    b.write_csv(erp_b["verkaeufe"].head(5), "verkaeufe.csv")
    b.write_csv(erp_b["artikel"], "artikel.csv")
    sales = (tmp_path / "verkaeufe.csv").read_bytes().decode("cp1252").splitlines()
    assert sales[0].startswith("Belegnr;Belegart;Belegdatum")
    date_field = sales[1].split(";")[2]
    assert len(date_field) == 10 and date_field[2] == "." and date_field[5] == "."
    assert "," in sales[1].split(";")[-1]                                # decimal comma
    assert "_listenpreis" not in (tmp_path / "artikel.csv").read_text(encoding="cp1252")


# ---------------------------------------------------------------- Excel (sustainability)
ITEMS = pd.DataFrame({
    "firma": ["Nordwerk Haushalt GmbH"] * 3 + ["Nordwerk Beutel GmbH"] * 2,
    "artikelnr": ["A00001", "A00002", "A00003", "MB-0001", "MB-0009"],
    "bezeichnung": ["Allzweckreiniger 1 l", "Spülmittel", "Alufolie", "Müllbeutel Standard 10 l",
                    "Müllbeutel Recycling 60 l"],
})


@pytest.fixture()
def sheet():
    random.seed(x.SEED)
    return x.make_sheet(ITEMS)


def test_sheet_has_history_and_unknown_item(sheet):
    assert len(sheet) == len(ITEMS) + 3 + 1
    assert (sheet["Gültig ab"] == date(2026, 1, 1)).sum() == 3
    assert "A09999" in set(sheet["Artikelnr"])


def test_sheet_has_percentages_as_text(sheet):
    assert sheet["Rezyklatanteil"].map(lambda v: isinstance(v, str) and v.endswith(" %")).any()


@pytest.mark.parametrize("name, low, high", [("Müllbeutel Recycling 60 l", 60, 85),
                                             ("Müllbeutel Standard", 10, 40), ("Spülmittel", 0, 35)])
def test_recycled_share_ranges(name, low, high):
    random.seed(3)
    assert all(low <= x.recycled_share(name) <= high for _ in range(50))


def test_excel_has_title_rows(sheet, tmp_path, monkeypatch):
    monkeypatch.setattr(x, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(x, "OUTPUT_FILE", tmp_path / "r.xlsx")
    x.write_excel(sheet)
    raw = pd.read_excel(tmp_path / "r.xlsx", header=None)
    assert raw.iloc[0, 0].startswith("Rezyklatanteile")
    assert "20.11.2026" in raw.iloc[1, 0]
    table = pd.read_excel(tmp_path / "r.xlsx", header=3)
    assert list(table.columns[:4]) == ["Firma", "Artikelnr", "Bezeichnung", "Rezyklatanteil"]
