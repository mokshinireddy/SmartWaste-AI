
from pathlib import Path

root = Path("frontend/src")
root.mkdir(parents=True, exist_ok=True)

files = {
"main.jsx": r'''
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode><App /></React.StrictMode>
);
''',

"App.jsx": r'''
import React, {useState,useEffect,useCallback} from "react";
import {
 LayoutDashboard, Trash2, Cpu, BrainCircuit, Bell,
 BarChart3, Truck, FileDown, Settings, RefreshCw,
 Search, AlertTriangle, Activity, Menu, X, CheckCircle2
} from "lucide-react";
import {
 ResponsiveContainer, AreaChart, Area, CartesianGrid,
 XAxis, YAxis, Tooltip, BarChart, Bar, PieChart,
 Pie, Cell
} from "recharts";

const API="http://127.0.0.1:5000";
const nav=[
 ["Dashboard",LayoutDashboard],["Bin Monitoring",Trash2],
 ["Virtual Sensor Lab",Cpu],["AI Predictions",BrainCircuit],
 ["Alerts",Bell],["Analytics",BarChart3],
 ["Collection Planning",Truck],["Reports",FileDown],
 ["Settings",Settings]
];
const colors=["#315c46","#82a68b","#d3a15c","#c36d60"];
const num=(n,d=1)=>Number(n||0).toFixed(d);
const priorityColor=p=>p==="Critical"?"red":p==="High"?"orange":p==="Medium"?"blue":"green";

function exportCSV(rows,name){
 if(!rows.length)return;
 const keys=Object.keys(rows[0]);
 const csv=[keys.join(","),...rows.map(r=>keys.map(k=>
  `"${String(r[k]??"").replaceAll('"','""')}"`
 ).join(","))].join("\n");
 const a=document.createElement("a");
 a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));
 a.download=name;a.click();URL.revokeObjectURL(a.href);
}

function Panel({title,children,action}){
 return <section className="panel">
  <div className="panelhead"><h3>{title}</h3>{action}</div>{children}
 </section>;
}
function Metric({title,value,detail,icon:Icon}){
 return <div className="metric">
  <div className="metric-top"><span>{title}</span><Icon size={19}/></div>
  <strong>{value}</strong><small>{detail}</small>
 </div>;
}
function Tag({value}){
 return <span className={"tag "+priorityColor(value)}>{value}</span>;
}
function Progress({value}){
 return <div className="track"><div className="fill"
 style={{width:`${Math.min(100,Math.max(0,value||0))}%`,
 background:value>=90?"#c36d60":value>=75?"#d3a15c":"#477a60"}}/></div>;
}

export default function App(){
 const [page,setPage]=useState("Dashboard");
 const [bins,setBins]=useState([]);
 const [dashboard,setDashboard]=useState({});
 const [alerts,setAlerts]=useState([]);
 const [history,setHistory]=useState([]);
 const [loading,setLoading]=useState(true);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [search,setSearch]=useState("");
 const [filter,setFilter]=useState("All");
 const [menu,setMenu]=useState(false);
 const [auto,setAuto]=useState(false);
 const [intervalSeconds,setIntervalSeconds]=useState(15);
 const [lastUpdate,setLastUpdate]=useState(null);

 const refresh=useCallback(async()=>{
  try{
   const paths=["/api/dashboard","/api/alerts","/api/history"];
   const responses=await Promise.all(paths.map(p=>fetch(API+p)));
   if(responses.some(r=>!r.ok))throw Error("API request failed");
   const [d,a,h]=await Promise.all(responses.map(r=>r.json()));
   setDashboard(d);setBins(d.bins||[]);setAlerts(a);
   setHistory(h);setError("");setLastUpdate(new Date());
  }catch(e){setError("Cannot connect to Flask. Start backend/app.py on port 5000.");}
  finally{setLoading(false);}
 },[]);

 const simulate=useCallback(async()=>{
  setBusy(true);
  try{
   const r=await fetch(API+"/api/simulate",{method:"POST"});
   if(!r.ok)throw Error("Simulation failed");
   await refresh();
  }catch(e){setError("Simulation failed. Check the Flask server.");}
  finally{setBusy(false);}
 },[refresh]);

 useEffect(()=>{refresh();},[refresh]);
 useEffect(()=>{
  if(!auto)return;
  const timer=setInterval(simulate,intervalSeconds*1000);
  return()=>clearInterval(timer);
 },[auto,intervalSeconds,simulate]);

 const filtered=bins.filter(b=>
  (filter==="All"||b.priority===filter)&&
  `${b.name} ${b.location}`.toLowerCase().includes(search.toLowerCase())
 );
 const ordered=[...bins].sort((a,b)=>
  ["Critical","High","Medium","Low"].indexOf(a.priority)-
  ["Critical","High","Medium","Low"].indexOf(b.priority)
 );
 const avgWeight=bins.length?bins.reduce((s,b)=>s+b.weight_percent,0)/bins.length:0;
 const chartData=bins.map(b=>({name:b.name,fill:b.fill_percent,weight:b.weight_percent}));
 const distribution=["Critical","High","Medium","Low"].map((p,i)=>({
  name:p,value:bins.filter(b=>b.priority===p).length,color:colors[[3,2,1,0][i]]
 }));
 const zones=[...new Set(bins.map(b=>b.location.split(" - ")[0]))];
 const zoneData=zones.map(z=>{
  const group=bins.filter(b=>b.location.startsWith(z));
  return {name:z,fill:group.reduce((s,b)=>s+b.fill_percent,0)/group.length};
 });

 const binTable=<div className="tablewrap"><table>
  <thead><tr><th>Device</th><th>Location</th><th>Fill level</th>
  <th>Weight</th><th>AI forecast</th><th>Priority</th></tr></thead>
  <tbody>{filtered.map(b=><tr key={b.id}>
   <td><b>{b.name}</b><small>ESP32-SIM-{String(b.id).padStart(3,"0")}</small></td>
   <td>{b.location}</td>
   <td><div className="cellprogress">{num(b.fill_percent)}%<Progress value={b.fill_percent}/></div></td>
   <td>{num(b.weight_kg)} / {b.capacity_kg} kg</td>
   <td>{b.days_to_full===null?"N/A":`${num(b.days_to_full)} days`}</td>
   <td><Tag value={b.priority}/></td>
  </tr>)}</tbody></table>
  {!filtered.length&&<p className="empty">No matching bins found.</p>}
 </div>;

 function chart(title,data,key,type="bar"){
  return <Panel title={title}><div className="chart">
   <ResponsiveContainer width="100%" height="100%">
    {type==="area"?
     <AreaChart data={data}><CartesianGrid stroke="#e6e9e3" vertical={false}/>
      <XAxis dataKey="name" tick={{fontSize:10}}/><YAxis/>
      <Tooltip/><Area type="monotone" dataKey={key} stroke="#315c46"
      fill="#d9e9dc"/></AreaChart>:
     <BarChart data={data}><CartesianGrid stroke="#e6e9e3" vertical={false}/>
      <XAxis dataKey="name" tick={{fontSize:10}} interval={data.length>12?3:0}/>
      <YAxis/><Tooltip/><Bar dataKey={key} fill="#477a60" radius={[4,4,0,0]}/></BarChart>}
   </ResponsiveContainer>
  </div></Panel>;
 }

 return <div className="shell">
  <aside className={"sidebar "+(menu?"show":"")}>
   <div className="brand"><div className="brandmark"><Trash2 size={21}/></div>
    <div><b>SmartWaste AI</b><small>INDUSTRIAL INTELLIGENCE</small></div>
    <button className="mobileclose" onClick={()=>setMenu(false)}><X/></button>
   </div>
   <div className="navlabel">WORKSPACE</div>
   <nav>{nav.map(([name,Icon])=><button key={name}
    className={page===name?"active":""}
    onClick={()=>{setPage(name);setMenu(false);}}>
    <Icon size={18}/><span>{name}</span>
    {name==="Alerts"&&alerts.length>0&&<em>{alerts.length}</em>}
   </button>)}</nav>
   <div className="sidebarbottom"><span className="online"/> Simulation environment
    <small>Virtual ESP32 network · v1.0</small></div>
  </aside>

  <main className="main">
   <header className="topbar">
    <button className="hamburger" onClick={()=>setMenu(!menu)}><Menu/></button>
    <div className="breadcrumb">Workspace <span>/</span> {page}</div>
    <div className="topactions">
     <span className="simulation-label"><span className="online"/> SIMULATION MODE</span>
     <button className="iconbutton" onClick={refresh} title="Refresh"><RefreshCw size={18}/></button>
    </div>
   </header>
   <div className="content">
    <div className="pageheading"><div>
     <div className="eyebrow">SMART WASTE MANAGEMENT PLATFORM</div>
     <h1>{page}</h1>
     <p>{page==="Dashboard"?"Industrial waste intelligence and predictive monitoring":
      "Virtual IoT monitoring and intelligent waste operations"}</p>
    </div>
    <button className="primary" onClick={simulate} disabled={busy}>
     <RefreshCw size={16}/>{busy?"Simulating...":"Generate Readings"}
    </button></div>

    {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}
    {loading?<div className="empty">Loading industrial monitoring data...</div>:<>
    {page==="Dashboard"&&<>
     <div className="metrics">
      <Metric title="Connected Virtual Bins" value={dashboard.total_bins||0}
       detail="ESP32 simulated nodes" icon={Cpu}/>
      <Metric title="Average Fill Level" value={num(dashboard.average_fill)+"%"}
       detail="Across all monitored bins" icon={Activity}/>
      <Metric title="Total Waste Load" value={num(dashboard.total_waste_kg)+" kg"}
       detail="Simulated load cell readings" icon={Trash2}/>
      <Metric title="Critical Bins" value={dashboard.critical_bins||0}
       detail="Require collection attention" icon={AlertTriangle}/>
     </div>
     <div className="twocol">
      {chart("Bin Fill Levels",chartData,"fill")}
      <Panel title="Collection Priority Distribution">
       <div className="chart"><ResponsiveContainer width="100%" height="100%">
        <PieChart><Pie data={distribution} dataKey="value" nameKey="name"
         innerRadius={65} outerRadius={95} paddingAngle={3}>
         {distribution.map((d,i)=><Cell key={i} fill={d.color}/>)}
        </Pie><Tooltip/><React.Fragment>{null}</React.Fragment></PieChart>
       </ResponsiveContainer></div>
       <div className="legend">{distribution.map(d=><span key={d.name}>
        <i style={{background:d.color}}/>{d.name}: {d.value}</span>)}</div>
      </Panel>
     </div>
     <Panel title="Priority Collection Queue">
      <div className="queue">{ordered.slice(0,6).map(b=><div key={b.id} className="queueitem">
       <div><b>{b.name}</b><small>{b.location}</small></div>
       <div><strong>{num(b.fill_percent)}%</strong><Tag value={b.priority}/></div>
      </div>)}</div>
     </Panel>
    </>}

    {page==="Bin Monitoring"&&<>
     <div className="toolbar">
      <div className="search"><Search size={18}/><input value={search}
       onChange={e=>setSearch(e.target.value)} placeholder="Search device or location"/></div>
      <select value={filter} onChange={e=>setFilter(e.target.value)}>
       {["All","Critical","High","Medium","Low"].map(x=><option key={x}>{x}</option>)}
      </select>
     </div>
     <Panel title={`${filtered.length} Monitored Devices`}>{binTable}</Panel>
    </>}

    {page==="Virtual Sensor Lab"&&<>
     <div className="metrics">
      <Metric title="Virtual ESP32 Devices" value={bins.length} detail="Simulated nodes" icon={Cpu}/>
      <Metric title="Ultrasonic Sensors" value={bins.length} detail="Virtual distance measurements" icon={Activity}/>
      <Metric title="HX711 Load Cells" value={bins.length} detail="Virtual weight measurements" icon={Trash2}/>
      <Metric title="Simulation State" value={auto?"Active":"Manual"} detail="No physical hardware" icon={CheckCircle2}/>
     </div>
     <Panel title="Simulation Control Center">
      <p className="muted">Generate synthetic readings from virtual ESP32 devices.
       Values are stored in SQLite and processed by the Flask API.</p>
      <div className="controls">
       <button className="primary" onClick={simulate} disabled={busy}>Generate Sensor Cycle</button>
       <label><input type="checkbox" checked={auto} onChange={e=>setAuto(e.target.checked)}/> Automatic simulation</label>
       <label>Interval <select value={intervalSeconds} onChange={e=>setIntervalSeconds(Number(e.target.value))}>
        {[5,10,15,30,60].map(s=><option key={s} value={s}>{s} seconds</option>)}
       </select></label>
      </div>
     </Panel>
     <Panel title="Virtual Sensor Telemetry">
      <div className="tablewrap"><table><thead><tr><th>ESP32 Device</th><th>Ultrasonic Distance</th>
       <th>HX711 Weight</th><th>Fill Level</th></tr></thead><tbody>
       {bins.map(b=><tr key={b.id}><td>{b.name}</td><td>{num(b.distance_cm)} cm</td>
        <td>{num(b.weight_kg)} kg</td><td>{num(b.fill_percent)}%</td></tr>)}
       </tbody></table></div>
     </Panel>
    </>}

    {page==="AI Predictions"&&<>
     <div className="notice"><BrainCircuit size={19}/>
      Random Forest regression trained on synthetic fill-level and growth-rate data.
      Predictions are estimates for demonstration, not field-validated forecasts.</div>
     <Panel title="Predictive Collection Intelligence">
      <div className="tablewrap"><table><thead><tr><th>Bin</th><th>Location</th>
       <th>Fill Level</th><th>Daily Growth</th><th>Time to Full</th><th>Priority</th>
       </tr></thead><tbody>{ordered.map(b=><tr key={b.id}>
       <td><b>{b.name}</b></td><td>{b.location}</td>
       <td>{num(b.fill_percent)}%</td><td>{num(b.daily_growth)}% / day</td>
       <td><b>{b.days_to_full===null?"N/A":num(b.days_to_full)+" days"}</b></td>
       <td><Tag value={b.priority}/></td>
       </tr>)}</tbody></table></div>
     </Panel>
    </>}

    {page==="Alerts"&&<>
     <div className="notice"><Bell size={19}/> Alerts are generated automatically
      when simulated fill level or weight capacity reaches 75%.</div>
     <div className="alertgrid">{alerts.length?alerts.map((a,i)=>
      <div className="alertcard" key={i}>
       <div className="alerticon"><AlertTriangle size={20}/></div>
       <div><b>{a.bin} · {a.type}</b><p>{a.message}</p><Tag value={a.priority}/></div>
      </div>):<div className="empty">No active threshold alerts.</div>}</div>
    </>}

    {page==="Analytics"&&<>
     <div className="metrics">
      <Metric title="Total Devices" value={bins.length} detail="Across monitoring zones" icon={Cpu}/>
      <Metric title="Average Weight Capacity" value={num(avgWeight)+"%"} detail="Current utilization" icon={Activity}/>
      <Metric title="Historical Readings" value={history.length} detail="Latest 100 records" icon={BarChart3}/>
      <Metric title="Monitoring Zones" value={zones.length} detail="Derived from location labels" icon={LayoutDashboard}/>
     </div>
     <div className="twocol">
      {chart("Average Fill by Zone",zoneData,"fill")}
      {chart("Weight Utilization by Bin",chartData,"weight")}
     </div>
     <Panel title="Latest Sensor History"><div className="tablewrap"><table>
      <thead><tr><th>Bin</th><th>Fill</th><th>Weight</th><th>Timestamp</th></tr></thead>
      <tbody>{history.slice(0,25).map(h=><tr key={h.id}>
       <td>{h.name}</td><td>{num(h.fill_percent)}%</td>
       <td>{num(h.weight_kg)} kg</td><td>{h.timestamp}</td>
      </tr>)}</tbody></table></div></Panel>
    </>}

    {page==="Collection Planning"&&<>
     <div className="notice"><Truck size={19}/> Collection priority is determined
      by fill percentage, weight utilization and predicted time to full.</div>
     <Panel title="Recommended Collection Order"><div className="queue">
      {ordered.map((b,i)=><div className="queueitem" key={b.id}>
       <div className="rank">{String(i+1).padStart(2,"0")}</div>
       <div><b>{b.name}</b><small>{b.location}</small></div>
       <div><strong>{num(b.fill_percent)}% full</strong><Tag value={b.priority}/></div>
      </div>)}</div></Panel>
    </>}

    {page==="Reports"&&<>
     <div className="reportgrid">
      <Panel title="Device Inventory Report"><p>Export all simulated smart bin
       readings, utilization and prediction data.</p>
       <button className="primary" onClick={()=>exportCSV(bins,"smartwaste-bins.csv")}>
       <FileDown size={16}/> Export CSV</button></Panel>
      <Panel title="Sensor History Report"><p>Export the latest 100 stored
       virtual sensor readings.</p>
       <button className="primary" onClick={()=>exportCSV(history,"smartwaste-history.csv")}>
       <FileDown size={16}/> Export CSV</button></Panel>
      <Panel title="Alerts Report"><p>Export current fill-level and weight
       threshold warnings.</p>
       <button className="primary" onClick={()=>exportCSV(alerts,"smartwaste-alerts.csv")}>
       <FileDown size={16}/> Export CSV</button></Panel>
     </div>
    </>}

    {page==="Settings"&&<>
     <Panel title="Simulation Preferences">
      <div className="settingrow"><div><b>Automatic sensor simulation</b>
       <small>Generate readings periodically while the website is open</small></div>
       <input type="checkbox" checked={auto} onChange={e=>setAuto(e.target.checked)}/></div>
      <div className="settingrow"><div><b>Simulation interval</b>
       <small>Frequency of virtual sensor cycles</small></div>
       <select value={intervalSeconds} onChange={e=>setIntervalSeconds(Number(e.target.value))}>
        {[5,10,15,30,60].map(s=><option key={s} value={s}>{s} seconds</option>)}
       </select></div>
      <div className="settingrow"><div><b>Backend API</b>
       <small>Flask development server</small></div><code>{API}</code></div>
      <div className="settingrow"><div><b>Data source</b>
       <small>Virtual sensors, SQLite and synthetic ML training data</small></div>
       <span className="tag green">SIMULATED</span></div>
     </Panel>
    </>}
    </>}
    <footer>SmartWaste AI · Industrial Monitoring Platform ·
     Simulation Only · {lastUpdate?`Last synced ${lastUpdate.toLocaleTimeString()}`:"Waiting for data"}</footer>
   </div>
  </main>
 </div>;
}
''',

"index.css": r'''
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{font-family:'DM Sans',sans-serif;color:#25352d;background:#f7f8f5;font-synthesis:none}
*{box-sizing:border-box}body{margin:0}button,input,select{font:inherit}
button{cursor:pointer}h1,h2,h3,p{margin-top:0}h1,h3,b,strong{font-family:Manrope,sans-serif}
.shell{display:flex;min-height:100vh}.sidebar{width:255px;background:#fff;border-right:1px solid #e5eae4;position:fixed;inset:0 auto 0 0;display:flex;flex-direction:column;z-index:5}
.brand{display:flex;align-items:center;gap:11px;padding:29px 20px 35px}.brandmark{background:#315c46;color:white;padding:11px;border-radius:12px;display:flex}.brand b{font-size:17px;letter-spacing:-.5px}.brand small{display:block;font-size:9px;letter-spacing:1.5px;color:#859188;margin-top:5px}
.navlabel{padding:0 25px 13px;font-size:10px;letter-spacing:1.5px;color:#98a39b;font-weight:700}
nav{padding:0 12px;display:flex;flex-direction:column;gap:4px;overflow-y:auto}
nav button{border:0;background:transparent;text-align:left;padding:13px 14px;display:flex;align-items:center;gap:13px;color:#68766d;border-radius:8px;font-size:13px;font-weight:600}
nav button:hover{background:#f3f6f2}nav button.active{background:#eaf2ec;color:#315c46}
nav em{margin-left:auto;background:#c36d60;color:white;border-radius:12px;padding:2px 7px;font-style:normal;font-size:10px}
.sidebarbottom{margin-top:auto;padding:22px;font-size:12px;border-top:1px solid #edf0eb;color:#4c6856}.sidebarbottom small{display:block;margin-top:7px;color:#8a958d}
.online{display:inline-block;width:8px;height:8px;background:#4b9a67;border-radius:50%;margin-right:7px}
.main{margin-left:255px;flex:1;min-width:0}.topbar{height:72px;background:#fff;border-bottom:1px solid #e5eae4;display:flex;align-items:center;justify-content:space-between;padding:0 35px}
.breadcrumb{font-size:13px;color:#5c6b60}.breadcrumb span{color:#b6c0b7;margin:0 9px}.topactions{display:flex;align-items:center;gap:22px}.simulation-label{font-size:10px;letter-spacing:1px;font-weight:700;color:#477a60}
.iconbutton,.hamburger,.mobileclose{background:none;border:0;color:#5b6d60}.hamburger,.mobileclose{display:none}
.content{max-width:1600px;margin:auto;padding:35px}.pageheading{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:28px}
.eyebrow{font-size:10px;font-weight:800;letter-spacing:1.8px;color:#789280;margin-bottom:10px}.pageheading h1{font-size:29px;letter-spacing:-1.1px;margin:0 0 7px}.pageheading p{color:#89958b;font-size:13px;margin:0}
.primary{background:#315c46;border:1px solid #315c46;color:white;padding:12px 17px;border-radius:8px;font-size:12px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;gap:9px}
.primary:hover{background:#244c36}.primary:disabled{opacity:.55}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:17px;margin-bottom:20px}
.metric,.panel,.alertcard{background:white;border:1px solid #e7ece5;border-radius:11px}
.metric{padding:22px}.metric-top{display:flex;justify-content:space-between;align-items:center;color:#7e8d82;font-size:12px;font-weight:600}
.metric-top svg{color:#74947d}.metric strong{display:block;font-size:30px;margin:16px 0 8px;letter-spacing:-1px}.metric small{color:#9aa59c;font-size:11px}
.twocol{display:grid;grid-template-columns:1.4fr 1fr;gap:20px;margin-bottom:20px}.panel{padding:22px;margin-bottom:20px;min-width:0}
.panelhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.panel h3{font-size:14px;margin:0}.chart{height:265px;min-width:0}
.legend{display:flex;justify-content:center;flex-wrap:wrap;gap:14px;font-size:11px;color:#69796c}.legend i{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:6px}
.queueitem{display:flex;align-items:center;gap:15px;padding:14px 0;border-bottom:1px solid #edf0eb}.queueitem:last-child{border:0}
.queueitem>div:nth-last-child(2){flex:1}.queueitem b{display:block;font-size:12px}.queueitem small,td small{display:block;color:#9aa69c;font-size:11px;margin-top:5px}
.queueitem>div:last-child{text-align:right;display:flex;align-items:center;gap:15px}.queueitem strong{font-size:12px}
.tag{font-size:10px;font-weight:800;padding:6px 10px;border-radius:5px;display:inline-block}
.tag.red{background:#fae8e5;color:#b24b41}.tag.orange{background:#fff1d9;color:#a97528}
.tag.blue{background:#e8eff9;color:#55749b}.tag.green{background:#e8f4eb;color:#408259}
.toolbar{display:flex;gap:12px;margin-bottom:20px}.search{display:flex;align-items:center;gap:9px;background:white;border:1px solid #e3e9e1;padding:0 13px;border-radius:8px;flex:1}
.search input{border:0;outline:0;width:100%;padding:12px 0}.toolbar select,.controls select,.settingrow select{border:1px solid #dce5da;background:white;border-radius:7px;padding:10px;color:#425a48}
.tablewrap{overflow-x:auto}table{width:100%;border-collapse:collapse;white-space:nowrap;text-align:left}th{background:#f7f9f6;color:#7d8d81;font-size:10px;letter-spacing:.6px;text-transform:uppercase}
th,td{padding:14px 15px;border-bottom:1px solid #edf0eb}td{font-size:12px;color:#4f6254}td b{color:#283e2f}
.cellprogress{min-width:110px}.track{height:5px;background:#edf1ec;border-radius:5px;margin-top:8px;overflow:hidden}.fill{height:100%;border-radius:5px}
.notice{display:flex;align-items:center;gap:13px;padding:17px 20px;background:#eaf2ec;border:1px solid #d8e8db;border-radius:9px;color:#426b4d;font-size:12px;margin-bottom:20px;line-height:1.6}
.alertgrid,.reportgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.alertcard{display:flex;gap:15px;padding:20px}.alerticon{color:#c36d60;background:#fcece9;padding:11px;border-radius:9px;height:max-content}
.alertcard b{font-size:13px}.alertcard p{color:#829085;font-size:12px;margin:9px 0}
.reportgrid .panel p,.muted{font-size:13px;color:#819084;line-height:1.8}
.controls{display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin-top:20px;font-size:12px}
.controls label{display:flex;align-items:center;gap:8px}.settingrow{display:flex;justify-content:space-between;align-items:center;gap:20px;border-bottom:1px solid #edf0eb;padding:20px 0}
.settingrow:last-child{border:0}.settingrow b{display:block;font-size:13px}.settingrow small{display:block;color:#93a097;margin-top:7px;font-size:11px}
.rank{font-weight:800;color:#94a99a;font-size:14px;width:28px}.error{background:#fff0ed;color:#b34c43;border:1px solid #f3c7c1;padding:15px;margin-bottom:20px;border-radius:8px;font-size:13px;display:flex;gap:10px}
.empty{padding:30px;text-align:center;color:#9ba69e;font-size:13px}
footer{padding:25px 0;color:#a2ada4;font-size:11px;text-align:center}
@media(max-width:1150px){.metrics{grid-template-columns:repeat(2,1fr)}.twocol{grid-template-columns:1fr}}
@media(max-width:760px){.sidebar{transform:translateX(-100%);transition:transform .2s}.sidebar.show{transform:translateX(0)}
.main{margin-left:0}.hamburger,.mobileclose{display:block}.mobileclose{margin-left:auto}.topbar{padding:0 17px;height:62px;gap:12px}
.content{padding:22px 15px}.pageheading{align-items:flex-start;flex-direction:column}.pageheading h1{font-size:25px}
.metrics,.alertgrid,.reportgrid{grid-template-columns:1fr}.metric{padding:19px}.simulation-label{font-size:9px}
.sidebar{box-shadow:8px 0 35px #00000010}.queueitem>div:last-child{flex-direction:column;gap:5px;align-items:flex-end}
.settingrow{align-items:flex-start;flex-direction:column}.toolbar{flex-wrap:wrap}.toolbar select{width:100%}}
'''
}

for name,content in files.items():
    (root/name).write_text(content.strip()+"\n",encoding="utf-8")
    print("Created:",root/name)

print("Frontend source files generated successfully.")
