import { useEffect, useState, type FormEvent } from "react";
import Nav from "../components/Nav";
import { ApiError, createLure, listLures, type Lure, type LureCreate } from "../api";

interface FormState {
  name: string;
  weight: string;
  type: string;
  color: string;
  brand: string;
  model: string;
  size: string;
}

const emptyForm: FormState = {
  name: "",
  weight: "",
  type: "",
  color: "",
  brand: "",
  model: "",
  size: "",
};

export default function Lures() {
  const [lures, setLures] = useState<Lure[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [form, setForm] = useState<FormState>(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  useEffect(() => {
    void fetchLures();
  }, []);

  async function fetchLures() {
    setLoading(true);
    setListError("");
    try {
      const data = await listLures();
      setLures(data);
    } catch (err) {
      setListError(err instanceof ApiError ? err.message : "Failed to load lures.");
    } finally {
      setLoading(false);
    }
  }

  function updateField(field: keyof FormState, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError("");
    setSubmitting(true);

    const data: LureCreate = {};
    if (form.name.trim() !== "") data.name = form.name.trim();
    if (form.type.trim() !== "") data.type = form.type.trim();
    if (form.color.trim() !== "") data.color = form.color.trim();
    if (form.brand.trim() !== "") data.brand = form.brand.trim();
    if (form.model.trim() !== "") data.model = form.model.trim();
    if (form.weight.trim() !== "") data.weight = Number(form.weight);
    if (form.size.trim() !== "") data.size = Number(form.size);

    try {
      await createLure(data);
      setForm(emptyForm);
      await fetchLures();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Failed to create lure.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Nav />
      <h1>Lures</h1>

      <form onSubmit={handleSubmit}>
        <label htmlFor="lure-name">Name</label>
        <input
          id="lure-name"
          type="text"
          value={form.name}
          onChange={(e) => updateField("name", e.target.value)}
        />

        <label htmlFor="lure-type">Type</label>
        <input
          id="lure-type"
          type="text"
          value={form.type}
          onChange={(e) => updateField("type", e.target.value)}
        />

        <label htmlFor="lure-color">Color</label>
        <input
          id="lure-color"
          type="text"
          value={form.color}
          onChange={(e) => updateField("color", e.target.value)}
        />

        <label htmlFor="lure-brand">Brand</label>
        <input
          id="lure-brand"
          type="text"
          value={form.brand}
          onChange={(e) => updateField("brand", e.target.value)}
        />

        <label htmlFor="lure-model">Model</label>
        <input
          id="lure-model"
          type="text"
          value={form.model}
          onChange={(e) => updateField("model", e.target.value)}
        />

        <label htmlFor="lure-weight">Weight</label>
        <input
          id="lure-weight"
          type="number"
          step="any"
          value={form.weight}
          onChange={(e) => updateField("weight", e.target.value)}
        />

        <label htmlFor="lure-size">Size</label>
        <input
          id="lure-size"
          type="number"
          step="any"
          value={form.size}
          onChange={(e) => updateField("size", e.target.value)}
        />

        {submitError && <p className="error">{submitError}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Adding…" : "Add lure"}
        </button>
      </form>

      {loading ? (
        <p>Loading…</p>
      ) : listError ? (
        <p className="error">{listError}</p>
      ) : lures.length === 0 ? (
        <p className="empty-state">No lures yet — add one above.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Color</th>
              <th>Brand</th>
              <th>Model</th>
              <th>Weight</th>
              <th>Size</th>
            </tr>
          </thead>
          <tbody>
            {lures.map((lure) => (
              <tr key={lure.id}>
                <td>{lure.name ?? ""}</td>
                <td>{lure.type ?? ""}</td>
                <td>{lure.color ?? ""}</td>
                <td>{lure.brand ?? ""}</td>
                <td>{lure.model ?? ""}</td>
                <td>{lure.weight ?? ""}</td>
                <td>{lure.size ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
