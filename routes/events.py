import csv
import io
from flask import Blueprint, render_template, request, jsonify, Response
from datetime import datetime
from models import get_events, count_filtered_events
from services.simulator import inject_single_event, generate_simulated_dataset
from services.analytics_service import AnalyticsService

events_bp = Blueprint('events', __name__)

@events_bp.route('/history')
def history_view():
    date_range = AnalyticsService.get_available_date_range()
    current_date = date_range.get('max_date') or datetime.now().strftime('%Y-%m-%d')
    return render_template('history.html', active_page='history', current_date=current_date)

@events_bp.route('/api/events', methods=['GET'])
def list_events():
    """
    Endpoint riwayat kejadian dengan filter lengkap dan pagination:
    - page, limit (default 25)
    - start_date, end_date
    - direction (IN/OUT)
    - source (SIMULATED/YOLO)
    - camera_id
    """
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 25))
    offset = (page - 1) * limit
    
    start_date = request.args.get('start_date') or request.args.get('date')
    end_date = request.args.get('end_date') or request.args.get('date')
    direction = request.args.get('direction')
    source = request.args.get('source')
    camera_id = request.args.get('camera_id')
    
    events = get_events(
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date,
        direction=direction,
        source=source,
        camera_id=camera_id
    )
    
    total = count_filtered_events(
        start_date=start_date,
        end_date=end_date,
        direction=direction,
        source=source,
        camera_id=camera_id
    )
    
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    return jsonify({
        "status": "success",
        "data": {
            "events": events,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_records": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    })

@events_bp.route('/api/events/export', methods=['GET'])
def export_events_csv():
    """Ekspor seluruh data kejadian terfilter ke file CSV"""
    start_date = request.args.get('start_date') or request.args.get('date')
    end_date = request.args.get('end_date') or request.args.get('date')
    direction = request.args.get('direction')
    source = request.args.get('source')
    camera_id = request.args.get('camera_id')
    
    # Get all matching events without small limit
    events = get_events(
        limit=100000,
        offset=0,
        start_date=start_date,
        end_date=end_date,
        direction=direction,
        source=source,
        camera_id=camera_id
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['id', 'occurred_at', 'direction', 'track_id', 'confidence', 'source', 'camera_id', 'created_at'])
    
    for e in events:
        writer.writerow([
            e['id'],
            e['occurred_at'],
            e['direction'],
            e.get('track_id') or '',
            e.get('confidence') or '',
            e['source'],
            e['camera_id'],
            e['created_at']
        ])
        
    output.seek(0)
    filename = f"people_analytics_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@events_bp.route('/api/events/simulate', methods=['POST'])
def trigger_simulation():
    """
    Endpoint untuk menyuntikkan atau meregenerasi data simulasi:
    - action: 'single' (direction: 'IN'/'OUT')
    - action: 'generate' (days: 14, clear_existing: true/false)
    """
    data = request.get_json() or {}
    action = data.get('action', 'single')
    
    if action == 'single':
        direction = data.get('direction', 'IN').upper()
        res = inject_single_event(
            direction=direction,
            source=data.get('source', 'SIMULATED'),
            camera_id=data.get('camera_id', 'CAM-01')
        )
        return jsonify({
            "status": "success",
            "message": f"Berhasil mencatat 1 orang {direction} secara instan.",
            "data": res
        })
        
    elif action == 'generate':
        days = int(data.get('days', 14))
        clear_existing = data.get('clear_existing', False)
        target_date = data.get('target_end_date') or datetime.now().strftime('%Y-%m-%d')
        res = generate_simulated_dataset(days=days, target_end_date=target_date, clear_existing=clear_existing)
        return jsonify({
            "status": "success",
            "message": f"Berhasil menghasilkan {res['inserted_count']} data kejadian simulasi selama {days} hari.",
            "data": res
        })
        
    else:
        return jsonify({"status": "error", "message": "Aksi tidak dikenali."}), 400
