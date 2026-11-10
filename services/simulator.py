import random
from datetime import datetime, timedelta, date
from models import insert_events_batch, get_db_connection

def generate_simulated_dataset(days=14, target_end_date=None, clear_existing=False):
    """
    Menghasilkan data simulasi kejadian orang masuk dan keluar selama N hari.
    Mengikuti kurva aktivitas harian realistis (gedung kampus/perkantoran).
    """
    if clear_existing:
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM count_events WHERE source = 'SIMULATED'")
            conn.commit()
        finally:
            conn.close()

    if target_end_date is None:
        target_end_date = datetime.now().date()
    elif isinstance(target_end_date, str):
        target_end_date = datetime.strptime(target_end_date, '%Y-%m-%d').date()

    start_date = target_end_date - timedelta(days=days - 1)
    
    # Probabilitas relatif per jam (0..23) untuk IN dan OUT
    # Pola: Pagi banyak masuk, Siang makan siang (keluar lalu masuk), Sore pulang (banyak keluar)
    HOURLY_WEIGHTS = {
        0: (0.1, 0.1),
        1: (0.0, 0.0),
        2: (0.0, 0.0),
        3: (0.0, 0.0),
        4: (0.1, 0.0),
        5: (0.3, 0.1),
        6: (1.5, 0.3),
        7: (7.0, 1.0),   # Masuk pagi
        8: (10.0, 1.5),  # Peak masuk pagi
        9: (8.0, 2.5),
        10: (5.0, 3.5),
        11: (4.0, 7.0),  # Mulai istirahat siang
        12: (7.5, 9.0),  # Peak siang (keluar makan lalu masuk kembali)
        13: (9.0, 5.0),  # Kembali dari makan siang
        14: (5.5, 4.0),
        15: (4.0, 5.0),
        16: (3.0, 8.5),  # Mulai bubar kelas / pulang
        17: (2.0, 11.0), # Peak pulang sore
        18: (1.5, 7.5),
        19: (1.0, 4.0),
        20: (1.0, 2.5),
        21: (0.5, 1.5),
        22: (0.2, 0.8),
        23: (0.1, 0.3),
    }

    events = []
    track_counter = 1000

    curr_date = start_date
    while curr_date <= target_end_date:
        # Weekend has lower traffic
        is_weekend = curr_date.weekday() >= 5
        traffic_multiplier = 0.35 if is_weekend else 1.0

        daily_in_total = int(random.randint(180, 260) * traffic_multiplier)
        daily_out_total = int(daily_in_total * random.uniform(0.92, 0.98)) # slightly fewer out on normal days

        for hour in range(24):
            in_weight, out_weight = HOURLY_WEIGHTS[hour]
            
            # Approximate events this hour
            in_hour_count = int(round((in_weight / 80.0) * daily_in_total * random.uniform(0.8, 1.2)))
            out_hour_count = int(round((out_weight / 80.0) * daily_out_total * random.uniform(0.8, 1.2)))

            # Distribute IN events across the hour
            for _ in range(in_hour_count):
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                event_time = datetime(curr_date.year, curr_date.month, curr_date.day, hour, minute, second)
                
                # If target is today and time is in future, skip future events
                if curr_date == datetime.now().date() and event_time > datetime.now():
                    continue

                track_counter += 1
                confidence = round(random.uniform(0.84, 0.99), 2)
                events.append({
                    "occurred_at": event_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "direction": "IN",
                    "track_id": f"TRK-{track_counter}",
                    "confidence": confidence,
                    "source": "SIMULATED",
                    "camera_id": "CAM-01"
                })

            # Distribute OUT events across the hour
            for _ in range(out_hour_count):
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                event_time = datetime(curr_date.year, curr_date.month, curr_date.day, hour, minute, second)
                
                if curr_date == datetime.now().date() and event_time > datetime.now():
                    continue

                track_counter += 1
                confidence = round(random.uniform(0.82, 0.98), 2)
                events.append({
                    "occurred_at": event_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "direction": "OUT",
                    "track_id": f"TRK-{track_counter}",
                    "confidence": confidence,
                    "source": "SIMULATED",
                    "camera_id": "CAM-01"
                })

        curr_date += timedelta(days=1)

    # Sort events chronologically
    events.sort(key=lambda e: e['occurred_at'])
    
    # Insert in batch
    count = insert_events_batch(events)
    return {
        "inserted_count": count,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": target_end_date.strftime('%Y-%m-%d'),
        "source": "SIMULATED"
    }

def inject_single_event(direction="IN", source="SIMULATED", camera_id="CAM-01", occurred_at=None):
    """Memasukkan 1 kejadian instan (berguna untuk simulasi live / pengujian endpoint)"""
    from models import insert_event
    if not occurred_at:
        occurred_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    track_id = f"TRK-LIVE-{random.randint(1000, 9999)}"
    confidence = round(random.uniform(0.88, 0.99), 2)
    
    event_id = insert_event(
        occurred_at=occurred_at,
        direction=direction.upper(),
        track_id=track_id,
        confidence=confidence,
        source=source.upper(),
        camera_id=camera_id
    )
    return {
        "id": event_id,
        "occurred_at": occurred_at,
        "direction": direction.upper(),
        "track_id": track_id,
        "confidence": confidence,
        "source": source.upper(),
        "camera_id": camera_id
    }
