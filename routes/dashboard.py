from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, timedelta
from services.analytics_service import AnalyticsService
from models import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def dashboard_view():
    date_range = AnalyticsService.get_available_date_range()
    current_date = date_range.get('max_date') or datetime.now().strftime('%Y-%m-%d')
    return render_template('dashboard.html', active_page='dashboard', current_date=current_date)

@dashboard_bp.route('/api/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """
    Endpoint utama untuk metrik kartu dashboard:
    - Total IN
    - Total OUT
    - Arus Bersih (Net Flow)
    - Estimasi Okupansi
    - Jam Puncak (Peak Hour) & Jumlahnya
    - Status Anomali Data
    """
    date_str = request.args.get('date')
    start_date = request.args.get('start_date') or date_str
    end_date = request.args.get('end_date') or date_str
    camera_id = request.args.get('camera_id')
    
    # If no date passed, use max available date in database or today
    if not start_date:
        range_info = AnalyticsService.get_available_date_range()
        start_date = range_info.get('max_date') or datetime.now().strftime('%Y-%m-%d')
        end_date = start_date

    summary = AnalyticsService.get_summary(start_date=start_date, end_date=end_date, camera_id=camera_id)
    peak = AnalyticsService.get_peak_period(start_date=start_date, end_date=end_date, metric='IN', camera_id=camera_id)
    
    # Also get previous period for automatic comparison badge
    try:
        cur_d = datetime.strptime(start_date, '%Y-%m-%d').date()
        prev_d = (cur_d - timedelta(days=1)).strftime('%Y-%m-%d')
        comparison = AnalyticsService.compare_periods(
            period1_start=prev_d, period1_end=prev_d,
            period2_start=start_date, period2_end=end_date,
            metric='IN'
        )
    except Exception:
        comparison = None

    return jsonify({
        "status": "success",
        "data": {
            "summary": summary,
            "peak_period": peak,
            "comparison_to_previous_day": comparison
        }
    })

@dashboard_bp.route('/api/analytics/hourly', methods=['GET'])
def get_hourly_analytics():
    """Mengambil data chart per jam (00:00 - 23:00)"""
    date_str = request.args.get('date')
    camera_id = request.args.get('camera_id')
    
    if not date_str:
        range_info = AnalyticsService.get_available_date_range()
        date_str = range_info.get('max_date') or datetime.now().strftime('%Y-%m-%d')
        
    hourly_data = AnalyticsService.get_hourly_counts(date_str=date_str, camera_id=camera_id)
    return jsonify({
        "status": "success",
        "data": hourly_data
    })

@dashboard_bp.route('/api/analytics/daily', methods=['GET'])
def get_daily_analytics():
    """Mengambil rekap harian untuk rentang waktu (default 7 hari ke belakang)"""
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    camera_id = request.args.get('camera_id')
    
    if not end_date:
        range_info = AnalyticsService.get_available_date_range()
        end_date = range_info.get('max_date') or datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        end_d_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        start_date = (end_d_obj - timedelta(days=6)).strftime('%Y-%m-%d')
        
    trends = AnalyticsService.get_daily_trends(start_date, end_date, camera_id=camera_id)
    return jsonify({
        "status": "success",
        "data": {
            "start_date": start_date,
            "end_date": end_date,
            "trends": trends
        }
    })

@dashboard_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check kesiapan backend dan koneksi database"""
    try:
        range_info = AnalyticsService.get_available_date_range()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "total_records": range_info["total_records"],
            "date_range": range_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
