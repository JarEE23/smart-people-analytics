import pytest
import sqlite3
import os
from datetime import datetime, date
from config import Config
from models import init_db, insert_events_batch, get_db_connection
from services.analytics_service import AnalyticsService
from services.ai_service import AIService

@pytest.fixture(autouse=True)
def setup_test_database(monkeypatch, tmp_path):
    # Use temporary database for tests
    test_db_path = str(tmp_path / "test_analytics.db")
    monkeypatch.setattr(Config, "DATABASE_PATH", test_db_path)
    init_db()

    # Seed known deterministic test data
    # 2026-10-10:
    # 08:00 -> 10 IN, 2 OUT
    # 12:00 -> 25 IN, 15 OUT
    # 17:00 -> 5 IN, 20 OUT
    # Total IN = 40, Total OUT = 37, Net = +3
    #
    # 2026-10-11:
    # 09:00 -> 15 IN, 1 OUT
    # 12:00 -> 35 IN, 10 OUT (Peak hour 12:00 for IN is 35)
    # 18:00 -> 10 IN, 30 OUT
    # Total IN = 60, Total OUT = 41, Net = +19

    test_events = [
        # 2026-10-10 events
        {"occurred_at": "2026-10-10 08:15:00", "direction": "IN", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(10)
    ] + [
        {"occurred_at": "2026-10-10 08:30:00", "direction": "OUT", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(2)
    ] + [
        {"occurred_at": "2026-10-10 12:10:00", "direction": "IN", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(25)
    ] + [
        {"occurred_at": "2026-10-10 12:45:00", "direction": "OUT", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(15)
    ] + [
        {"occurred_at": "2026-10-10 17:15:00", "direction": "IN", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(5)
    ] + [
        {"occurred_at": "2026-10-10 17:50:00", "direction": "OUT", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(20)
    ] + [
        # 2026-10-11 events
        {"occurred_at": "2026-10-11 09:10:00", "direction": "IN", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(15)
    ] + [
        {"occurred_at": "2026-10-11 09:40:00", "direction": "OUT", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(1)
    ] + [
        {"occurred_at": "2026-10-11 12:15:00", "direction": "IN", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(35)
    ] + [
        {"occurred_at": "2026-10-11 12:40:00", "direction": "OUT", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(10)
    ] + [
        {"occurred_at": "2026-10-11 18:20:00", "direction": "IN", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(10)
    ] + [
        {"occurred_at": "2026-10-11 18:55:00", "direction": "OUT", "source": "SIMULATED", "camera_id": "CAM-01"} for _ in range(30)
    ]

    insert_events_batch(test_events)
    yield

def test_summary_calculation():
    """Menguji rekapitulasi numerik IN, OUT, dan Net Flow dari database"""
    summary = AnalyticsService.get_summary(start_date="2026-10-11", end_date="2026-10-11")
    assert summary["total_in"] == 60
    assert summary["total_out"] == 41
    assert summary["net_flow"] == 19
    assert summary["estimated_occupancy"] == 19
    assert summary["source"] == "SIMULATED"
    assert summary["has_data"] is True

def test_hourly_counts():
    """Menguji pembagian data per jam 00..23"""
    hourly = AnalyticsService.get_hourly_counts(date_str="2026-10-11")
    assert len(hourly["hours"]) == 24
    assert hourly["in_counts"][12] == 35  # Jam 12:00 ada 35 IN
    assert hourly["out_counts"][18] == 30 # Jam 18:00 ada 30 OUT
    assert hourly["total_in"] == 60
    assert hourly["total_out"] == 41

def test_peak_period():
    """Menguji pencarian periode paling ramai"""
    peak = AnalyticsService.get_peak_period(start_date="2026-10-11", end_date="2026-10-11", metric="IN")
    assert peak["peak_hour_start"] == 12
    assert peak["peak_hour"] == "12:00 - 12:59"
    assert peak["count"] == 35
    assert peak["has_data"] is True

def test_compare_periods_standard():
    """
    Menguji perhitungan persentase perubahan:
    N_lama (2026-10-10) = 40
    N_baru (2026-10-11) = 60
    Difference = +20
    Persen = ((60 - 40) / 40) * 100% = +50.0%
    """
    comp = AnalyticsService.compare_periods(
        period1_start="2026-10-10",
        period1_end="2026-10-10",
        period2_start="2026-10-11",
        period2_end="2026-10-11",
        metric="IN"
    )
    assert comp["period_previous"]["count"] == 40
    assert comp["period_current"]["count"] == 60
    assert comp["difference"] == 20
    assert comp["change_percent"] == 50.0
    assert "+50.00%" in comp["change_percent_str"]
    assert comp["trend"] == "NAIK"

def test_compare_periods_zero_division():
    """
    Menguji penanganan matematis khusus bila data pembanding bernilai nol
    """
    comp = AnalyticsService.compare_periods(
        period1_start="2026-01-01", # kosong (0)
        period1_end="2026-01-01",
        period2_start="2026-10-11", # 60
        period2_end="2026-10-11",
        metric="IN"
    )
    assert comp["period_previous"]["count"] == 0
    assert comp["period_current"]["count"] == 60
    assert comp["change_percent"] is None
    assert "Basis awal 0" in comp["change_percent_str"]

def test_ai_service_summary_question():
    """AI menjawab pertanyaan total orang masuk dengan angka yang diverifikasi"""
    res = AIService.ask("Berapa jumlah orang yang masuk pada tanggal 11 Oktober 2026?")
    assert "60 orang" in res["answer"]
    assert res["evidence"] is not None
    assert res["evidence"]["tool"] == "get_summary"
    assert res["evidence"]["result"]["total_in"] == 60

def test_ai_service_peak_question():
    """AI menjawab jam paling ramai berdasarkan pencarian jam puncak"""
    res = AIService.ask("Jam berapa paling ramai pada 11 Oktober 2026?")
    assert "12:00 - 12:59" in res["answer"]
    assert "35 orang" in res["answer"]
    assert res["evidence"]["tool"] == "get_peak_period"

def test_ai_service_compare_question():
    """AI menjawab perbandingan antarperiode dengan persentase benar"""
    res = AIService.ask("Bandingkan jumlah orang masuk pada 11 Oktober 2026 dengan kemarin.")
    assert "40 orang" in res["answer"]
    assert "60 orang" in res["answer"]
    assert "+50.00%" in res["answer"]

def test_ai_service_empty_date():
    """AI menangani tanggal kosong secara jujur tanpa mengarang"""
    res = AIService.ask("Berapa orang masuk tanggal 1 Januari 2020?")
    assert "tidak ditemukan catatan" in res["answer"].lower() or "belum ada catatan" in res["answer"].lower()

def test_ai_service_out_of_scope():
    """AI menolak pertanyaan di luar topik people analytics"""
    res = AIService.ask("Bagaimana resep membuat rendang padang?")
    assert "hanya dapat membantu" in res["answer"].lower() or "dibatasi" in res["answer"].lower()
