import json
import re
import requests
from datetime import datetime, timedelta, date
from config import Config
from services.analytics_service import AnalyticsService

INDONESIAN_MONTHS = {
    'januari': 1, 'jan': 1,
    'februari': 2, 'feb': 2,
    'maret': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'mei': 5,
    'juni': 6, 'jun': 6,
    'juli': 7, 'jul': 7,
    'agustus': 8, 'agt': 8, 'agu': 8,
    'september': 9, 'sep': 9,
    'oktober': 10, 'okt': 10,
    'november': 11, 'nov': 11,
    'desember': 12, 'des': 12
}

TOOLS_SPEC = [
    {
        "name": "get_summary",
        "description": "Mengambil ringkasan total orang masuk (IN), keluar (OUT), arus bersih, dan okupansi untuk tanggal atau rentang tanggal tertentu.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Tanggal awal format YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "Tanggal akhir format YYYY-MM-DD (opsional, default sama dengan start_date)"}
            },
            "required": ["start_date"]
        }
    },
    {
        "name": "get_hourly_counts",
        "description": "Mengambil rekap data jumlah orang masuk dan keluar per jam (00:00 - 23:00) pada satu tanggal tertentu.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_str": {"type": "string", "description": "Tanggal yang dianalisis format YYYY-MM-DD"}
            },
            "required": ["date_str"]
        }
    },
    {
        "name": "get_peak_period",
        "description": "Mencari periode atau jam paling ramai/tertinggi aktivitasnya pada tanggal atau rentang tanggal tertentu.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Tanggal awal format YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "Tanggal akhir format YYYY-MM-DD (opsional)"},
                "metric": {"type": "string", "enum": ["IN", "OUT", "TOTAL"], "description": "Metrik keramaian: IN (masuk), OUT (keluar), atau TOTAL"}
            },
            "required": ["start_date"]
        }
    },
    {
        "name": "compare_periods",
        "description": "Membandingkan total orang masuk/keluar antara dua periode (misal: hari ini vs kemarin, minggu ini vs minggu lalu) dan menghitung persentase perubahannya.",
        "parameters": {
            "type": "object",
            "properties": {
                "period1_start": {"type": "string", "description": "Tanggal awal periode pembanding (lama) YYYY-MM-DD"},
                "period1_end": {"type": "string", "description": "Tanggal akhir periode pembanding (lama) YYYY-MM-DD"},
                "period2_start": {"type": "string", "description": "Tanggal awal periode utama (baru) YYYY-MM-DD"},
                "period2_end": {"type": "string", "description": "Tanggal akhir periode utama (baru) YYYY-MM-DD"},
                "metric": {"type": "string", "enum": ["IN", "OUT", "NET"], "description": "Metrik yang dibandingkan: IN, OUT, atau NET"}
            },
            "required": ["period1_start", "period1_end", "period2_start", "period2_end"]
        }
    },
    {
        "name": "get_occupancy_estimate",
        "description": "Mengambil estimasi jumlah orang yang saat ini masih berada di dalam area/gedung (okupansi).",
        "parameters": {
            "type": "object",
            "properties": {
                "target_date": {"type": "string", "description": "Tanggal target YYYY-MM-DD"}
            }
        }
    }
]

SYSTEM_PROMPT = """
Anda adalah AI Chat Analyst untuk sistem Smart People Analytics pada proyek TA/Kapita Selekta Fajar.
Tugas Anda adalah menjawab pertanyaan pengguna tentang statistik dan pergerakan orang (IN, OUT, okupansi, jam tersibuk).

ATURAN UTAMA:
1. Anda DILARANG KERAS mengarang (halusinasi) angka. Semua angka HARUS berasal dari pemanggilan fungsi analitik backend (tool calling).
2. Sebutkan secara jelas: tanggal/periode yang dianalisis, metrik yang dihitung, nilai angka numerik yang didapat, dan sumber data (SIMULATED atau YOLO).
3. Jika data tidak tersedia atau bernilai 0, sampaikan dengan jujur bahwa data belum tercatat atau tidak ada aktivitas.
4. Jawab dalam Bahasa Indonesia yang formal, ringkas, santun, dan mudah dipahami.
5. Jika pengguna menanyakan hal di luar topik analisis jumlah orang (misal cuaca umum, resep makanan), jelaskan dengan sopan bahwa Anda dibatasi hanya untuk analisis data pergerakan orang dan okupansi area.
"""

