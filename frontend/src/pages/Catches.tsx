import { useEffect, useState, type FormEvent } from "react";
import Nav from "../components/Nav";
import {
  ApiError,
  createCatch,
  listCatches,
  listLures,
  type Catch,
  type CatchCreate,
  type Lure,
} from "../api";

const emptyForm = {
  dateCaught: "",
  species: "",
  weight: "",
  length: "",
  latitude: "",
  longitude: "",
  lureId: "",
  depth: "",
  notes: "",
};

export default function Catches() {
  const [catches, setCatches] = useState<Catch[]>([]);
  const [lures, setLures] = useState<Lure[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState("");
  const [locationSuccess, setLocationSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [catchesData, luresData] = await Promise.all([listCatches(), listLures()]);
        if (cancelled) return;
        setCatches(catchesData);
        setLures(luresData);
      } catch (err) {
        if (cancelled) return;
        setLoadError(err instanceof ApiError ? err.message : "Failed to load catches");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  function updateField(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handleUseLocation() {
    setLocationError("");
    setLocationSuccess("");

    if (!("geolocation" in navigator)) {
      setLocationError("Geolocation isn't supported by this browser. Enter coordinates manually.");
      return;
    }

    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocating(false);
        setForm((prev) => ({
          ...prev,
          latitude: String(position.coords.latitude),
          longitude: String(position.coords.longitude),
        }));
        setLocationSuccess("Location captured. You can still edit it below.");
      },
      (error) => {
        setLocating(false);
        const message =
          error.code === error.PERMISSION_DENIED
            ? "Location permission denied. Enter coordinates manually."
            : "Couldn't get your location. Enter coordinates manually.";
        setLocationError(message);
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError("");

    if (!form.dateCaught) {
      setSubmitError("Date caught is required");
      return;
    }

    const payload: CatchCreate = {
      date_caught: new Date(form.dateCaught).toISOString(),
    };

    if (form.species.trim() !== "") payload.species = form.species.trim();
    if (form.weight !== "") payload.weight = parseFloat(form.weight);
    if (form.length !== "") payload.length = parseFloat(form.length);
    if (form.latitude !== "") payload.latitude = parseFloat(form.latitude);
    if (form.longitude !== "") payload.longitude = parseFloat(form.longitude);
    if (form.depth !== "") payload.depth = parseFloat(form.depth);
    if (form.notes.trim() !== "") payload.notes = form.notes.trim();
    if (form.lureId !== "") payload.lure_id = Number(form.lureId);

    setSubmitting(true);
    try {
      const created = await createCatch(payload);
      setCatches((prev) => [...prev, created]);
      setForm(emptyForm);
      setLocationError("");
      setLocationSuccess("");
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Failed to create catch");
    } finally {
      setSubmitting(false);
    }
  }

  function lureName(lureId: number | null): string {
    if (lureId === null) return "-";
    return lures.find((l) => l.id === lureId)?.name ?? "-";
  }

  return (
    <>
      <Nav />
      <h1>Catches</h1>

      <form onSubmit={handleSubmit}>
        <label htmlFor="dateCaught">Date caught</label>
        <input
          id="dateCaught"
          type="datetime-local"
          value={form.dateCaught}
          onChange={(e) => updateField("dateCaught", e.target.value)}
          required
        />

        <label htmlFor="species">Species</label>
        <input
          id="species"
          type="text"
          value={form.species}
          onChange={(e) => updateField("species", e.target.value)}
        />

        <label htmlFor="weight">Weight</label>
        <input
          id="weight"
          type="number"
          step="any"
          value={form.weight}
          onChange={(e) => updateField("weight", e.target.value)}
        />

        <label htmlFor="length">Length</label>
        <input
          id="length"
          type="number"
          step="any"
          value={form.length}
          onChange={(e) => updateField("length", e.target.value)}
        />

        <button type="button" onClick={handleUseLocation} disabled={locating}>
          {locating ? "Locating..." : "Use my location"}
        </button>
        {locationError && <p className="error">{locationError}</p>}
        {locationSuccess && <p className="success">{locationSuccess}</p>}

        <label htmlFor="latitude">Latitude</label>
        <input
          id="latitude"
          type="number"
          step="any"
          value={form.latitude}
          onChange={(e) => updateField("latitude", e.target.value)}
        />

        <label htmlFor="longitude">Longitude</label>
        <input
          id="longitude"
          type="number"
          step="any"
          value={form.longitude}
          onChange={(e) => updateField("longitude", e.target.value)}
        />

        <label htmlFor="depth">Depth</label>
        <input
          id="depth"
          type="number"
          step="any"
          value={form.depth}
          onChange={(e) => updateField("depth", e.target.value)}
        />

        <label htmlFor="lureId">Lure</label>
        <select
          id="lureId"
          value={form.lureId}
          onChange={(e) => updateField("lureId", e.target.value)}
        >
          <option value="">None</option>
          {lures.map((lure) => (
            <option key={lure.id} value={lure.id}>
              {lure.name ?? `Lure #${lure.id}`}
            </option>
          ))}
        </select>

        <label htmlFor="notes">Notes</label>
        <textarea
          id="notes"
          value={form.notes}
          onChange={(e) => updateField("notes", e.target.value)}
        />

        {submitError && <p className="error">{submitError}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Log catch"}
        </button>
      </form>

      {loading ? (
        <p>Loading catches...</p>
      ) : loadError ? (
        <p className="error">{loadError}</p>
      ) : catches.length === 0 ? (
        <p className="empty-state">No catches logged yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Species</th>
              <th>Weight</th>
              <th>Length</th>
              <th>Lure</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {catches.map((c) => (
              <tr key={c.id}>
                <td>{new Date(c.date_caught).toLocaleString()}</td>
                <td>{c.species ?? "-"}</td>
                <td>{c.weight ?? "-"}</td>
                <td>{c.length ?? "-"}</td>
                <td>{lureName(c.lure_id)}</td>
                <td>{c.notes ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
