
import threading
import time

from flask import Flask, jsonify
from flask_cors import CORS

from database import init_database, get_connection
from simulator import simulate_readings
from ml_model import (
    predict_time_to_full,
    get_priority,
    get_model_evaluation
)

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://smart-waste-ai-lyart.vercel.app",
            "https://vercel.com"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

init_database()



def get_bins():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM bins ORDER BY id"
        ).fetchall()

    results = []

    for row in rows:
        b = dict(row)

        fill = round(float(b["fill_percent"]), 2)
        weight = round(float(b["weight_kg"]), 2)
        capacity = float(b["capacity_kg"])
        growth = float(b["daily_growth"])

        weight_percent = (
            round(weight / capacity * 100, 2)
            if capacity > 0
            else 0
        )

        days = predict_time_to_full(fill, growth)

        priority = get_priority(
            fill,
            weight_percent,
            days
        )

        b.update({
            "fill_percent": fill,
            "weight_kg": weight,
            "weight_percent": weight_percent,
            "distance_cm": round(
                100 * (1 - fill / 100), 2
            ),
            "days_to_full": days,
            "priority": priority,
            "simulated": True
        })

        results.append(b)

    return results


@app.get("/")
def home():
    return jsonify({
        "project": "SmartWaste AI",
        "status": "Backend running",
        "simulation": True,
        "total_bins": len(get_bins())
    })


@app.get("/api/bins")
def bins():
    return jsonify(get_bins())


@app.get("/api/dashboard")
def dashboard():
    data = get_bins()
    total = len(data)

    return jsonify({
        "total_bins": total,
        "average_fill": round(
            sum(b["fill_percent"] for b in data) / total,
            2
        ) if total else 0,
        "total_waste_kg": round(
            sum(b["weight_kg"] for b in data),
            2
        ),
        "critical_bins": sum(
            b["priority"] == "Critical"
            for b in data
        ),
        "high_priority_bins": sum(
            b["priority"] == "High"
            for b in data
        ),
        "bins": data,
        "simulated": True
    })


@app.get("/api/predictions")
def predictions():
    return jsonify([
        {
            "bin_id": b["id"],
            "name": b["name"],
            "location": b["location"],
            "fill_percent": b["fill_percent"],
            "days_to_full": b["days_to_full"],
            "priority": b["priority"]
        }
        for b in get_bins()
    ])


@app.get("/api/alerts")
def alerts():
    results = []

    for b in get_bins():
        if b["fill_percent"] >= 75:
            results.append({
                "bin": b["name"],
                "type": "Fill Level",
                "message": (
                    f'Bin is {b["fill_percent"]}% full'
                ),
                "priority": b["priority"]
            })

        if b["weight_percent"] >= 75:
            results.append({
                "bin": b["name"],
                "type": "Weight",
                "message": (
                    f'Weight capacity is '
                    f'{b["weight_percent"]}% used'
                ),
                "priority": b["priority"]
            })

    return jsonify(results)


@app.get("/api/history")
def history():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                readings.*,
                bins.name
            FROM readings
            JOIN bins
                ON bins.id = readings.bin_id
            ORDER BY readings.id DESC
            LIMIT 100
        """).fetchall()

    return jsonify([
        dict(row) for row in rows
    ])


@app.post("/api/simulate")
def simulate():
    readings = simulate_readings()

    return jsonify({
        "message": "Virtual sensor readings generated",
        "readings": readings,
        "simulated": True
    })


@app.post("/api/collect/<int:bin_id>")
def collect_bin(bin_id):
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        b = conn.execute(
            "SELECT * FROM bins WHERE id = ?",
            (bin_id,)
        ).fetchone()

        if b is None:
            return jsonify({
                "error": "Bin not found"
            }), 404

        previous_fill = float(
            b["fill_percent"]
        )

        collected_weight = float(
            b["weight_kg"]
        )

        conn.execute("""
            INSERT INTO collections
            (
                bin_id,
                previous_fill,
                collected_weight_kg
            )
            VALUES (?, ?, ?)
        """, (
            bin_id,
            previous_fill,
            collected_weight
        ))

        conn.execute("""
            UPDATE bins
            SET fill_percent = 0,
                weight_kg = 0
            WHERE id = ?
        """, (bin_id,))

        conn.execute("""
            INSERT INTO readings
            (
                bin_id,
                fill_percent,
                weight_kg
            )
            VALUES (?, 0, 0)
        """, (bin_id,))

    return jsonify({
        "success": True,
        "message": (
            f"SW-{bin_id:03d} collected successfully"
        ),
        "previous_fill": round(
            previous_fill, 2
        ),
        "collected_weight_kg": round(
            collected_weight, 2
        ),
        "simulated": True
    })


@app.get("/api/collections")
def collection_history():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                c.*,
                b.name,
                b.location
            FROM collections c
            JOIN bins b
                ON b.id = c.bin_id
            ORDER BY c.id DESC
            LIMIT 500
        """).fetchall()

    return jsonify([
        dict(row) for row in rows
    ])


@app.get("/api/analytics/summary")
def analytics_summary():
    with get_connection() as conn:
        total_readings = conn.execute(
            "SELECT COUNT(*) FROM readings"
        ).fetchone()[0]

        collected = conn.execute("""
            SELECT
                COUNT(*) AS events,
                COALESCE(
                    SUM(collected_weight_kg), 0
                ) AS kg
            FROM collections
        """).fetchone()

    return jsonify({
        "total_sensor_readings": total_readings,
        "completed_collections": collected["events"],
        "total_collected_kg": round(
            collected["kg"], 2
        ),
        "simulated": True
    })


@app.get("/api/ml/evaluation")
def ml_evaluation():
    return jsonify(
        get_model_evaluation()
    )


def background_simulator():
    while True:
        time.sleep(15)

        try:
            simulate_readings()
        except Exception:
            app.logger.exception(
                "Background simulation failed"
            )


if __name__ == "__main__":
    worker = threading.Thread(
        target=background_simulator,
        daemon=True
    )

    worker.start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
