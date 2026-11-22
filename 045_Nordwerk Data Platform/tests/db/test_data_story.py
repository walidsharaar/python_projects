"""
The data story of the report, checked against the warehouse.
If one of these fails, a sentence in the presentation would be wrong.
"""
import pytest

from tests.conftest import scalar

GROUP = "NOT ist_intercompany"


def revenue(db, where):
    return float(scalar(db, f"SELECT SUM(umsatz_netto) FROM gold.fact_verkauf WHERE {GROUP} AND {where}"))


def margin(db, year):
    return float(scalar(db, f"SELECT SUM(deckungsbeitrag) / SUM(umsatz_netto) FROM gold.fact_verkauf "
                            f"WHERE {GROUP} AND EXTRACT(YEAR FROM datum) = {year}"))


@pytest.mark.parametrize("year, million", [(2023, 3.46), (2024, 4.23), (2025, 4.68)])
def test_group_revenue_per_year(db, year, million):
    assert revenue(db, f"EXTRACT(YEAR FROM datum) = {year}") / 1e6 == pytest.approx(million, abs=0.005)


def test_growth_year_to_date(db):
    ytd = "TO_CHAR(datum, 'MMDD') <= '1120' AND EXTRACT(YEAR FROM datum) = "
    growth = revenue(db, ytd + "2026") / revenue(db, ytd + "2025") - 1
    assert growth == pytest.approx(0.120, abs=0.001)


def test_margin_rises_every_year(db):
    m = [margin(db, y) for y in (2023, 2024, 2025, 2026)]
    assert m == sorted(m)
    assert (round(m[0], 3), round(m[-1], 3)) == (0.309, 0.365)


def test_seasonality_company_a_spring_company_b_summer(db):
    def peak(firma):
        return scalar(db, f"SELECT EXTRACT(MONTH FROM datum) FROM gold.fact_verkauf "
                          f"WHERE firma_id = '{firma}' AND datum BETWEEN '2023-01-01' AND '2025-12-31' "
                          f"GROUP BY 1 ORDER BY SUM(umsatz_netto) DESC LIMIT 1")
    assert peak("A") in (3, 4, 12)
    assert peak("B") == 8


def delivery_rate(db, where):
    return float(scalar(db, "SELECT SUM(menge_geliefert_stueck) / SUM(menge_bestellt_stueck) "
                            f"FROM gold.fact_lieferung WHERE ist_faellig AND NOT ist_storniert AND {where}"))


def test_delivery_problem_aug_sep_2025(db):
    assert delivery_rate(db, "datum BETWEEN '2025-08-01' AND '2025-09-30'") == pytest.approx(0.905, abs=0.001)
    assert delivery_rate(db, "datum >= '2026-01-01'") == pytest.approx(0.988, abs=0.001)


def test_customers_of_both_companies(db):
    share = float(scalar(db, f"SELECT SUM(umsatz_netto) FILTER (WHERE k.anzahl_firmen >= 2) / SUM(umsatz_netto) "
                             f"FROM gold.fact_verkauf f JOIN gold.dim_kunde k USING (kunde_sk) "
                             f"WHERE {GROUP} AND f.datum >= '2026-01-01'"))
    assert share == pytest.approx(0.334, abs=0.001)
    assert scalar(db, "SELECT COUNT(*) FROM gold.dim_kunde WHERE anzahl_firmen >= 2") == 60


def test_lost_customer_no_orders_after_march(db):
    last_order = scalar(db, "SELECT MAX(docdate::date) FROM bronze.sap_b1_ordr WHERE cardcode = 'C10012'")
    assert str(last_order) <= "2026-03-31"
    orders_2025 = scalar(db, "SELECT COUNT(*) FROM bronze.sap_b1_ordr WHERE cardcode = 'C10012' AND docdate LIKE '2025%'")
    assert orders_2025 > 5                     # it was a regular customer before


def test_revenue_without_customer(db):
    assert float(scalar(db, "SELECT SUM(umsatz_netto) FROM gold.fact_verkauf WHERE kunde_sk = -1")) == \
        pytest.approx(60256, abs=1)
