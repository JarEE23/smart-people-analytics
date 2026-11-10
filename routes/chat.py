import json
import uuid
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from models import (
    create_chat_session,
    get_chat_sessions,
    get_chat_session,
    insert_chat_message,
    get_chat_messages,
    delete_chat_session
)
from services.ai_service import AIService
from config import Config

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
def chat_view():
    return render_template('chat.html', active_page='chat')

@chat_bp.route('/api/chat', methods=['POST'])
def handle_chat_message():
    """
    Endpoint pemrosesan chat AI:
    Menerima pertanyaan, memanggil fungsi analitik backend (tool calling),
    menyusun penjelasan dalam Bahasa Indonesia, dan menyimpan riwayat percakapan.
    """
    payload = request.get_json() or {}
    message = payload.get('message', '').strip()
    session_id = payload.get('session_id')
    provider = payload.get('provider')
    api_key = payload.get('api_key')
    
    if not message:
        return jsonify({"status": "error", "message": "Pesan tidak boleh kosong."}), 400

    # Ensure session exists
    if not session_id:
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        title = message[:40] + ("..." if len(message) > 40 else "")
        create_chat_session(session_id, title=title)
    else:
        existing = get_chat_session(session_id)
        if not existing:
            title = message[:40] + ("..." if len(message) > 40 else "")
            create_chat_session(session_id, title=title)

    # Save user message
    insert_chat_message(session_id=session_id, role="user", content=message)

    # Process via AI Service (Tool Calling + Intent Analysis)
    try:
        ai_response = AIService.ask(user_message=message, provider=provider, api_key=api_key)
        
        answer_text = ai_response.get("answer", "")
        evidence = ai_response.get("evidence")
        evidence_json = json.dumps(evidence) if evidence else None
        
        # Save assistant message
        insert_chat_message(
            session_id=session_id,
            role="assistant",
            content=answer_text,
            evidence_json=evidence_json
        )
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "answer": answer_text,
            "source": ai_response.get("source", "SIMULATED"),
            "period": ai_response.get("period"),
            "evidence": evidence
        })
    except Exception as e:
        error_msg = f"Terjadi kesalahan saat memproses pertanyaan: {str(e)}"
        insert_chat_message(session_id=session_id, role="assistant", content=error_msg)
        return jsonify({
            "status": "error",
            "session_id": session_id,
            "answer": error_msg,
            "message": str(e)
        }), 500

@chat_bp.route('/api/chat/sessions', methods=['GET', 'POST'])
def manage_sessions():
    if request.method == 'POST':
        data = request.get_json() or {}
        new_id = f"sess-{uuid.uuid4().hex[:8]}"
        title = data.get('title', 'Percakapan baru')
        create_chat_session(new_id, title=title)
        return jsonify({"status": "success", "session_id": new_id, "title": title})
        
    sessions = get_chat_sessions()
    return jsonify({"status": "success", "data": sessions})

@chat_bp.route('/api/chat/sessions/<session_id>', methods=['GET', 'DELETE'])
def session_detail(session_id):
    if request.method == 'DELETE':
        delete_chat_session(session_id)
        return jsonify({"status": "success", "message": "Sesi berhasil dihapus."})
        
    session = get_chat_session(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Sesi tidak ditemukan."}), 404
        
    messages = get_chat_messages(session_id)
    return jsonify({
        "status": "success",
        "session": session,
        "messages": messages
    })

@chat_bp.route('/api/chat/config', methods=['GET'])
def get_ai_config():
    """Mengembalikan status provider AI saat ini (tanpa membocorkan isi key penuh)"""
    return jsonify({
        "status": "success",
        "provider": Config.LLM_PROVIDER,
        "has_gemini_key": bool(Config.GEMINI_API_KEY),
        "has_openai_key": bool(Config.OPENAI_API_KEY),
        "gemini_model": Config.GEMINI_MODEL,
        "openai_model": Config.OPENAI_MODEL
    })
