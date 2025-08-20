from flask import Blueprint, jsonify
from dashboard.services.stats_service import get_statistics

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/stats', methods=['GET'])
def stats():
    statistics = get_statistics()
    return jsonify(statistics)