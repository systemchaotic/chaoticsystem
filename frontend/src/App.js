import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

const API = import.meta?.env?.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '/api';

function PackForm({ onSave }) {
  const [title, setTitle] = useState('');
  const [theme, setTheme] = useState('');
  const [summary, setSummary] = useState('');
  const [authorEmail, setAuthorEmail] = useState('');

  const [resources, setResources] = useState([]);
  const [upgrades, setUpgrades] = useState([]);
  const [areas, setAreas] = useState([]);
  const [factions, setFactions] = useState([]);

  const addItem = (setter, factory) => () => setter(prev => [...prev, factory()]);
  const removeItem = (setter, id) => setter(prev => prev.filter(i => i.id !== id));

  const resFactory = () => ({ id: uuidv4(), key: '', name: '', description: '', base_rate: 0 });
  const upgFactory = () => ({ id: uuidv4(), key: '', name: '', description: '', cost: {}, effects: {} });
  const areaFactory = () => ({ id: uuidv4(), key: '', name: '', description: '', unlock_conditions: {} });
  const factionFactory = () => ({ id: uuidv4(), key: '', name: '', description: '', traits: {} });

  const submit = async (e) => {
    e.preventDefault();
    const payload = { id: uuidv4(), title, theme, summary, author_email: authorEmail, resources, upgrades, areas, factions };
    const { data } = await axios.post(`${API}/packs`, payload);
    onSave?.(data);
    setTitle(''); setTheme(''); setSummary(''); setAuthorEmail('');
    setResources([]); setUpgrades([]); setAreas([]); setFactions([]);
  };

  const Section = ({ title, items, setter, fields }) => (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">{title}</h3>
        <button type="button" className="btn" onClick={addItem(setter, fields.factory)}>+ Add</button>
      </div>
      <div className="space-y-2">
        {items.map((it) => (
          <div key={it.id} className="grid grid-cols-12 gap-2 items-start">
            <input className="input col-span-2" placeholder="key" value={it.key} onChange={e => setter(prev => prev.map(p => p.id===it.id?{...p, key:e.target.value}:p))} />
            <input className="input col-span-3" placeholder="name" value={it.name} onChange={e => setter(prev => prev.map(p => p.id===it.id?{...p, name:e.target.value}:p))} />
            <input className="input col-span-5" placeholder="description" value={it.description} onChange={e => setter(prev => prev.map(p => p.id===it.id?{...p, description:e.target.value}:p))} />
            {fields.extra?.(it, setter)}
            <button type="button" className="btn col-span-1" onClick={() => removeItem(setter, it.id)}>Remove</button>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <form className="space-y-4" onSubmit={submit}>
      <div className="card">
        <h2 className="text-xl font-bold mb-2">New Content Pack</h2>
        <div className="grid grid-cols-2 gap-4">
          <input className="input" placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} />
          <input className="input" placeholder="Theme (e.g., Solarpunk Alchemy)" value={theme} onChange={e => setTheme(e.target.value)} />
          <input className="input" placeholder="Short summary" value={summary} onChange={e => setSummary(e.target.value)} />
          <input className="input" placeholder="Author email (optional)" value={authorEmail} onChange={e => setAuthorEmail(e.target.value)} />
        </div>
      </div>

      <Section title="Resources" items={resources} setter={setResources} fields={{ factory: resFactory, extra: (it, setter)=> (
        <input className="input col-span-1" type="number" step="0.1" placeholder="base rate" value={it.base_rate}
          onChange={e => setter(prev => prev.map(p => p.id===it.id?{...p, base_rate: Number(e.target.value)}:p))} />
      ) }} />

      <Section title="Upgrades" items={upgrades} setter={setUpgrades} fields={{ factory: upgFactory }} />
      <Section title="Areas" items={areas} setter={setAreas} fields={{ factory: areaFactory }} />
      <Section title="Factions" items={factions} setter={setFactions} fields={{ factory: factionFactory }} />

      <div className="flex gap-3">
        <button className="btn" type="submit">Save Pack</button>
      </div>
    </form>
  );
}

function PacksList({ onSelect }) {
  const [items, setItems] = useState([]);
  const load = async () => {
    const { data } = await axios.get(`${API}/packs`);
    setItems(data);
  };
  useEffect(() => { load(); }, []);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold">Saved Packs</h2>
        <button className="btn" onClick={load}>Refresh</button>
      </div>
      <ul className="divide-y">
        {items.map(p => (
          <li key={p.id} className="py-2 flex items-center justify-between">
            <div>
              <div className="font-semibold">{p.title}</div>
              <div className="text-sm text-slate-500">{p.theme}</div>
            </div>
            <button className="btn" onClick={() => onSelect?.(p)}>Open</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function App() {
  const [selected, setSelected] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    async function check() {
      try {
        const { data } = await axios.get(`${API}/health`);
        setHealth(data);
      } catch (e) {
        setHealth({ ok: false, error: e?.message });
      }
    }
    check();
  }, []);

  return (
    <div className="container py-6 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Idle Game Content Studio</h1>
        <div className={`text-sm ${health?.ok ? 'text-green-600' : 'text-red-600'}`}>
          {health?.ok ? 'Backend OK' : `Backend Error: ${health?.error || 'unknown'}`}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <PackForm onSave={()=> setSelected(null)} />
        </div>
        <div className="lg:col-span-1 space-y-6">
          <PacksList onSelect={setSelected} />
          {selected && (
            <div className="card">
              <h3 className="font-semibold mb-2">Selected Pack</h3>
              <pre className="text-xs bg-slate-100 p-2 rounded overflow-auto max-h-64">{JSON.stringify(selected, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}