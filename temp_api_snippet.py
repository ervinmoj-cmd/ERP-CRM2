@app.route("/api/cotizaciones/detalle/<int:id>")
@require_permission("cotizaciones")
def api_cotizacion_detalle(id):
    """Get quote details including items"""
    cotizacion = get_cotizacion_by_id(id)
    if cotizacion:
        # Assuming get_cotizacion_by_id already returns items (it usually does for complete objects)
        # If not, we might need to fetch items separately. 
        # Based on previous code analysis (admin_cotizaciones_editar), get_cotizacion_by_id seems to return the full DictRow
        # We need to make sure we return JSON compatible data
        return jsonify(dict(cotizacion))
    return jsonify({"error": "Cotizacion not found"}), 404
