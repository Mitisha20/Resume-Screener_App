import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function History() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const nav = useNavigate();

const handleLoadInScanner=(item)=>{
  const prefill={
    mode:"text",
    resumetext:item.resume_text || "",
    jdText:item.jd_text || "",
  };
  
  Navigate("/scan",{state:{prefill}});
}

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/api/scans/?limit=50");
        const raw = data?.data ?? data;
        setItems(Array.isArray(raw?.items) ? raw.items : []);
      } catch (e) {
        setErr(e?.friendly || "Could not load history");
      }
    })();
  }, []);
  
  
  return (
    <div className="container">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>History</h2>
        {err && <p className="error">{err}</p>}
        {!items.length ? (
          <p>No saved scans yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {items.map((it) => (
              <li key={it.id} className="card" style={{ marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <div>
                    <div><b>{(it.score * 100).toFixed(1)}%</b> — matched {it.matched}, missing {it.missing}</div>
                    <div className="muted" style={{ fontSize: 12 }}>{new Date(it.created_at).toLocaleString()}</div>
                    <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>
                      <b>Resume:</b> {it.resume_preview}<br/>
                      <b>JD:</b> {it.jd_preview}
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <button onClick={() => {
                      nav("/scan", { state: { resume_text: it.resume_text, jd_text: it.jd_text }});
                    }}>Load in scanner</button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