class AIService:
    @staticmethod
    def execute_tool(tool_name, args):
        """Mengeksekusi fungsi analitik backend dan mengembalikan hasil numerik yang valid"""
        if tool_name == "get_summary":
            return AnalyticsService.get_summary(
                start_date=args.get("start_date"),
                end_date=args.get("end_date")
            )
        elif tool_name == "get_hourly_counts":
            return AnalyticsService.get_hourly_counts(
                date_str=args.get("date_str")
            )
        elif tool_name == "get_peak_period":
            return AnalyticsService.get_peak_period(
                start_date=args.get("start_date"),
                end_date=args.get("end_date"),
                metric=args.get("metric", "IN")
            )
        elif tool_name == "compare_periods":
            return AnalyticsService.compare_periods(
                period1_start=args.get("period1_start"),
                period1_end=args.get("period1_end"),
                period2_start=args.get("period2_start"),
                period2_end=args.get("period2_end"),
                metric=args.get("metric", "IN")
            )
        elif tool_name == "get_occupancy_estimate":
            target_date = args.get("target_date")
            sum_res = AnalyticsService.get_summary(start_date=target_date, end_date=target_date)
            return {
                "target_date": target_date,
                "current_estimated_occupancy": sum_res["estimated_occupancy"],
                "total_in": sum_res["total_in"],
                "total_out": sum_res["total_out"],
                "net_flow": sum_res["net_flow"],
                "is_negative_anomaly": sum_res["is_negative_anomaly"],
                "source": sum_res["source"]
            }
        else:
            raise ValueError(f"Fungsi '{tool_name}' tidak dikenali oleh backend.")

    @classmethod
    def _extract_date_references(cls, text):
        """Mengekstrak tanggal dari teks pengguna (format YYYY-MM-DD, '11 Oktober 2026', 'hari ini', 'kemarin')"""
        today = datetime.now().date()
        text_lower = text.lower()

        # Check explicit YYYY-MM-DD
        m_iso = re.search(r'\b(20\d\d[-/]\d{1,2}[-/]\d{1,2})\b', text)
        if m_iso:
            s = m_iso.group(1).replace('/', '-')
            try:
                parts = s.split('-')
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            except Exception:
                pass

        # Check "11 Oktober 2026" or "11 Okt"
        for month_name, month_num in INDONESIAN_MONTHS.items():
            pattern = rf'\b(\d{{1,2}})\s+{month_name}(?:\s+(20\d\d))?\b'
            m = re.search(pattern, text_lower)
            if m:
                day = int(m.group(1))
                year = int(m.group(2)) if m.group(2) else today.year
                try:
                    return date(year, month_num, day)
                except Exception:
                    pass

        # Check relative dates
        if 'kemarin' in text_lower:
            return today - timedelta(days=1)
        if 'besok' in text_lower:
            return today + timedelta(days=1)
        if 'lusa' in text_lower:
            return today + timedelta(days=2)
            
        # Default to today
        return today

    @classmethod
    def _parse_intent_and_execute(cls, user_message):
        """
        Built-in Intelligent Analytic Engine:
        Memetakan pertanyaan Bahasa Indonesia ke tool analitik yang tepat,
        mengeksekusi data riil dari SQLite, dan menyusun penjelasan komprehensif.
        """
        msg = user_message.lower().strip()
        ref_date = cls._extract_date_references(user_message)
        ref_date_str = ref_date.strftime('%Y-%m-%d')
        yesterday_str = (ref_date - timedelta(days=1)).strftime('%Y-%m-%d')
        today_str = datetime.now().strftime('%Y-%m-%d')

        # Check for out-of-scope queries
        out_of_scope_keywords = ['resep', 'cuaca', 'presiden', 'sepak bola', 'film', 'lagu', 'puisi', 'kurs dollar']
        if any(k in msg for k in out_of_scope_keywords):
            return {
                "answer": "Maaf, saya adalah **AI Chat Analyst** khusus sistem **Smart People Analytics**. Saya hanya dapat membantu menjawab dan menganalisis data terkait pergerakan orang masuk (IN), keluar (OUT), estimasi okupansi ruangan, jam sibuk, serta perbandingan aktivitas antarperiode.",
                "source": "SIMULATED",
                "period": None,
                "evidence": None
            }

        # Intent 1: Perbandingan (Compare periods) - "bandingkan", "dibanding", "perubahan", "kenaikan", "penurunan"
        if any(w in msg for w in ['banding', 'dibanding', 'persen', 'perubahan', 'kenaikan', 'penurunan', 'selisih hari']):
            metric = 'OUT' if ('keluar' in msg or 'out' in msg) else 'IN'
            
            # Period 1 = yesterday, Period 2 = today or ref_date
            if 'kemarin' in msg or 'hari ini' in msg or True:
                p1_start = yesterday_str
                p1_end = yesterday_str
                p2_start = ref_date_str
                p2_end = ref_date_str
                
            tool_name = "compare_periods"
            tool_args = {
                "period1_start": p1_start,
                "period1_end": p1_end,
                "period2_start": p2_start,
                "period2_end": p2_end,
                "metric": metric
            }
            res = cls.execute_tool(tool_name, tool_args)
            
            pct_text = res['change_percent_str']
            diff = res['difference']
            n_lama = res['period_previous']['count']
            n_baru = res['period_current']['count']
            source = res['source']
            trend = res['trend']
            
            trend_desc = "meningkat" if diff > 0 else ("menurun" if diff < 0 else "sama/stabil")
            abs_diff = abs(diff)
            metric_label = "orang masuk (IN)" if metric == 'IN' else "orang keluar (OUT)"
            
            answer = (
                f"Berdasarkan data **{source}**:\n\n"
                f"- **Periode Pembanding ({p1_start})**: {n_lama} orang\n"
                f"- **Periode Terkini ({p2_start})**: {n_baru} orang\n"
                f"- **Selisih**: {diff:+d} orang ({trend_desc} sebesar {abs_diff} orang)\n"
                f"- **Persentase Perubahan**: **{pct_text}**\n\n"
                f"Aktivitas {metric_label} pada {p2_start} terpantau **{trend}** dibanding periode sebelumnya."
            )
            
            return {
                "answer": answer,
                "source": source,
                "period": {"previous": p1_start, "current": p2_start},
                "evidence": {
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": res
                }
            }

        # Intent 2: Jam Paling Ramai / Puncak (Peak Period) - "paling ramai", "puncak", "terbanyak", "tersibuk", "jam berapa"
        if any(w in msg for w in ['ramai', 'puncak', 'tersibuk', 'terbanyak', 'tertinggi', 'peak']) and any(w in msg for w in ['jam', 'kapan', 'waktu']):
            metric = 'OUT' if ('keluar' in msg or 'out' in msg) else 'IN'
            tool_name = "get_peak_period"
            tool_args = {
                "start_date": ref_date_str,
                "end_date": ref_date_str,
                "metric": metric
            }
            res = cls.execute_tool(tool_name, tool_args)
            source = res['source']
            metric_label = "orang masuk (IN)" if metric == 'IN' else "orang keluar (OUT)"

            if not res['has_data']:
                answer = f"Berdasarkan data **{source}** untuk tanggal **{ref_date_str}**, belum ada catatan aktivitas {metric_label} yang tercatat di database."
            else:
                answer = (
                    f"Berdasarkan data **{source}** pada tanggal **{ref_date_str}**, "
                    f"periode dengan aktivitas {metric_label} paling tinggi tercatat pada pukul "
                    f"**{res['peak_hour']}** dengan jumlah akumulasi **{res['count']} orang**."
                )

            return {
                "answer": answer,
                "source": source,
                "period": {"date": ref_date_str},
                "evidence": {
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": res
                }
            }

        # Intent 3: Estimasi Okupansi / Orang di dalam - "berapa orang di dalam", "okupansi", "sisa orang", "di area"
        if any(w in msg for w in ['di dalam', 'okupansi', 'sisa orang', 'saat ini', 'akhir hari', 'dalam ruangan', 'dalam gedung']):
            tool_name = "get_occupancy_estimate"
            tool_args = {"target_date": ref_date_str}
            res = cls.execute_tool(tool_name, tool_args)
            source = res['source']
            
            warning_note = ""
            if res['is_negative_anomaly']:
                warning_note = "\n\n*(Catatan Anomali Data: Arus keluar terdeteksi melebihi arus masuk yang tercatat tanpa baseline awal)*"

            answer = (
                f"Berdasarkan rekap data **{source}** pada tanggal **{ref_date_str}**:\n\n"
                f"- Total Masuk (IN): **{res['total_in']} orang**\n"
                f"- Total Keluar (OUT): **{res['total_out']} orang**\n"
                f"- Arus Bersih (Net Flow): **{res['net_flow']:+d} orang**\n"
                f"- **Estimasi Okupansi**: **{res['current_estimated_occupancy']} orang**{warning_note}"
            )

            return {
                "answer": answer,
                "source": source,
                "period": {"date": ref_date_str},
                "evidence": {
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": res
                }
            }

        # Intent 4: Selisih IN dan OUT - "selisih", "net flow", "netto", "beda masuk dan keluar"
        if 'selisih' in msg:
            tool_name = "get_summary"
            tool_args = {"start_date": ref_date_str, "end_date": ref_date_str}
            res = cls.execute_tool(tool_name, tool_args)
            source = res['source']
            diff = res['total_in'] - res['total_out']
            diff_label = "lebih banyak yang masuk" if diff > 0 else ("lebih banyak yang keluar" if diff < 0 else "seimbang antara masuk dan keluar")

            answer = (
                f"Berdasarkan data **{source}** pada tanggal **{ref_date_str}**:\n\n"
                f"- Total Masuk (IN): **{res['total_in']} orang**\n"
                f"- Total Keluar (OUT): **{res['total_out']} orang**\n"
                f"- **Selisih (IN - OUT)**: **{diff:+d} orang** ({diff_label})."
            )

            return {
                "answer": answer,
                "source": source,
                "period": {"date": ref_date_str},
                "evidence": {
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": res
                }
            }

        # Intent 5: Rekap per jam - "per jam", "setiap jam", "grafik", "pola waktu"
        if any(w in msg for w in ['per jam', 'tiap jam', 'pola jam', 'rincian jam', 'distribusi jam']):
            tool_name = "get_hourly_counts"
            tool_args = {"date_str": ref_date_str}
            res = cls.execute_tool(tool_name, tool_args)
            source = res['source']
            
            # Find top 3 hours
            in_indexed = [(i, count) for i, count in enumerate(res['in_counts']) if count > 0]
            in_indexed.sort(key=lambda x: x[1], reverse=True)
            top_3 = in_indexed[:3]
            top_str = ", ".join([f"pukul {h:02d}:00 ({c} orang)" for h, c in top_3]) if top_3 else "Belum ada aktivitas"

            answer = (
                f"Rekap aktivitas per jam tanggal **{ref_date_str}** ({source}):\n\n"
                f"- Total Masuk (IN): **{res['total_in']} orang**\n"
                f"- Total Keluar (OUT): **{res['total_out']} orang**\n"
                f"- 3 Jam tersibuk masuk: **{top_str}**\n\n"
                f"Data lengkap 24 jam dapat dilihat langsung melalui grafik pada halaman Dashboard."
            )

            return {
                "answer": answer,
                "source": source,
                "period": {"date": ref_date_str},
                "evidence": {
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": res
                }
            }

        # Default Intent: Total IN / Total OUT / Ringkasan Umum (Summary)
        # e.g., "Berapa jumlah orang masuk hari ini?", "Rekap tanggal 11 Oktober 2026", "Total pengunjung"
        tool_name = "get_summary"
        tool_args = {"start_date": ref_date_str, "end_date": ref_date_str}
        res = cls.execute_tool(tool_name, tool_args)
        source = res['source']

        if not res['has_data']:
            answer = f"Berdasarkan data **{source}**, tidak ditemukan catatan kejadian orang masuk atau keluar untuk tanggal **{ref_date_str}**."
        else:
            if 'keluar' in msg or 'out' in msg:
                answer = (
                    f"Berdasarkan data **{source}** pada tanggal **{ref_date_str}**, "
                    f"total orang keluar (OUT) adalah sebanyak **{res['total_out']} orang** "
                    f"(dengan perbandingan {res['total_in']} orang masuk)."
                )
            elif 'masuk' in msg or 'in' in msg:
                answer = (
                    f"Berdasarkan data **{source}** pada tanggal **{ref_date_str}**, "
                    f"total orang masuk (IN) tercatat sebanyak **{res['total_in']} orang** "
                    f"(dengan perbandingan {res['total_out']} orang keluar)."
                )
            else:
                answer = (
                    f"Ringkasan analitik data **{source}** untuk tanggal **{ref_date_str}**:\n\n"
                    f"- Total Orang Masuk (IN): **{res['total_in']} orang**\n"
                    f"- Total Orang Keluar (OUT): **{res['total_out']} orang**\n"
                    f"- Arus Bersih (Net Flow): **{res['net_flow']:+d} orang**\n"
                    f"- Estimasi Okupansi: **{res['estimated_occupancy']} orang**."
                )

        return {
            "answer": answer,
            "source": source,
            "period": {"date": ref_date_str},
            "evidence": {
                "tool": tool_name,
                "arguments": tool_args,
                "result": res
            }
        }

    @classmethod
    def _call_gemini_api(cls, user_message, api_key, model_name="gemini-1.5-flash"):
        """Panggilan Gemini API dengan Function Calling (Google REST Endpoint)"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        # Format function declarations for Gemini
        gemini_tools = [{
            "function_declarations": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"]
                } for t in TOOLS_SPEC
            ]
        }]
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{SYSTEM_PROMPT}\n\nPertanyaan pengguna: {user_message}\nTanggal hari ini: {datetime.now().strftime('%Y-%m-%d')}"}]
                }
            ],
            "tools": gemini_tools
        }
        
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code != 200:
            raise Exception(f"Gemini API Error {resp.status_code}: {resp.text}")
            
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise Exception("Tidak ada respons dari Gemini API.")
            
        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        
        # Check for function call
        tool_call = None
        for part in parts:
            if "functionCall" in part:
                tool_call = part["functionCall"]
                break
                
        if tool_call:
            fn_name = tool_call.get("name")
            fn_args = tool_call.get("args", {})
            
            # Execute backend function
            tool_result = cls.execute_tool(fn_name, fn_args)
            
            # Call back Gemini with function response to compose final answer
            second_payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{SYSTEM_PROMPT}\n\nPertanyaan pengguna: {user_message}\nTanggal hari ini: {datetime.now().strftime('%Y-%m-%d')}"}]
                    },
                    {
                        "role": "model",
                        "parts": [{"functionCall": {"name": fn_name, "args": fn_args}}]
                    },
                    {
                        "role": "function",
                        "parts": [{
                            "functionResponse": {
                                "name": fn_name,
                                "response": tool_result
                            }
                        }]
                    }
                ]
            }
            second_resp = requests.post(url, json=second_payload, timeout=20)
            if second_resp.status_code == 200:
                sec_data = second_resp.json()
                sec_parts = sec_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                final_text = "".join([p.get("text", "") for p in sec_parts])
            else:
                final_text = f"Fungsi {fn_name} dieksekusi dengan hasil: {json.dumps(tool_result)}"
                
            return {
                "answer": final_text,
                "source": tool_result.get("source", "SIMULATED"),
                "period": tool_result.get("period", None),
                "evidence": {
                    "tool": fn_name,
                    "arguments": fn_args,
                    "result": tool_result
                }
            }
        else:
            # Direct text answer
            text_ans = "".join([p.get("text", "") for p in parts])
            return {
                "answer": text_ans,
                "source": "SIMULATED",
                "period": None,
                "evidence": None
            }

    @classmethod
    def _call_openai_api(cls, user_message, api_key, model_name="gpt-4o-mini"):
        """Panggilan OpenAI API dengan Function Calling"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        openai_tools = [{"type": "function", "function": t} for t in TOOLS_SPEC]
        
        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\nTanggal hari ini: {datetime.now().strftime('%Y-%m-%d')}"},
            {"role": "user", "content": user_message}
        ]
        
        payload = {
            "model": model_name,
            "messages": messages,
            "tools": openai_tools,
            "tool_choice": "auto"
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code != 200:
            raise Exception(f"OpenAI API Error {resp.status_code}: {resp.text}")
            
        data = resp.json()
        choice = data["choices"][0]["message"]
        tool_calls = choice.get("tool_calls")
        
        if tool_calls:
            tc = tool_calls[0]
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            
            tool_result = cls.execute_tool(fn_name, fn_args)
            
            messages.append(choice)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(tool_result)
            })
            
            second_resp = requests.post(url, headers=headers, json={
                "model": model_name,
                "messages": messages
            }, timeout=20)
            
            if second_resp.status_code == 200:
                final_answer = second_resp.json()["choices"][0]["message"]["content"]
            else:
                final_answer = f"Fungsi {fn_name} dijalankan: {json.dumps(tool_result)}"
                
            return {
                "answer": final_answer,
                "source": tool_result.get("source", "SIMULATED"),
                "period": tool_result.get("period", None),
                "evidence": {
                    "tool": fn_name,
                    "arguments": fn_args,
                    "result": tool_result
                }
            }
        else:
            return {
                "answer": choice.get("content", ""),
                "source": "SIMULATED",
                "period": None,
                "evidence": None
            }

    @classmethod
    def ask(cls, user_message, provider=None, api_key=None):
        """
        Main entry point untuk AI Chat Analyst.
        Mencoba memanggil provider LLM terpilih (Gemini / OpenAI),
        dan secara otomatis fallback ke Built-in Analytical Reasoning Engine bila key kosong atau terjadi error jaringan.
        """
        provider = provider or Config.LLM_PROVIDER
        
        # 1. Check Gemini
        if provider == "gemini":
            key = api_key or Config.GEMINI_API_KEY
            if key:
                try:
                    return cls._call_gemini_api(user_message, key, Config.GEMINI_MODEL)
                except Exception as e:
                    # Fallback cleanly with note
                    res = cls._parse_intent_and_execute(user_message)
                    res["answer"] += f"\n\n*(Catatan fallback sistem: Gagal terhubung ke Gemini API [{str(e)[:60]}...]. Jawaban dihasilkan oleh Analytics Engine lokal)*"
                    return res
                    
        # 2. Check OpenAI
        elif provider == "openai":
            key = api_key or Config.OPENAI_API_KEY
            if key:
                try:
                    return cls._call_openai_api(user_message, key, Config.OPENAI_MODEL)
                except Exception as e:
                    res = cls._parse_intent_and_execute(user_message)
                    res["answer"] += f"\n\n*(Catatan fallback sistem: Gagal terhubung ke OpenAI API [{str(e)[:60]}...]. Jawaban dihasilkan oleh Analytics Engine lokal)*"
                    return res

        # 3. Default to Built-in Engine (zero external dependencies, reliable & fast)
        return cls._parse_intent_and_execute(user_message)
