import sqlite3
from datetime import datetime, date, timedelta
from models import get_db_connection

class AnalyticsService:
    @staticmethod
    def _format_date(d):
        if isinstance(d, (datetime, date)):
            return d.strftime('%Y-%m-%d')
        return str(d) if d else None

    @classmethod
    def get_summary(cls, start_date=None, end_date=None, camera_id=None, baseline_occupancy=0):
        """
        Rekap kejadian IN, OUT, arus bersih (net flow), dan estimasi okupansi.
        start_date and end_date can be YYYY-MM-DD or full YYYY-MM-DD HH:MM:SS.
        """
        conn = get_db_connection()
        try:
            query = """
                SELECT 
                    direction,
                    COUNT(*) as count,
                    GROUP_CONCAT(DISTINCT source) as sources
                FROM count_events
                WHERE 1=1
            """
            params = []
            
            if start_date:
                s_str = cls._format_date(start_date)
                query += " AND occurred_at >= ?"
                params.append(f"{s_str} 00:00:00" if len(s_str) == 10 else s_str)
            if end_date:
                e_str = cls._format_date(end_date)
                query += " AND occurred_at <= ?"
                params.append(f"{e_str} 23:59:59" if len(e_str) == 10 else e_str)
            if camera_id:
                query += " AND camera_id = ?"
                params.append(camera_id)
                
            query += " GROUP BY direction"
            
            rows = conn.execute(query, params).fetchall()
            
            in_count = 0
            out_count = 0
            sources = set()
            
            for row in rows:
                direction = row['direction']
                cnt = row['count']
                if direction == 'IN':
                    in_count = cnt
                elif direction == 'OUT':
                    out_count = cnt
                if row['sources']:
                    for s in row['sources'].split(','):
                        sources.add(s.strip())
                        
            net_flow = in_count - out_count
            estimated_occupancy = baseline_occupancy + net_flow
            is_anomaly = estimated_occupancy < 0
            safe_occupancy = max(0, estimated_occupancy)
            
            source_label = "SIMULATED"
            if "YOLO" in sources and "SIMULATED" in sources:
                source_label = "MIXED (SIMULATED + YOLO)"
            elif "YOLO" in sources:
                source_label = "YOLO"
            elif not sources:
                source_label = "N/A"
                
            has_data = (in_count + out_count) > 0
            
            return {
                "period": {
                    "start": cls._format_date(start_date),
                    "end": cls._format_date(end_date) or cls._format_date(start_date)
                },
                "total_in": in_count,
                "total_out": out_out_count if (out_out_count := out_count) else 0,
                "net_flow": net_flow,
                "baseline_occupancy": baseline_occupancy,
                "estimated_occupancy": safe_occupancy,
                "is_negative_anomaly": is_anomaly,
                "raw_occupancy": estimated_occupancy,
                "source": source_label,
                "has_data": has_data
            }
        finally:
            conn.close()

    @classmethod
    def get_hourly_counts(cls, date_str, camera_id=None):
        """
        Rekap jumlah IN dan OUT per jam (00:00 - 23:00) untuk tanggal tertentu.
        """
        date_formatted = cls._format_date(date_str)
        conn = get_db_connection()
        try:
            # Query grouping by strftime('%H', occurred_at)
            query = """
                SELECT 
                    strftime('%H', occurred_at) as hour,
                    direction,
                    COUNT(*) as count,
                    GROUP_CONCAT(DISTINCT source) as sources
                FROM count_events
                WHERE occurred_at >= ? AND occurred_at <= ?
            """
            params = [f"{date_formatted} 00:00:00", f"{date_formatted} 23:59:59"]
            
            if camera_id:
                query += " AND camera_id = ?"
                params.append(camera_id)
                
            query += " GROUP BY hour, direction ORDER BY hour ASC"
            rows = conn.execute(query, params).fetchall()
            
            # Prepare 24 hours slots
            hours = [f"{h:02d}:00" for h in range(24)]
            in_counts = [0] * 24
            out_counts = [0] * 24
            sources = set()
            
            for row in rows:
                h_idx = int(row['hour'])
                if 0 <= h_idx < 24:
                    if row['direction'] == 'IN':
                        in_counts[h_idx] = row['count']
                    elif row['direction'] == 'OUT':
                        out_counts[h_idx] = row['count']
                if row['sources']:
                    for s in row['sources'].split(','):
                        sources.add(s.strip())
                        
            net_counts = [in_counts[i] - out_counts[i] for i in range(24)]
            
            # Cumulative occupancy throughout the day
            cumulative = []
            curr = 0
            for net in net_counts:
                curr += net
                cumulative.append(max(0, curr))
                
            source_label = "SIMULATED"
            if "YOLO" in sources and "SIMULATED" in sources:
                source_label = "MIXED"
            elif "YOLO" in sources:
                source_label = "YOLO"
            elif not sources:
                source_label = "SIMULATED"
                
            return {
                "date": date_formatted,
                "hours": hours,
                "in_counts": in_counts,
                "out_counts": out_counts,
                "net_counts": net_counts,
                "cumulative_occupancy": cumulative,
                "total_in": sum(in_counts),
                "total_out": sum(out_counts),
                "source": source_label,
                "has_data": (sum(in_counts) + sum(out_counts)) > 0
            }
        finally:
            conn.close()

    @classmethod
    def get_peak_period(cls, start_date=None, end_date=None, metric='IN', camera_id=None):
        """
        Mencari jam dengan intensitas tertinggi (peak period).
        metric: 'IN', 'OUT', atau 'TOTAL'.
        """
        metric = metric.upper() if metric else 'IN'
        conn = get_db_connection()
        try:
            query = """
                SELECT 
                    strftime('%Y-%m-%d', occurred_at) as event_date,
                    strftime('%H', occurred_at) as hour,
                    direction,
                    COUNT(*) as count,
                    GROUP_CONCAT(DISTINCT source) as sources
                FROM count_events
                WHERE 1=1
            """
            params = []
            
            if start_date:
                s_str = cls._format_date(start_date)
                query += " AND occurred_at >= ?"
                params.append(f"{s_str} 00:00:00" if len(s_str) == 10 else s_str)
            if end_date:
                e_str = cls._format_date(end_date)
                query += " AND occurred_at <= ?"
                params.append(f"{e_str} 23:59:59" if len(e_str) == 10 else e_str)
            if camera_id:
                query += " AND camera_id = ?"
                params.append(camera_id)
                
            query += " GROUP BY event_date, hour, direction"
            
            rows = conn.execute(query, params).fetchall()
            
            # Aggregate per (date, hour)
            slots = {} # (date, hour) -> {'IN': count, 'OUT': count, 'sources': set}
            for row in rows:
                key = (row['event_date'], int(row['hour']))
                if key not in slots:
                    slots[key] = {'IN': 0, 'OUT': 0, 'sources': set()}
                slots[key][row['direction']] += row['count']
                if row['sources']:
                    for s in row['sources'].split(','):
                        slots[key]['sources'].add(s.strip())
                        
            if not slots:
                return {
                    "period": {
                        "start": cls._format_date(start_date),
                        "end": cls._format_date(end_date) or cls._format_date(start_date)
                    },
                    "metric": metric,
                    "peak_hour": "Tidak ada data",
                    "peak_hour_start": None,
                    "peak_date": None,
                    "count": 0,
                    "source": "SIMULATED",
                    "has_data": False
                }
                
            best_key = None
            max_val = -1
            best_sources = set()
            
            for key, val in slots.items():
                if metric == 'IN':
                    score = val['IN']
                elif metric == 'OUT':
                    score = val['OUT']
                else: # TOTAL or NET
                    score = val['IN'] + val['OUT']
                    
                if score > max_val:
                    max_val = score
                    best_key = key
                    best_sources = val['sources']
                    
            p_date, p_hour = best_key
            hour_str = f"{p_hour:02d}:00 - {p_hour:02d}:59"
            
            source_label = "SIMULATED"
            if "YOLO" in best_sources and "SIMULATED" in best_sources:
                source_label = "MIXED"
            elif "YOLO" in best_sources:
                source_label = "YOLO"
                
            return {
                "period": {
                    "start": cls._format_date(start_date),
                    "end": cls._format_date(end_date) or cls._format_date(start_date)
                },
                "metric": metric,
                "peak_date": p_date,
                "peak_hour": hour_str,
                "peak_hour_start": p_hour,
                "count": max_val,
                "source": source_label,
                "has_data": max_val > 0
            }
        finally:
            conn.close()

    @classmethod
    def compare_periods(cls, period1_start, period1_end, period2_start, period2_end, metric='IN'):
        """
        Membandingkan total dua periode.
        period1 = Periode Pembanding (Lama / Baseline, misal: Kemarin)
        period2 = Periode Utama (Baru / Terkini, misal: Hari Ini)
        Rumus: Perubahan (%) = ((N_baru - N_lama) / N_lama) * 100%
        Penanganan khusus bila N_lama == 0.
        """
        metric = metric.upper() if metric else 'IN'
        
        sum1 = cls.get_summary(period1_start, period1_end)
        sum2 = cls.get_summary(period2_start, period2_end)
        
        if metric == 'IN':
            n_lama = sum1['total_in']
            n_baru = sum2['total_in']
        elif metric == 'OUT':
            n_lama = sum1['total_out']
            n_baru = sum2['total_out']
        else: # NET
            n_lama = sum1['net_flow']
            n_baru = sum2['net_flow']
            
        difference = n_baru - n_lama
        
        # Penanganan khusus jika nilai sebelumnya nol:
        if n_lama == 0:
            if n_baru == 0:
                change_percent = 0.0
                change_percent_str = "0.0% (Kedua periode 0)"
                note = "Tidak ada aktivitas pada kedua periode."
            else:
                change_percent = None # Matematika undefined
                change_percent_str = f"+{n_baru} (Basis awal 0)"
                note = "Data pada periode pembanding adalah 0, persentase tidak terdefinisi secara matematis."
        else:
            pct = ((n_baru - n_lama) / abs(n_lama)) * 100.0
            change_percent = round(pct, 2)
            prefix = "+" if change_percent > 0 else ""
            change_percent_str = f"{prefix}{change_percent:.2f}%"
            note = "Dihitung menggunakan rumus standar ((N_baru - N_lama) / N_lama) * 100%"

        if difference > 0:
            trend = "NAIK"
        elif difference < 0:
            trend = "TURUN"
        else:
            trend = "TETAP"

        return {
            "metric": metric,
            "period_previous": {
                "label": "Periode Pembanding (Lama)",
                "start": cls._format_date(period1_start),
                "end": cls._format_date(period1_end),
                "count": n_lama
            },
            "period_current": {
                "label": "Periode Terkini (Baru)",
                "start": cls._format_date(period2_start),
                "end": cls._format_date(period2_end),
                "count": n_baru
            },
            "difference": difference,
            "change_percent": change_percent,
            "change_percent_str": change_percent_str,
            "trend": trend,
            "note": note,
            "source": sum2['source'] if sum2['has_data'] else sum1['source']
        }

    @classmethod
    def get_daily_trends(cls, start_date, end_date, camera_id=None):
        """
        Mengambil rekap harian untuk rentang tanggal (berguna untuk chart mingguan).
        """
        s_str = cls._format_date(start_date)
        e_str = cls._format_date(end_date)
        
        conn = get_db_connection()
        try:
            query = """
                SELECT 
                    strftime('%Y-%m-%d', occurred_at) as day_date,
                    direction,
                    COUNT(*) as count
                FROM count_events
                WHERE occurred_at >= ? AND occurred_at <= ?
            """
            params = [f"{s_str} 00:00:00", f"{e_str} 23:59:59"]
            if camera_id:
                query += " AND camera_id = ?"
                params.append(camera_id)
                
            query += " GROUP BY day_date, direction ORDER BY day_date ASC"
            rows = conn.execute(query, params).fetchall()
            
            days_map = {}
            # Generate all dates in range
            d_curr = datetime.strptime(s_str, '%Y-%m-%d').date()
            d_last = datetime.strptime(e_str, '%Y-%m-%d').date()
            while d_curr <= d_last:
                d_key = d_curr.strftime('%Y-%m-%d')
                days_map[d_key] = {"date": d_key, "IN": 0, "OUT": 0, "NET": 0}
                d_curr += timedelta(days=1)
                
            for row in rows:
                d_key = row['day_date']
                if d_key in days_map:
                    direction = row['direction']
                    days_map[d_key][direction] = row['count']
                    days_map[d_key]['NET'] = days_map[d_key]['IN'] - days_map[d_key]['OUT']
                    
            return sorted(days_map.values(), key=lambda x: x['date'])
        finally:
            conn.close()

    @classmethod
    def get_available_date_range(cls):
        """Mengambil tanggal paling awal dan paling akhir di database"""
        conn = get_db_connection()
        try:
            row = conn.execute("""
                SELECT 
                    MIN(strftime('%Y-%m-%d', occurred_at)) as min_date,
                    MAX(strftime('%Y-%m-%d', occurred_at)) as max_date,
                    COUNT(*) as total_records
                FROM count_events
            """).fetchone()
            if row and row['min_date']:
                return {
                    "min_date": row['min_date'],
                    "max_date": row['max_date'],
                    "total_records": row['total_records']
                }
            return {
                "min_date": datetime.now().strftime('%Y-%m-%d'),
                "max_date": datetime.now().strftime('%Y-%m-%d'),
                "total_records": 0
            }
        finally:
            conn.close()
