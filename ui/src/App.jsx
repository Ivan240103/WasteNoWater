import { useCallback, useEffect, useState } from "react";
import { getJson, postJson } from "./api";

const POLL_MS = 2000;
const fmtTime = (iso) => (iso ? new Date(iso).toLocaleTimeString() : "-");

function usePoll(fetchers) {
  const [data, setData] = useState({});
  const [online, setOnline] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const entries = await Promise.all(
        Object.entries(fetchers).map(async ([k, url]) => [k, await getJson(url)])
      );
      setData(Object.fromEntries(entries));
      setOnline(true);
    } catch {
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  return { data, online, refresh };
}

export default function App() {
  const { data, online, refresh } = usePoll({
    sensors: "/api/sensors",
    sim: "/sim/sensors",
    readings: "/api/readings?limit=15",
    decisions: "/api/decisions?limit=15",
    warnings: "/api/warnings?limit=10",
  });

  const simUp = Object.fromEntries((data.sim ?? []).map((s) => [s.sensor_id, s.is_up]));

  const toggle = async (id) => {
    await postJson(`/sim/sensors/${id}/${simUp[id] ? "down" : "up"}`);
    refresh();
  };

  return (
    <main>
      <h1>Smart Irrigation <small>prototype dashboard</small></h1>
      {!online && <p className="banner">Backend not reachable...</p>}

      <section>
        <h2>Sensors</h2>
        <table>
          <thead>
            <tr><th>Sensor</th><th>Backend status</th><th>Last value</th><th>Silent for</th><th>Emulator</th></tr>
          </thead>
          <tbody>
            {(data.sensors ?? []).map((s) => (
              <tr key={s.sensor_id}>
                <td>{s.sensor_id}</td>
                <td><span className={`badge ${s.status}`}>{s.status}</span></td>
                <td>{s.last_value == null ? "-" : `${s.last_value.toFixed(1)} %`}</td>
                <td>{s.seconds_since_last_data}s</td>
                <td>
                  <button onClick={() => toggle(s.sensor_id)} disabled={!(s.sensor_id in simUp)}>
                    {simUp[s.sensor_id] ? "Kill sensor" : "Revive sensor"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Warnings</h2>
        {(data.warnings ?? []).length === 0 && <p className="muted">none</p>}
        <ul>
          {(data.warnings ?? []).map((w, i) => (
            <li key={i} className={w.kind}>
              <b>{fmtTime(w.created_at)}</b> [{w.kind}] {w.message}
            </li>
          ))}
        </ul>
      </section>

      <div className="cols">
        <section>
          <h2>Irrigation decisions</h2>
          <table>
            <thead><tr><th>Time</th><th>Sensor</th><th>Action</th><th>Water</th><th>Data</th></tr></thead>
            <tbody>
              {(data.decisions ?? []).map((d, i) => (
                <tr key={i} title={d.reason}>
                  <td>{fmtTime(d.created_at)}</td>
                  <td>{d.sensor_id}</td>
                  <td>{d.action}</td>
                  <td>{d.water_liters} L</td>
                  <td>{d.based_on_cached_data ? <span className="badge DOWN">cached</span> : "fresh"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section>
          <h2>Latest readings (from the database)</h2>
          <table>
            <thead><tr><th>Time</th><th>Sensor</th><th>Value</th></tr></thead>
            <tbody>
              {(data.readings ?? []).map((r, i) => (
                <tr key={i}>
                  <td>{fmtTime(r.timestamp)}</td>
                  <td>{r.sensor_id}</td>
                  <td>{r.value.toFixed(2)} %</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </main>
  );
}
