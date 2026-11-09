
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, BarChart3, BrainCircuit,
  CheckCircle2, Cpu, Download, Gauge,
  LayoutDashboard, Play, RefreshCw, Settings,
  Trash2, Truck, Weight
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, CartesianGrid,
  XAxis, YAxis, Tooltip, Legend, LineChart, Line,
  PieChart, Pie, Cell
} from "recharts";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const NAV = [
  ["Dashboard", LayoutDashboard],
  ["Bin Monitoring", Trash2],
  ["Virtual Sensor Lab", Cpu],
  ["AI Predictions", BrainCircuit],
  ["Alerts", AlertTriangle],
  ["Analytics", BarChart3],
  ["Collection Planning", Truck],
  ["Reports", Download],
  ["Settings", Settings]
];

const COLORS = {
  green: "#315c46",
  sage: "#82a68b",
  amber: "#c88b35",
  red: "#c6534c"
};

const num = (value, digits = 1) =>
  Number(value ?? 0).toFixed(digits);

const rank = { Critical: 4, High: 3, Medium: 2, Low: 1 };

function Priority({ value }) {
  const color = value === "Critical"
    ? COLORS.red
    : value === "High"
      ? COLORS.amber
      : value === "Medium"
        ? COLORS.sage
        : COLORS.green;

  return (
    <span className="sw-priority" style={{
      color,
      background: `${color}18`
    }}>
      {value || "Low"}
    </span>
  );
}

function Panel({ title, action, children }) {
  return (
    <section className="sw-panel">
      <div className="sw-panel-head">
        <h3>{title}</h3>
        {action}
      </div>
      {children}
    </section>
  );
}

