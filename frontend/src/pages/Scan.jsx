import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom"; // <-- add this
import api from "../api";

export default function Scan() {
  const [mode, setMode] = useState("text"); // "text" | "pdf"
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [file, setFile] = useState(null);

  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState(null);

  const location = useLocation(); // <-- add this

  // NEW: prefill from History -> Scan navigation
  useEffect(() => {
    const st = location.state;
    if (st && (typeof st.resume_text === "string" || typeof st.jd_text === "string")) {
      setMode("text"); // ensure text mode so fields are visible
      if (typeof st.resume_text === "string") setResumeText(st.resume_text);
      if (typeof st.jd_text === "string") setJdText(st.jd_text);
      // optional: we could clear router state here, but it’s not required
    }
  }, [location.state]);

  const fillSampleResume = () => {
    setResumeText(
      "Final-year CS student. Built a React + Flask app with JWT. Skills: Python, JavaScript, React, Node.js, REST APIs, SQL, MongoDB, Docker, NLP basics."
    );
  };

  const fillSampleJD = () => {
    setJdText("Must-have: Python, REST, PostgreSQL. Nice to have: Docker, React.");
  };

  async function onScan() {
    setErr("");
    setRes(null);
    setBusy(true);
    try {
      let axiosResp;

      if (mode === "pdf") {
        if (!file) {
          setBusy(false);
          return setErr("Choose a PDF");
        }
        const fd = new FormData();
        fd.append("file", file);
        fd.append("jd_text", jdText);
        axiosResp = await api.post("/api/scan/", fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      } else {
        const body = { resume_text: resumeText, jd_text: jdText };
        axiosResp = await api.post("/api/scan/", body, {
          headers: { "Content-Type": "application/json" },
        });
      }

      const payload = axiosResp?.data;
      let raw = null;

      if (payload && typeof payload === "object") {
        if (payload.data && typeof payload.data === "object") {
          raw = payload.data;
        } else if ("score" in payload || "overlap_ratio" in payload) {
          raw = payload;
        }
      }
      if (!raw) throw new Error("Bad response format from server");

      const normalized = {
        score: Number(raw.score ?? 0),
        overlap_ratio: Number(raw.overlap_ratio ?? 0),
        matched_skills: Array.isArray(raw.matched_skills) ? raw.matched_skills : [],
        missing_skills: Array.isArray(raw.missing_skills) ? raw.missing_skills : [],
        extra_skills: Array.isArray(raw.extra_skills) ? raw.extra_skills : [],
        jd_required: Array.isArray(raw.jd_required) ? raw.jd_required : [],
        jd_optional: Array.isArray(raw.jd_optional) ? raw.jd_optional : [],
      };

      setRes(normalized);
    } catch (e) {
      setErr(e?.response?.data?.message || e?.friendly || "Scan failed");
    } finally {
      setBusy(false);
    }
  }

  const score = Number(res?.score ?? 0);
  const overlap = Number(res?.overlap_ratio ?? 0);

  return (
    <div className="container">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Student: Resume ↔ JD Scanner</h2>

        <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
          <label>
            <input
              type="radio"
              name="mode"
              value="text"
              checked={mode === "text"}
              onChange={() => setMode("text")}
            />{" "}
            Paste Resume Text
          </label>
          <label>
            <input
              type="radio"
              name="mode"
              value="pdf"
              checked={mode === "pdf"}
              onChange={() => setMode("pdf")}
            />{" "}
            Upload PDF
          </label>
        </div>

        {mode === "pdf" ? (
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        ) : (
          <>
            <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
              <button type="button" onClick={fillSampleResume}>
                Use sample resume
              </button>
              <button type="button" onClick={fillSampleJD}>
                Use sample JD
              </button>
            </div>
            <label className="muted">Resume text ({resumeText.length} chars)</label>
            <textarea
              rows={8}
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
            />
          </>
        )}

        <div style={{ marginTop: 12 }}>
          <label className="muted">Job description ({jdText.length} chars)</label>
          <textarea rows={8} value={jdText} onChange={(e) => setJdText(e.target.value)} />
        </div>

        <div style={{ marginTop: 12 }}>
          <button
            onClick={onScan}
            disabled={
              busy ||
              !jdText.trim() ||
              (mode === "pdf" && !file) ||
              (mode === "text" && !resumeText.trim())
            }
          >
            {busy ? "Scanning..." : "Scan"}
          </button>
        </div>

        {err && (
          <p className="error" style={{ marginTop: 12 }}>
            {err}
          </p>
        )}

        {res && (
          <div style={{ marginTop: 16 }}>
            <h3>Results</h3>
            <p>
              <b>Score:</b> {(score * 100).toFixed(1)}% &nbsp; | &nbsp;
              <b>Overlap:</b> {(overlap * 100).toFixed(1)}% &nbsp; | &nbsp;
              <b>Matched:</b> {res.matched_skills.length} &nbsp; | &nbsp;
              <b>Missing:</b> {res.missing_skills.length}
            </p>

            {(res?.jd_required?.length || res?.jd_optional?.length) ? (
              <p style={{ opacity: 0.8, fontSize: 13 }}>
                <b>JD skills detected:</b>{" "}
                {[...(res.jd_required || []), ...(res.jd_optional || [])].join(", ") || "—"}
              </p>
            ) : (
              <p style={{ opacity: 0.8, fontSize: 13 }}>
                <b>JD skills detected:</b> — (no recognizable skills; try adding tech/soft skill keywords)
              </p>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div className="card">
                <b>Matched skills</b>
                <p className="muted">{res.matched_skills.join(", ") || "—"}</p>
              </div>
              <div className="card">
                <b>Missing skills (focus here)</b>
                <p className="muted">{res.missing_skills.join(", ") || "—"}</p>
              </div>
            </div>

            <div style={{ marginTop: 8 }}>
              <button
                onClick={async () => {
                  try {
                    await api.post(
                      "/api/scans/",
                      {
                        resume_text: mode === "pdf" ? "(uploaded pdf)" : resumeText,
                        jd_text: jdText,
                        result: res,
                      },
                      { headers: { "Content-Type": "application/json" } }
                    );
                    alert("Saved to history ✅");
                  } catch (e) {
                    alert(e?.friendly || "Could not save");
                  }
                }}
              >
                Save to history
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
