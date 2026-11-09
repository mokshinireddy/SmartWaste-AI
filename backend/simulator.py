
import random
from datetime import datetime, timezone
from database import get_connection

def simulate_readings():
    now = datetime.now(timezone.utc)
    results = []

    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        state = conn.execute(
            "SELECT last_tick FROM simulation_state WHERE id = 1"
        ).fetchone()

        previous = datetime.fromisoformat(
            state["last_tick"].replace("Z", "+00:00")
        )

        if previous.tzinfo is None:
            previous = previous.replace(tzinfo=timezone.utc)

        elapsed_hours = max(
            0, (now - previous).total_seconds() / 3600
        )

        elapsed_hours = min(elapsed_hours, 24)

        bins = conn.execute("SELECT * FROM bins").fetchall()

        for b in bins:
            growth = b["daily_growth"] / 24 * elapsed_hours
            growth *= random.uniform(0.85, 1.15)

            fill = min(
                100, b["fill_percent"] + growth
            )

            weight_growth = (
                b["capacity_kg"] * growth / 100
                * random.uniform(0.8, 1.1)
            )

            weight = min(
                b["capacity_kg"],
                b["weight_kg"] + weight_growth
            )

            conn.execute("""
                UPDATE bins
                SET fill_percent = ?, weight_kg = ?
                WHERE id = ?
            """, (fill, weight, b["id"]))

            conn.execute("""
                INSERT INTO readings
                (bin_id, fill_percent, weight_kg)
                VALUES (?, ?, ?)
            """, (b["id"], fill, weight))

            results.append({
                "bin_id": b["id"],
                "device": f"ESP32-SIM-{b['id']:03d}",
                "fill_percent": round(fill, 2),
                "hx711_weight_kg": round(weight, 2),
                "ultrasonic_distance_cm": round(
                    100 * (1 - fill / 100), 2
                ),
                "simulated": True
            })

        conn.execute("""
            UPDATE simulation_state
            SET last_tick = ?
            WHERE id = 1
        """, (now.isoformat(),))

    return results