function Metric({ title, value, detail, icon: Icon }) {
  return (
    <div className="sw-metric">
      <div className="sw-metric-label">
        <span>{title}</span>
        {Icon && <Icon size={19} />}
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function DataTable({ headers, children }) {
  return (
    <div className="sw-table-wrap">
      <table className="sw-table">
        <thead>
          <tr>
            {headers.map(h => <th key={h}>{h}</th>)}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

function PageTitle({ title, description }) {
  return (
    <div className="sw-page-title">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
}

function downloadCSV(filename, records) {
  if (!records.length) {
    alert("No records available.");
    return;
  }

  const keys = [...new Set(records.flatMap(Object.keys))];
  const escape = value =>
    `"${String(value ?? "").replaceAll('"', '""')}"`;

  const lines = [
    keys.map(escape).join(","),
    ...records.map(row =>
      keys.map(key => escape(row[key])).join(",")
    )
  ];

  const blob = new Blob([lines.join("\r\n")], {
    type: "text/csv;charset=utf-8"
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [page, setPage] = useState("Dashboard");
  const [dashboard, setDashboard] = useState({});
  const [bins, setBins] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [collections, setCollections] = useState([]);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdate, setLastUpdate] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [collectingId, setCollectingId] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(15);
  const [search, setSearch] = useState("");
  const [zoneFilter, setZoneFilter] = useState("All");

  const refresh = useCallback(async () => {
    try {
      const paths = [
        "/api/dashboard",
        "/api/alerts",
        "/api/history",
        "/api/collections"
      ];

      const responses = await Promise.all(
        paths.map(path => fetch(API + path))
      );

      if (responses.some(r => !r.ok)) {
        throw new Error("One or more APIs failed");
      }

      const [d, a, h, c] = await Promise.all(
        responses.map(r => r.json())
      );

      setDashboard(d);
      setBins(d.bins || []);
      setAlerts(a);
      setHistory(h);
      setCollections(c);
      setLastUpdate(new Date());
      setError("");
    } catch (err) {
      setError("Backend connection failed. Check Flask port 5000.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    let cancelled = false;

    async function loadEvaluation() {
      try {
        const response = await fetch(
          `${API}/api/ml/evaluation`
        );

        if (!response.ok) return;

        const data = await response.json();

        if (!cancelled) {
          setEvaluation(data);
        }
      } catch (err) {
        console.error("AI evaluation unavailable", err);
      }
    }

    loadEvaluation();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const timer = setInterval(
      refresh,
      refreshInterval * 1000
    );

    return () => clearInterval(timer);
  }, [autoRefresh, refreshInterval, refresh]);

  const simulate = async () => {
    if (simulating) return;

    setSimulating(true);

    try {
      const response = await fetch(`${API}/api/simulate`, {
        method: "POST"
      });

      if (!response.ok) throw new Error("Simulation failed");

      await refresh();
    } catch (err) {
      setError("Unable to generate readings.");
    } finally {
      setSimulating(false);
    }
  };

  const collectBin = async bin => {
    if (!window.confirm(
      `Confirm simulated collection for ${bin.name}?`
    )) return;

    setCollectingId(bin.id);

    try {
      const response = await fetch(
        `${API}/api/collect/${bin.id}`,
        { method: "POST" }
      );

      if (!response.ok) throw new Error("Collection failed");

      await refresh();
      alert(`${bin.name} collected successfully.`);
    } catch (err) {
      setError("Unable to complete collection.");
    } finally {
      setCollectingId(null);
    }
  };

  const ordered = useMemo(() =>
    [...bins].sort((a, b) =>
      (rank[b.priority] || 0) - (rank[a.priority] || 0) ||
      b.fill_percent - a.fill_percent
    ), [bins]
  );

  const zones = useMemo(() =>
    ["All", ...new Set(bins.map(b => b.location))],
    [bins]
  );

  const filteredBins = useMemo(() =>
    ordered.filter(b =>
      `${b.name} ${b.location}`
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (zoneFilter === "All" || b.location === zoneFilter)
    ), [ordered, search, zoneFilter]
  );

  const zoneData = useMemo(() => {
    const groups = {};

    bins.forEach(bin => {
      const location = bin.location || "Unknown";
      const zone = location.includes(" - ")
        ? location.split(" - ")[0].trim()
        : location;

      if (!groups[zone]) {
        groups[zone] = { zone, totalFill: 0, bins: 0 };
      }

      groups[zone].totalFill += Number(bin.fill_percent);
      groups[zone].bins += 1;
    });

    return Object.values(groups).map(group => ({
      zone: group.zone,
      averageFill: Number(
        (group.totalFill / group.bins).toFixed(1)
      ),
      bins: group.bins
    }));
  }, [bins]);

  const chartBins = bins.map(b => ({
    name: b.name,
    fill: Number(b.fill_percent),
    weight: Number(b.weight_percent)
  }));

  const priorityData = ["Critical", "High", "Medium", "Low"]
    .map(name => ({
      name,
      value: bins.filter(b => b.priority === name).length
    }));

  const totalWaste = bins.reduce(
    (sum, b) => sum + Number(b.weight_kg), 0
  );

  const avgFill = bins.length
    ? bins.reduce(
        (sum, b) => sum + Number(b.fill_percent), 0
      ) / bins.length
    : 0;

  const critical = bins.filter(
    b => b.priority === "Critical"
  ).length;

  const high = bins.filter(
    b => b.priority === "High"
  ).length;

  const collectedKg = collections.reduce(
    (sum, c) => sum + Number(c.collected_weight_kg || 0),
    0
  );

  const metrics = evaluation?.metrics;
  const comparison = evaluation?.comparison || [];

  const collectionButton = bin => (
    <button
      className="sw-btn sw-primary"
      disabled={
        collectingId === bin.id ||
        (bin.fill_percent <= 0 && bin.weight_kg <= 0)
      }
      onClick={() => collectBin(bin)}
    >
      <Truck size={14} />
      {collectingId === bin.id ? "Collecting..." : "Collect Waste"}
    </button>
  );

  return (
    <div className="sw-app">
      <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; background: #f7f6f2; }
        .sw-app {
          min-height: 100vh;
          display: flex;
          background: #f7f6f2;
          color: #252a28;
          font-family: Arial, Helvetica, sans-serif;
        }
        .sw-sidebar {
          width: 245px;
          min-width: 245px;
          background: #fff;
          border-right: 1px solid #e1e5de;
          padding: 25px 14px;
          position: sticky;
          top: 0;
          height: 100vh;
          overflow-y: auto;
        }
        .sw-brand {
          display: flex;
          gap: 12px;
          align-items: center;
          padding: 5px 12px 28px;
        }
        .sw-brand-icon {
          background: #315c46;
          color: white;
          border-radius: 12px;
          padding: 11px;
          display: flex;
        }
        .sw-brand strong { display: block; font-size: 19px; }
        .sw-brand small { color: #7a837c; font-size: 11px; }
        .sw-nav {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .sw-nav button {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 13px;
          background: transparent;
          border: 0;
          border-radius: 9px;
          text-align: left;
          cursor: pointer;
          color: #647068;
          font-size: 13px;
          font-weight: 600;
        }
        .sw-nav button:hover { background: #f1f4ef; }
        .sw-nav button.active {
          background: #e9f0e9;
          color: #315c46;
        }
        .sw-main {
          flex: 1;
          min-width: 0;
          padding: 25px 32px 60px;
        }
        .sw-topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 30px;
          flex-wrap: wrap;
        }
        .sw-topbar small { color: #78837b; }
        .sw-actions {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          align-items: center;
        }
        .sw-status {
          display: flex;
          gap: 7px;
          align-items: center;
          color: #315c46;
          font-size: 12px;
          font-weight: 700;
        }
        .sw-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #27845b;
        }
        .sw-btn {
          border: 1px solid #d7dfd6;
          background: white;
          color: #315c46;
          border-radius: 8px;
          padding: 10px 13px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          cursor: pointer;
          font-size: 12px;
          font-weight: 700;
          white-space: nowrap;
        }
        .sw-primary {
          background: #315c46;
          border-color: #315c46;
          color: white;
        }
        .sw-btn:disabled { opacity: .45; cursor: not-allowed; }
        .sw-page-title { margin-bottom: 25px; }
        .sw-page-title h2 {
          margin: 0 0 8px;
          font-size: 28px;
          letter-spacing: -.6px;
        }
        .sw-page-title p {
          margin: 0;
          color: #7b847d;
          font-size: 13px;
          line-height: 1.6;
        }
        .sw-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0,1fr));
          gap: 15px;
          margin-bottom: 20px;
        }
        .sw-grid-two {
          display: grid;
          grid-template-columns: repeat(2,minmax(0,1fr));
          gap: 18px;
          margin-bottom: 20px;
        }
        .sw-metric, .sw-panel {
          background: white;
          border: 1px solid #e2e7df;
          border-radius: 12px;
        }
        .sw-metric { padding: 21px; }
        .sw-metric-label {
          display: flex;
          justify-content: space-between;
          color: #7b857c;
          font-size: 12px;
          gap: 8px;
          align-items: center;
        }
        .sw-metric strong {
          display: block;
          font-size: 29px;
          margin: 16px 0 7px;
          letter-spacing: -.5px;
        }
        .sw-metric small { color: #89938a; font-size: 11px; }
        .sw-panel {
          padding: 20px;
          margin-bottom: 20px;
          min-width: 0;
        }
        .sw-panel-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
          margin-bottom: 19px;
          flex-wrap: wrap;
        }
        .sw-panel h3 { margin: 0; font-size: 15px; }
        .sw-chart { width: 100%; height: 300px; }
        .sw-table-wrap { overflow-x: auto; }
        .sw-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
          text-align: left;
        }
        .sw-table th {
          background: #f8faf7;
          color: #78837b;
          padding: 13px;
          font-weight: 700;
          white-space: nowrap;
        }
        .sw-table td {
          padding: 14px 13px;
          border-top: 1px solid #edf0eb;
          white-space: nowrap;
        }
        .sw-table tbody tr:hover { background: #fafbf9; }
        .sw-priority {
          display: inline-block;
          padding: 5px 11px;
          border-radius: 20px;
          font-weight: 700;
          font-size: 12px;
        }
        .sw-progress {
          width: 105px;
          height: 7px;
          background: #e8eee7;
          border-radius: 20px;
          overflow: hidden;
          display: inline-block;
          margin-right: 9px;
          vertical-align: middle;
        }
        .sw-progress span {
          display: block;
          height: 100%;
          background: #315c46;
          border-radius: 20px;
        }
        .sw-muted { color: #7b857d; font-size: 12px; }
        .sw-empty {
          padding: 25px 10px;
          text-align: center;
          color: #89938a;
          font-size: 13px;
        }
        .sw-error {
          padding: 14px;
          color: #9e3535;
          background: #fff0ed;
          border: 1px solid #f1d0ca;
          border-radius: 8px;
          margin-bottom: 18px;
          font-size: 13px;
        }
        .sw-input {
          padding: 10px 12px;
          border: 1px solid #dbe2d9;
          border-radius: 8px;
          background: white;
          min-width: 150px;
          max-width: 100%;
          font-size: 12px;
        }
        .sw-filterbar {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-bottom: 16px;
        }
        .sw-sensor-grid {
          display: grid;
          grid-template-columns: repeat(3,minmax(0,1fr));
          gap: 15px;
        }
        .sw-sensor {
          padding: 18px;
          border: 1px solid #e1e7df;
          border-radius: 10px;
          background: #fafbf9;
        }
        .sw-sensor small {
          display: block;
          color: #7a857d;
          margin: 10px 0;
        }
        .sw-sensor strong { font-size: 22px; }
        .sw-setting {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 17px 0;
          border-bottom: 1px solid #edf0eb;
          gap: 15px;
          flex-wrap: wrap;
        }
        .sw-setting p {
          margin: 5px 0 0;
          color: #7c867d;
          font-size: 12px;
        }
        .sw-reports {
          display: grid;
          grid-template-columns: repeat(2,minmax(0,1fr));
          gap: 15px;
        }
        .sw-report {
          border: 1px solid #e1e7df;
          padding: 18px;
          border-radius: 10px;
        }
        .sw-report p { font-size: 12px; color: #7d877e; }
        .sw-report h4 { margin: 8px 0; }
        @media(max-width:1100px) {
          .sw-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
          .sw-sidebar { width: 215px; min-width: 215px; }
          .sw-main { padding: 22px; }
        }
        @media(max-width:750px) {
          .sw-app { display: block; }
          .sw-sidebar {
            position: static;
            height: auto;
            width: 100%;
            padding: 12px;
            border-right: 0;
            border-bottom: 1px solid #e1e5de;
          }
          .sw-brand { padding-bottom: 10px; }
          .sw-nav { flex-direction: row; overflow-x: auto; }
          .sw-nav button { white-space: nowrap; }
          .sw-main { padding: 18px 13px; }
          .sw-grid-two, .sw-reports { grid-template-columns: 1fr; }
          .sw-sensor-grid { grid-template-columns: 1fr; }
        }
        @media(max-width:460px) {
          .sw-grid { grid-template-columns: 1fr; }
        }
      `}</style>

      <aside className="sw-sidebar">
        <div className="sw-brand">
          <div className="sw-brand-icon">
            <Trash2 size={24} />
          </div>
          <div>
            <strong>SmartWaste AI</strong>
            <small>INDUSTRIAL MONITORING</small>
          </div>
        </div>

        <nav className="sw-nav">
          {NAV.map(([name, Icon]) => (
            <button
              key={name}
              className={page === name ? "active" : ""}
              onClick={() => setPage(name)}
            >
              <Icon size={18} />
              {name}
            </button>
          ))}
        </nav>
      </aside>

      <main className="sw-main">
        <header className="sw-topbar">
          <div>
            <strong>Smart Waste Operations Center</strong>
            <div>
              <small>
                {lastUpdate
                  ? `Last updated: ${lastUpdate.toLocaleTimeString()}`
                  : "Waiting for data"}
              </small>
            </div>
          </div>

          <div className="sw-actions">
            <span className="sw-status">
              <span className="sw-dot" />
              {error ? "Disconnected" : "Live Simulation"}
            </span>

            <button className="sw-btn" onClick={refresh}>
              <RefreshCw size={15} />
              Refresh
            </button>

            <button
              className="sw-btn sw-primary"
              onClick={simulate}
              disabled={simulating}
            >
              <Play size={15} />
              {simulating ? "Generating..." : "Generate Readings"}
            </button>
          </div>
        </header>

        {error && <div className="sw-error">{error}</div>}

        {loading && (
          <p className="sw-empty">Loading SmartWaste AI data...</p>
        )}

        {page === "Dashboard" && (
          <>
            <PageTitle
              title="Operations Dashboard"
              description="Live industrial waste monitoring overview."
            />

            <div className="sw-grid">
              <Metric
                title="Total Smart Bins"
                value={bins.length}
                detail="Virtual sensor devices"
                icon={Trash2}
              />
              <Metric
                title="Average Fill Level"
                value={`${num(avgFill)}%`}
                detail="Across all bins"
                icon={Gauge}
              />
              <Metric
                title="Current Waste Load"
                value={`${num(totalWaste)} kg`}
                detail="Simulated waste weight"
                icon={Weight}
              />
              <Metric
                title="Critical Bins"
                value={critical}
                detail={`${alerts.length} active alerts`}
                icon={AlertTriangle}
              />
            </div>

            <div className="sw-grid-two">
              <Panel title="Fill Level by Smart Bin">
                <div className="sw-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartBins.slice(0, 15)}>
                      <CartesianGrid stroke="#edf0eb" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar
                        dataKey="fill"
                        name="Fill %"
                        fill={COLORS.green}
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Panel>

              <Panel title="Bin Priority Distribution">
                <div className="sw-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={priorityData}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={65}
                        outerRadius={100}
                        label
                      >
                        {priorityData.map(entry => (
                          <Cell
                            key={entry.name}
                            fill={
                              entry.name === "Critical" ? COLORS.red :
                              entry.name === "High" ? COLORS.amber :
                              entry.name === "Medium" ? COLORS.sage :
                              COLORS.green
                            }
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </Panel>
            </div>

            <Panel title="Bins Requiring Attention">
              <DataTable headers={[
                "Bin", "Location", "Fill", "Weight",
                "AI Prediction", "Priority"
              ]}>
                {ordered.slice(0, 8).map(b => (
                  <tr key={b.id}>
                    <td><strong>{b.name}</strong></td>
                    <td>{b.location}</td>
                    <td>{num(b.fill_percent)}%</td>
                    <td>{num(b.weight_kg)} kg</td>
                    <td>
                      {b.days_to_full == null
                        ? "N/A"
                        : `${num(b.days_to_full)} days`}
                    </td>
                    <td><Priority value={b.priority} /></td>
                  </tr>
                ))}
              </DataTable>
            </Panel>
          </>
        )}

        {page === "Bin Monitoring" && (
          <>
            <PageTitle
              title="Bin Monitoring"
              description="Monitor smart bins across industrial locations."
            />

            <div className="sw-filterbar">
              <input
                className="sw-input"
                placeholder="Search bin or location..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
              <select
                className="sw-input"
                value={zoneFilter}
                onChange={e => setZoneFilter(e.target.value)}
              >
                {zones.map(zone => (
                  <option key={zone}>{zone}</option>
                ))}
              </select>
            </div>

            <Panel title={`Smart Bin Registry (${filteredBins.length})`}>
              <DataTable headers={[
                "Bin ID", "Location", "Fill Level",
                "Weight", "Capacity", "Priority"
              ]}>
                {filteredBins.map(b => (
                  <tr key={b.id}>
                    <td><strong>{b.name}</strong></td>
                    <td>{b.location}</td>
                    <td>
                      <span className="sw-progress">
                        <span style={{
                          width: `${Math.min(100, b.fill_percent)}%`
                        }} />
                      </span>
                      {num(b.fill_percent)}%
                    </td>
                    <td>{num(b.weight_kg)} kg</td>
                    <td>{num(b.capacity_kg)} kg</td>
                    <td><Priority value={b.priority} /></td>
                  </tr>
                ))}
              </DataTable>
            </Panel>
          </>
        )}

        {page === "Virtual Sensor Lab" && (
          <>
            <PageTitle
              title="Virtual Sensor Laboratory"
              description="Software-based ESP32, ultrasonic and HX711 sensor monitoring."
            />

            <Panel
              title="Virtual Hardware Status"
              action={
                <button
                  className="sw-btn sw-primary"
                  onClick={simulate}
                  disabled={simulating}
                >
                  <Play size={15} />
                  {simulating ? "Generating..." : "Generate Readings"}
                </button>
              }
            >
              <div className="sw-sensor-grid">
                <div className="sw-sensor">
                  <Cpu size={20} color={COLORS.green} />
                  <small>Virtual ESP32 Controllers</small>
                  <strong>{bins.length}</strong>
                </div>
                <div className="sw-sensor">
                  <Gauge size={20} color={COLORS.green} />
                  <small>Ultrasonic Fill Sensors</small>
                  <strong>{bins.length}</strong>
                </div>
                <div className="sw-sensor">
                  <Weight size={20} color={COLORS.green} />
                  <small>HX711 Weight Sensors</small>
                  <strong>{bins.length}</strong>
                </div>
              </div>
            </Panel>

            <Panel title="Latest Virtual Sensor Readings">
              <DataTable headers={[
                "Device", "Bin", "Distance",
                "Fill", "Weight", "Timestamp"
              ]}>
                {history.slice(0, 30).map(h => (
                  <tr key={h.id}>
                    <td>
                      ESP32-SIM-{String(h.bin_id).padStart(3, "0")}
                    </td>
                    <td>{h.name || `SW-${h.bin_id}`}</td>
                    <td>{num(100 - h.fill_percent)} cm</td>
                    <td>{num(h.fill_percent)}%</td>
                    <td>{num(h.weight_kg)} kg</td>
                    <td>{h.timestamp}</td>
                  </tr>
                ))}
              </DataTable>
            </Panel>
          </>
        )}

        {page === "AI Predictions" && (
          <>
            <PageTitle
              title="AI Prediction Engine"
              description="Random Forest predictions for estimated time until bins become full."
            />

            {metrics && (
              <>
                <div className="sw-grid">
                  <Metric
                    title="Training Samples"
                    value={metrics.training_samples}
                    detail="Training dataset"
                    icon={BrainCircuit}
                  />
                  <Metric
                    title="Testing Samples"
                    value={metrics.testing_samples}
                    detail="Evaluation dataset"
                    icon={Activity}
                  />
                  <Metric
                    title="Mean Absolute Error"
                    value={`${metrics.mae_days} days`}
                    detail="Lower is better"
                    icon={Gauge}
                  />
                  <Metric
                    title="R² Score"
                    value={metrics.r2_score}
                    detail="Higher is better"
                    icon={CheckCircle2}
                  />
                </div>

                <Panel title="AI Model Evaluation — Predicted vs Actual">
                  <div className="sw-chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={comparison}>
                        <CartesianGrid stroke="#edf0eb" />
                        <XAxis dataKey="sample" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="actual"
                          stroke={COLORS.sage}
                          strokeWidth={2}
                          dot={false}
                          name="Actual Days"
                        />
                        <Line
                          type="monotone"
                          dataKey="predicted"
                          stroke={COLORS.green}
                          strokeWidth={2}
                          dot={false}
                          name="Predicted Days"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="sw-muted">
                    Evaluation uses held-out synthetic test data.
                  </p>
                </Panel>
              </>
            )}

            <Panel title="Live Time-to-Full Predictions">
              <DataTable headers={[
                "Bin", "Location", "Current Fill",
                "Daily Growth", "Days to Full", "Priority"
              ]}>
                {ordered.map(b => (
                  <tr key={b.id}>
                    <td><strong>{b.name}</strong></td>
                    <td>{b.location}</td>
                    <td>{num(b.fill_percent)}%</td>
                    <td>{num(b.daily_growth)}%/day</td>
                    <td>
                      <strong>
                        {b.days_to_full == null
                          ? "N/A"
                          : `${num(b.days_to_full)} days`}
                      </strong>
                    </td>
                    <td><Priority value={b.priority} /></td>
                  </tr>
                ))}
              </DataTable>
            </Panel>
          </>
        )}

        {page === "Alerts" && (
          <>
            <PageTitle
              title="Smart Alerts"
              description="Automatic alerts based on fill and weight thresholds."
            />

            <div className="sw-grid">
              <Metric
                title="Active Alerts"
                value={alerts.length}
                detail="Threshold violations"
                icon={AlertTriangle}
              />
              <Metric
                title="Critical Bins"
                value={critical}
                detail="Immediate attention"
                icon={CheckCircle2}
              />
              <Metric
                title="High Priority Bins"
                value={high}
                detail="Collection recommended"
                icon={Activity}
              />
              <Metric
                title="Monitored Devices"
                value={bins.length}
                detail="Virtual sensor nodes"
                icon={Cpu}
              />
            </div>

            <Panel title="Active Alert Register">
              <DataTable headers={[
                "Bin", "Alert Type", "Description", "Priority"
              ]}>
                {alerts.map((a, i) => (
                  <tr key={i}>
                    <td><strong>{a.bin || a.name}</strong></td>
                    <td>{a.type}</td>
                    <td>{a.message}</td>
                    <td><Priority value={a.priority} /></td>
                  </tr>
                ))}
              </DataTable>
              {!alerts.length && (
                <p className="sw-empty">No active alerts.</p>
              )}
            </Panel>
          </>
        )}

        {page === "Analytics" && (
          <>
            <PageTitle
              title="Industrial Analytics"
              description="Waste distribution and sensor performance."
            />

            <div className="sw-grid-two">
              <Panel title="Average Fill by Industrial Zone">
                <div className="sw-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={zoneData}>
                      <CartesianGrid stroke="#edf0eb" vertical={false} />
                      <XAxis
                        dataKey="zone"
                        tick={{ fontSize: 10 }}
                        interval={0}
                        angle={-20}
                        height={75}
                      />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar
                        dataKey="averageFill"
                        name="Average Fill %"
                        fill={COLORS.green}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Panel>

              <Panel title="Fill vs Weight Utilization">
                <div className="sw-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartBins.slice(0, 12)}>
                      <CartesianGrid stroke="#edf0eb" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <Bar
                        dataKey="fill"
                        name="Fill %"
                        fill={COLORS.green}
                      />
                      <Bar
                        dataKey="weight"
                        name="Weight %"
                        fill={COLORS.sage}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Panel>
            </div>

            <Panel title="Recent Sensor Data">
              <DataTable headers={[
                "Reading ID", "Bin", "Fill", "Weight", "Timestamp"
              ]}>
                {history.slice(0, 40).map(h => (
                  <tr key={h.id}>
                    <td>RD-{h.id}</td>
                    <td>{h.name || `SW-${h.bin_id}`}</td>
                    <td>{num(h.fill_percent)}%</td>
                    <td>{num(h.weight_kg)} kg</td>
                    <td>{h.timestamp}</td>
                  </tr>
                ))}
              </DataTable>
            </Panel>
          </>
        )}

        {page === "Collection Planning" && (
          <>
            <PageTitle
              title="Smart Collection Management"
              description="Prioritize waste collection using AI predictions."
            />

            <div className="sw-grid">
              <Metric
                title="Monitored Bins"
                value={bins.length}
                detail="Available collection points"
                icon={Truck}
              />
              <Metric
                title="Urgent Bins"
                value={critical + high}
                detail="Critical and high priority"
                icon={AlertTriangle}
              />
              <Metric
                title="Completed Collections"
                value={collections.length}
                detail="Recent saved records"
                icon={CheckCircle2}
              />
              <Metric
                title="Collected Waste"
                value={`${num(collectedKg)} kg`}
                detail="From loaded collection history"
                icon={Weight}
              />
            </div>

            <Panel title="Priority-Based Collection Queue">
              <DataTable headers={[
                "Bin ID", "Location", "Fill",
                "Weight", "Priority", "Action"
              ]}>
                {ordered.map(b => (
                  <tr key={b.id}>
                    <td><strong>{b.name}</strong></td>
                    <td>{b.location}</td>
                    <td>{num(b.fill_percent)}%</td>
                    <td>{num(b.weight_kg)} kg</td>
                    <td><Priority value={b.priority} /></td>
                    <td>{collectionButton(b)}</td>
                  </tr>
                ))}
              </DataTable>
            </Panel>

            <Panel
              title="Completed Collection History"
              action={
                <button
                  className="sw-btn"
                  onClick={() =>
                    downloadCSV("SmartWaste_Collections.csv", collections)
                  }
                >
                  <Download size={15} /> Export
                </button>
              }
            >
              <DataTable headers={[
                "Collection ID", "Bin", "Location",
                "Previous Fill", "Collected Weight", "Timestamp"
              ]}>
                {collections.map(c => (
                  <tr key={c.id}>
                    <td>
                      COL-{String(c.id).padStart(4, "0")}
                    </td>
                    <td><strong>{c.name}</strong></td>
                    <td>{c.location}</td>
                    <td>{num(c.previous_fill)}%</td>
                    <td>{num(c.collected_weight_kg)} kg</td>
                    <td>{c.collected_at}</td>
                  </tr>
                ))}
              </DataTable>
              {!collections.length && (
                <p className="sw-empty">
                  No collections recorded yet.
                </p>
              )}
            </Panel>
          </>
        )}

        {page === "Reports" && (
          <>
            <PageTitle
              title="Reports & Data Export"
              description="Download operational and AI reports."
            />

            <Panel title="Export Center">
              <div className="sw-reports">
                {[
                  {
                    title: "Smart Bin Inventory",
                    description: "Bin levels, capacities and priorities",
                    filename: "SmartWaste_Bins.csv",
                    data: bins
                  },
                  {
                    title: "Sensor Reading History",
                    description: "Latest virtual sensor measurements",
                    filename: "SmartWaste_Readings.csv",
                    data: history
                  },
                  {
                    title: "Collection History",
                    description: "Completed collection records",
                    filename: "SmartWaste_Collections.csv",
                    data: collections
                  },
                  {
                    title: "AI Prediction Report",
                    description: "Estimated time to full",
                    filename: "SmartWaste_Predictions.csv",
                    data: bins.map(b => ({
                      bin: b.name,
                      location: b.location,
                      fill_percent: b.fill_percent,
                      days_to_full: b.days_to_full,
                      priority: b.priority
                    }))
                  },
                  {
                    title: "AI Evaluation",
                    description: "Synthetic predicted vs actual values",
                    filename: "SmartWaste_ML_Evaluation.csv",
                    data: comparison
                  },
                  {
                    title: "Active Alerts",
                    description: "Current threshold violations",
                    filename: "SmartWaste_Alerts.csv",
                    data: alerts
                  }
                ].map(report => (
                  <div className="sw-report" key={report.title}>
                    <Download size={20} color={COLORS.green} />
                    <h4>{report.title}</h4>
                    <p>{report.description}</p>
                    <button
                      className="sw-btn sw-primary"
                      onClick={() =>
                        downloadCSV(report.filename, report.data)
                      }
                    >
                      <Download size={14} /> Download CSV
                    </button>
                  </div>
                ))}
              </div>
            </Panel>
          </>
        )}

        {page === "Settings" && (
          <>
            <PageTitle
              title="System Settings"
              description="Configure live monitoring preferences."
            />

            <Panel title="Live Monitoring Preferences">
              <div className="sw-setting">
                <div>
                  <strong>Automatic Dashboard Refresh</strong>
                  <p>Fetch updated readings periodically.</p>
                </div>
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={e => setAutoRefresh(e.target.checked)}
                />
              </div>

              <div className="sw-setting">
                <div>
                  <strong>Refresh Interval</strong>
                  <p>How frequently the website fetches data.</p>
                </div>
                <select
                  className="sw-input"
                  value={refreshInterval}
                  onChange={e =>
                    setRefreshInterval(Number(e.target.value))
                  }
                >
                  <option value={5}>5 seconds</option>
                  <option value={10}>10 seconds</option>
                  <option value={15}>15 seconds</option>
                  <option value={30}>30 seconds</option>
                  <option value={60}>60 seconds</option>
                </select>
              </div>
            </Panel>

            <Panel title="System Architecture">
              {[
                ["Frontend", "React + Vite"],
                ["Backend", "Python + Flask"],
                ["Database", "SQLite"],
                ["AI Model", "Random Forest Regressor"],
                ["Virtual Hardware", "ESP32 + Ultrasonic + HX711"],
                ["Backend Address", API],
                ["Data Source", "Software simulation"]
              ].map(([name, value]) => (
                <div className="sw-setting" key={name}>
                  <strong>{name}</strong>
                  <span className="sw-muted">{value}</span>
                </div>
              ))}
            </Panel>
          </>
        )}
      </main>
    </div>
  );
}
