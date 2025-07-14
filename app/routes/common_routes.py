from flask import jsonify, request, Blueprint

common_bp = Blueprint('common', __name__)

@common_bp.route('/')
def hello_world():
    """기본 홈 라우트"""
    return 'Hello, Flask in Docker! (Financial Tracker App)'

@common_bp.route('/health')
def health_check():
    """서버 상태 확인 라우트"""
    from datetime import datetime
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "covered_call_explorer_backend",
        "version": "1.0.0"
    })

@common_bp.route('/echo', methods=['POST'])
def echo_message():
    """
    POST 요청으로 받은 'message'를 그대로 응답하는 테스트용 라우트
    """
    data = request.get_json()
    if data and 'message' in data:
        received_message = data['message']
        return jsonify({"response_message": received_message})
    return jsonify({"error": "No 'message' field found in request"}), 400