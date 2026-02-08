<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRENZA - Dispensa e Dieta</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        .glass-nav { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(12px); }
        .card-pop { transition: all 0.2s ease; }
        .card-pop:active { transform: scale(0.97); }
        .animate-pop { animation: pop 0.3s ease-out; }
        @keyframes pop {
            0% { transform: scale(0.9); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        .hide-scrollbar::-webkit-scrollbar { display: none; }
    </style>
</head>
<body class="bg-[#F8FAFC] min-h-screen text-[#1E293B]">
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef, useMemo } = React;

        const CATEGORY_MAP = {
            "Pasta/Riso": { icon: "utensils", color: "bg-orange-100 text-orange-600 border-orange-200" },
            "Pane/Farina": { icon: "wheat", color: "bg-amber-100 text-amber-700 border-amber-200" },
            "Verdura": { icon: "carrot", color: "bg-green-100 text-green-700 border-green-200" },
            "Frutta": { icon: "apple", color: "bg-emerald-100 text-emerald-700 border-emerald-200" },
            "Carne": { icon: "drumstick", color: "bg-red-100 text-red-600 border-red-200" },
            "Pesce": { icon: "fish", color: "bg-blue-100 text-blue-700 border-blue-200" },
            "Latticini": { icon: "milk", color: "bg-indigo-100 text-indigo-600 border-indigo-200" },
            "Bibite": { icon: "cup-soda", color: "bg-cyan-100 text-cyan-600 border-cyan-200" },
            "Dolci": { icon: "ice-cream", color: "bg-pink-100 text-pink-600 border-pink-200" },
            "Conserve": { icon: "archive", color: "bg-stone-100 text-stone-600 border-stone-200" },
            "Surgelati": { icon: "snowflake", color: "bg-sky-100 text-sky-600 border-sky-200" },
            "Igiene": { icon: "sparkles", color: "bg-violet-100 text-violet-600 border-violet-200" },
            "Altro": { icon: "box", color: "bg-slate-100 text-slate-600 border-slate-200" }
        };

        const DAYS = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"];
        const MEALS = ["Colazione", "Spuntino Mattutino", "Pranzo", "Spuntino Pomeridiano", "Cena"];

        const Icon = ({ name, size = 24, className = "" }) => {
            useEffect(() => { if (window.lucide) window.lucide.createIcons(); });
            return <i data-lucide={name} style={{ width: size, height: size }} className={className}></i>;
        };

        const App = () => {
            const [activeTab, setActiveTab] = useState('pantry');
            const [pantries, setPantries] = useState(() => {
                const saved = localStorage.getItem('crenza_v5_pantries');
                return saved ? JSON.parse(saved) : [{ id: 1, name: "Dispensa Principale", items: [] }];
            });
            const [activePantryId, setActivePantryId] = useState(() => parseInt(localStorage.getItem('crenza_v5_active_pantry')) || 1);
            const [shoppingList, setShoppingList] = useState(() => JSON.parse(localStorage.getItem('crenza_v5_shopping') || '[]'));
            const [diets, setDiets] = useState(() => {
                const saved = localStorage.getItem('crenza_v5_diets');
                return saved ? JSON.parse(saved) : [
                    { id: 1, name: "La mia Dieta", plan: {} },
                    { id: 2, name: "Dieta figlio", plan: {} }
                ];
            });
            const [activeDietId, setActiveDietId] = useState(() => parseInt(localStorage.getItem('crenza_v5_active_diet')) || 1);
            const [settings, setSettings] = useState(() => JSON.parse(localStorage.getItem('crenza_v5_settings') || '{"alertDays": 3}'));
            const [showPantryManager, setShowPantryManager] = useState(false);
            const [showDietManager, setShowDietManager] = useState(false);
            const [moveItem, setMoveItem] = useState(null);
            const [editingPantryId, setEditingPantryId] = useState(null);
            const [editingDietId, setEditingDietId] = useState(null);

            useEffect(() => localStorage.setItem('crenza_v5_pantries', JSON.stringify(pantries)), [pantries]);
            useEffect(() => localStorage.setItem('crenza_v5_shopping', JSON.stringify(shoppingList)), [shoppingList]);
            useEffect(() => localStorage.setItem('crenza_v5_diets', JSON.stringify(diets)), [diets]);
            useEffect(() => localStorage.setItem('crenza_v5_settings', JSON.stringify(settings)), [settings]);
            useEffect(() => localStorage.setItem('crenza_v5_active_pantry', activePantryId), [activePantryId]);
            useEffect(() => localStorage.setItem('crenza_v5_active_diet', activeDietId), [activeDietId]);

            const currentPantry = useMemo(() => pantries.find(p => p.id === activePantryId) || pantries[0], [pantries, activePantryId]);
            const currentDiet = useMemo(() => diets.find(d => d.id === activeDietId) || diets[0], [diets, activeDietId]);

            const addToPantry = (item) => {
                setPantries(prev => prev.map(p => p.id === activePantryId ? { ...p, items: [...p.items, { ...item, id: Date.now() }] } : p));
                setActiveTab('pantry');
                setMoveItem(null);
            };

            const removeFromPantry = (id) => {
                setPantries(prev => prev.map(p => p.id === activePantryId ? { ...p, items: p.items.filter(i => i.id !== id) } : p));
            };

            const checkExpiryStatus = (expiryDate) => {
                if (!expiryDate) return 'none';
                const today = new Date(); today.setHours(0,0,0,0);
                const expiry = new Date(expiryDate);
                const diffDays = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
                if (diffDays < 0) return 'expired';
                if (diffDays <= settings.alertDays) return 'near';
                return 'ok';
            };

            const updateDiet = (day, meal, value) => {
                setDiets(prev => prev.map(d => d.id === activeDietId ? { ...d, plan: { ...d.plan, [`${day}-${meal}`]: value } } : d));
            };

            const shoppingTotal = useMemo(() => {
                return shoppingList.reduce((acc, item) => acc + ((item.price || 0) * (item.qty || 1)), 0);
            }, [shoppingList]);

            return (
                <div className="max-w-md mx-auto bg-white min-h-screen flex flex-col shadow-2xl relative border-x border-slate-100 overflow-hidden">
                    <header className="bg-gradient-to-r from-red-600 to-rose-500 text-white p-5 sticky top-0 z-40 shadow-lg">
                        <div className="flex justify-between items-center mb-2">
                            <h1 className="text-2xl font-black flex items-center gap-2 tracking-tighter uppercase italic">
                                <Icon name="pizza" size={32} /> CRENZA
                            </h1>
                            <button onClick={() => setShowPantryManager(!showPantryManager)} className="bg-white/20 p-2.5 rounded-2xl hover:bg-white/30 transition-all backdrop-blur-md">
                                <Icon name="layers" size={22} />
                            </button>
                        </div>
                        <div className="inline-flex items-center gap-2 bg-black/10 px-3 py-1.5 rounded-xl text-xs font-bold border border-white/10">
                            <Icon name="map-pin" size={14} /> {currentPantry.name}
                        </div>
                    </header>

                    {showPantryManager && (
                        <div className="absolute top-[108px] left-0 right-0 z-50 bg-white shadow-2xl border-b animate-in slide-in-from-top duration-300 rounded-b-3xl">
                            <div className="p-5 space-y-4">
                                <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">Le mie zone</h3>
                                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                                    {pantries.map(p => (
                                        <div key={p.id} className="flex gap-2">
                                            {editingPantryId === p.id ? (
                                                <input 
                                                    autoFocus
                                                    className="flex-1 bg-slate-50 border-2 border-red-500 rounded-2xl px-4 py-2 font-bold outline-none"
                                                    defaultValue={p.name}
                                                    onBlur={(e) => {
                                                        const newName = e.target.value.trim();
                                                        if (newName) setPantries(pantries.map(x => x.id === p.id ? { ...x, name: newName } : x));
                                                        setEditingPantryId(null);
                                                    }}
                                                    onKeyPress={(e) => {
                                                        if (e.key === 'Enter') e.target.blur();
                                                    }}
                                                />
                                            ) : (
                                                <button onClick={() => { setActivePantryId(p.id); setShowPantryManager(false); }} className={`flex-1 text-left p-4 rounded-2xl border-2 transition-all flex items-center justify-between ${activePantryId === p.id ? 'border-red-500 bg-red-50 text-red-700 shadow-sm' : 'border-slate-100 text-slate-600'}`}>
                                                    <span className="font-bold">{p.name}</span>
                                                    <span className="text-[10px] bg-white px-2 py-1 rounded-lg border border-slate-200">{p.items.length} items</span>
                                                </button>
                                            )}
                                            <button onClick={() => setEditingPantryId(editingPantryId === p.id ? null : p.id)} className="p-4 text-slate-300 hover:text-blue-500 transition-colors">
                                                <Icon name="edit-3" size={20} />
                                            </button>
                                            <button onClick={() => { if(pantries.length > 1 && confirm("Eliminare questa zona e tutti i suoi prodotti?")) { const f = pantries.filter(x => x.id !== p.id); setPantries(f); if(activePantryId === p.id) setActivePantryId(f[0].id); } }} className="p-4 text-slate-300 hover:text-red-500 transition-colors">
                                                <Icon name="trash-2" size={20} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                                <div className="flex gap-2 pt-2 border-t border-slate-50">
                                    <input id="pantryName" type="text" placeholder="Nuova zona (es. Frigo)" className="flex-1 bg-slate-100 rounded-2xl px-4 py-3 text-sm font-bold focus:ring-2 focus:ring-red-500 outline-none" />
                                    <button onClick={() => { const v = document.getElementById('pantryName').value; if(v){ setPantries([...pantries, {id: Date.now(), name: v, items: []}]); document.getElementById('pantryName').value=''; } }} className="bg-red-600 text-white p-3 rounded-2xl shadow-lg shadow-red-200"><Icon name="plus" size={24} /></button>
                                </div>
                            </div>
                        </div>
                    )}

                    <main className="flex-1 p-5 overflow-y-auto pb-32">
                        {activeTab === 'pantry' && (
                            <div className="space-y-6">
                                <div className="flex justify-between items-end">
                                    <div>
                                        <p className="text-[10px] font-black text-red-500 uppercase tracking-[0.2em] mb-1">Inventario</p>
                                        <h2 className="text-3xl font-black text-slate-800 tracking-tighter">Credenza</h2>
                                    </div>
                                    <button onClick={() => setShowPantryManager(true)} className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 p-3 rounded-2xl transition-all">
                                        <Icon name="plus" size={18} className="text-red-600" />
                                        <span className="text-[10px] font-black uppercase text-slate-600">Nuova Zona</span>
                                    </button>
                                </div>

                                {/* Selettore rapido credenze */}
                                <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
                                    {pantries.map(p => (
                                        <button 
                                            key={p.id} 
                                            onClick={() => setActivePantryId(p.id)}
                                            className={`shrink-0 px-4 py-2 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all border-2 ${activePantryId === p.id ? 'bg-red-600 border-red-600 text-white shadow-lg shadow-red-100' : 'bg-white border-slate-100 text-slate-400 hover:border-red-200'}`}
                                        >
                                            {p.name}
                                        </button>
                                    ))}
                                </div>

                                <div className="flex justify-between items-center bg-slate-50 p-4 rounded-3xl border border-slate-100">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 bg-white rounded-2xl flex items-center justify-center shadow-sm">
                                            <Icon name="box" size={20} className="text-red-600" />
                                        </div>
                                        <div>
                                            <h4 className="font-black text-slate-800 text-sm">{currentPantry.name}</h4>
                                            <p className="text-[10px] font-bold text-slate-400 uppercase">{currentPantry.items.length} Articoli totali</p>
                                        </div>
                                    </div>
                                    <button onClick={() => { setEditingPantryId(currentPantry.id); setShowPantryManager(true); }} className="p-2 text-slate-300 hover:text-blue-500 transition-colors">
                                        <Icon name="edit-3" size={18} />
                                    </button>
                                </div>

                                {currentPantry.items.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center py-24 text-slate-200 text-center">
                                        <Icon name="package" size={80} strokeWidth={1} className="mb-4" />
                                        <p className="font-black uppercase tracking-widest text-xs">Credenza Vuota</p>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 gap-4">
                                        {currentPantry.items.sort((a,b) => (a.expiry || '9999') > (b.expiry || '9999') ? 1 : -1).map(item => {
                                            const status = checkExpiryStatus(item.expiry);
                                            const cat = CATEGORY_MAP[item.category] || CATEGORY_MAP["Altro"];
                                            return (
                                                <div key={item.id} className={`card-pop group relative p-4 rounded-[2rem] border-2 flex gap-4 items-center shadow-sm hover:shadow-xl transition-all animate-pop ${
                                                    status === 'expired' ? 'bg-red-50 border-red-200' : 
                                                    status === 'near' ? 'bg-amber-50 border-amber-200' : 'bg-white border-slate-50'
                                                }`}>
                                                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-inner shrink-0 ${cat.color} border`}>
                                                        <Icon name={cat.icon} size={28} />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <h3 className="font-extrabold text-slate-800 text-lg leading-tight truncate">{item.name}</h3>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <span className="text-[9px] font-black uppercase tracking-wider opacity-60">{item.category}</span>
                                                            <div className={`flex items-center gap-1 text-[10px] font-bold ${status === 'expired' ? 'text-red-600' : status === 'near' ? 'text-amber-600' : 'text-slate-400'}`}>
                                                                <Icon name="clock" size={10} />
                                                                {item.expiry ? item.expiry : 'Senza scadenza'}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <button onClick={() => removeFromPantry(item.id)} className="w-10 h-10 rounded-full bg-slate-50 text-slate-300 hover:bg-red-500 hover:text-white flex items-center justify-center transition-all active:scale-90">
                                                        <Icon name="trash-2" size={16} />
                                                    </button>
                                                    {status === 'expired' && <div className="absolute -top-2 -right-2 bg-red-600 text-white text-[8px] font-black px-2 py-1 rounded-lg shadow-lg uppercase">Scaduto</div>}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'shopping' && (
                            <div className="space-y-6">
                                <div className="flex justify-between items-end">
                                    <h2 className="text-3xl font-black text-slate-800 tracking-tighter">La Spesa</h2>
                                    <div className="text-right">
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Totale Stimato</p>
                                        <p className="text-2xl font-black text-red-600">€{shoppingTotal.toFixed(2)}</p>
                                    </div>
                                </div>
                                
                                <div className="bg-white p-4 rounded-[2.5rem] shadow-xl border-2 border-slate-100 space-y-3">
                                    <input id="shopIn" type="text" placeholder="Cosa comprare?" className="w-full bg-slate-50 rounded-2xl px-4 py-3 outline-none text-sm font-bold border-2 border-transparent focus:border-red-100" />
                                    <div className="flex gap-2">
                                        <div className="flex-1">
                                            <label className="text-[9px] font-black text-slate-300 uppercase pl-2">Quantità</label>
                                            <input id="shopQty" type="number" defaultValue="1" min="1" className="w-full bg-slate-50 rounded-xl px-4 py-2 outline-none text-sm font-bold" />
                                        </div>
                                        <div className="flex-1">
                                            <label className="text-[9px] font-black text-slate-300 uppercase pl-2">Prezzo €</label>
                                            <input id="shopPrice" type="number" step="0.01" placeholder="0.00" className="w-full bg-slate-50 rounded-xl px-4 py-2 outline-none text-sm font-bold" />
                                        </div>
                                        <button onClick={() => { 
                                            const name = document.getElementById('shopIn').value;
                                            const qty = parseFloat(document.getElementById('shopQty').value) || 1;
                                            const price = parseFloat(document.getElementById('shopPrice').value) || 0;
                                            if(name){ 
                                                setShoppingList([...shoppingList, {id: Date.now(), name, qty, price}]); 
                                                document.getElementById('shopIn').value = ''; 
                                                document.getElementById('shopQty').value = '1'; 
                                                document.getElementById('shopPrice').value = ''; 
                                            } 
                                        }} className="self-end bg-red-600 text-white p-3 rounded-2xl shadow-lg shadow-red-200 active:scale-95 transition-all"><Icon name="plus" size={24} /></button>
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    {shoppingList.map(item => (
                                        <div key={item.id} className="group flex items-center justify-between p-4 bg-white rounded-3xl border-2 border-slate-50 shadow-sm hover:border-red-100 transition-all">
                                            <div className="flex-1 min-w-0">
                                                <h3 className="font-extrabold text-slate-800 truncate">{item.name}</h3>
                                                <div className="flex gap-3 text-[10px] font-bold text-slate-400 uppercase">
                                                    <span>Q.tà: {item.qty || 1}</span>
                                                    <span>€{(item.price || 0).toFixed(2)}</span>
                                                    <span className="text-red-500 font-black">Tot: €{((item.qty || 1) * (item.price || 0)).toFixed(2)}</span>
                                                </div>
                                            </div>
                                            <div className="flex gap-1">
                                                <button onClick={() => setMoveItem(item)} className="p-3 text-red-500 hover:bg-red-50 rounded-2xl transition-all"><Icon name="truck" size={18} /></button>
                                                <button onClick={() => setShoppingList(shoppingList.filter(i => i.id !== item.id))} className="p-3 text-slate-200 hover:text-red-500 transition-colors"><Icon name="trash-2" size={18} /></button>
                                            </div>
                                        </div>
                                    ))}
                                    {shoppingList.length === 0 && <div className="text-center py-20 opacity-30 font-black uppercase text-xs tracking-[0.3em]">Lista vuota</div>}
                                </div>
                            </div>
                        )}

                        {activeTab === 'diet' && (
                            <div className="space-y-6">
                                <div className="flex justify-between items-center">
                                    <h2 className="text-3xl font-black text-slate-800 tracking-tighter">Dieta</h2>
                                    <button onClick={() => setShowDietManager(!showDietManager)} className="bg-red-50 text-red-600 p-3 rounded-2xl flex items-center gap-2 font-black text-xs uppercase tracking-widest">
                                        <Icon name="users" size={16} /> {currentDiet.name}
                                    </button>
                                </div>

                                {showDietManager && (
                                    <div className="bg-white p-5 rounded-[2rem] border-2 border-slate-100 shadow-xl space-y-4 animate-in slide-in-from-top duration-300">
                                        <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Scegli o aggiungi dieta</h3>
                                        <div className="space-y-2">
                                            {diets.map(d => (
                                                <div key={d.id} className="flex gap-2">
                                                    {editingDietId === d.id ? (
                                                        <input 
                                                            autoFocus
                                                            className="flex-1 bg-slate-50 border-2 border-red-500 rounded-xl px-4 py-2 font-bold outline-none"
                                                            defaultValue={d.name}
                                                            onBlur={(e) => {
                                                                const newName = e.target.value.trim();
                                                                if (newName) setDiets(diets.map(x => x.id === d.id ? { ...x, name: newName } : x));
                                                                setEditingDietId(null);
                                                            }}
                                                            onKeyPress={(e) => { if (e.key === 'Enter') e.target.blur(); }}
                                                        />
                                                    ) : (
                                                        <button onClick={() => { setActiveDietId(d.id); setShowDietManager(false); }} className={`flex-1 text-left p-3 rounded-xl border-2 font-bold transition-all ${activeDietId === d.id ? 'border-red-500 bg-red-50 text-red-700' : 'border-slate-50 text-slate-500'}`}>
                                                            {d.name}
                                                        </button>
                                                    )}
                                                    <button onClick={() => setEditingDietId(editingDietId === d.id ? null : d.id)} className="p-2 text-slate-300 hover:text-blue-500"><Icon name="edit-3" size={18} /></button>
                                                    <button onClick={() => { if(diets.length > 1 && confirm("Eliminare?")) { const f = diets.filter(x => x.id !== d.id); setDiets(f); if(activeDietId === d.id) setActiveDietId(f[0].id); } }} className="p-2 text-slate-300 hover:text-red-500"><Icon name="trash-2" size={18} /></button>
                                                </div>
                                            ))}
                                        </div>
                                        <div className="flex gap-2 pt-2 border-t">
                                            <input id="newDietName" type="text" placeholder="Nome nuova dieta" className="flex-1 bg-slate-50 rounded-xl px-4 py-2 text-xs font-bold outline-none" />
                                            <button onClick={() => { const v = document.getElementById('newDietName').value; if(v){ setDiets([...diets, {id: Date.now(), name: v, plan: {}}]); document.getElementById('newDietName').value=''; } }} className="bg-red-600 text-white p-2 rounded-xl"><Icon name="plus" size={20} /></button>
                                        </div>
                                    </div>
                                )}

                                <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
                                    {DAYS.map((day, idx) => (
                                        <button key={day} onClick={() => document.getElementById(`day-${idx}`).scrollIntoView({ behavior: 'smooth', block: 'start' })} className="shrink-0 bg-white border-2 border-slate-100 px-4 py-2 rounded-2xl text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-red-500 hover:border-red-200 transition-all">{day}</button>
                                    ))}
                                </div>
                                <div className="space-y-12">
                                    {DAYS.map((day, idx) => (
                                        <div key={day} id={`day-${idx}`} className="space-y-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-red-600 text-white flex items-center justify-center font-black text-xs">{idx + 1}</div>
                                                <h3 className="text-xl font-black text-slate-800 tracking-tight">{day}</h3>
                                            </div>
                                            <div className="grid grid-cols-1 gap-3 bg-white p-4 rounded-[2.5rem] border-2 border-slate-50 shadow-sm">
                                                {MEALS.map(meal => (
                                                    <div key={meal} className="space-y-1">
                                                        <label className="text-[9px] font-black text-slate-300 uppercase tracking-widest pl-2">{meal}</label>
                                                        <input 
                                                            type="text" 
                                                            value={currentDiet.plan[`${day}-${meal}`] || ''} 
                                                            onChange={e => updateDiet(day, meal, e.target.value)}
                                                            className="w-full bg-slate-50/50 border-2 border-slate-50 rounded-2xl px-4 py-3 text-sm font-bold focus:bg-white focus:border-red-100 outline-none transition-all placeholder:text-slate-200"
                                                            placeholder="Cosa mangiamo?"
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {activeTab === 'scan' && <AddView initialName={moveItem?.name} onAdd={(item) => { addToPantry(item); if(moveItem) setShoppingList(shoppingList.filter(i => i.id !== moveItem.id)); }} onCancel={() => { setActiveTab('pantry'); setMoveItem(null); }} />}

                        {activeTab === 'settings' && (
                            <div className="space-y-6">
                                <h2 className="text-3xl font-black text-slate-800 tracking-tighter">Opzioni</h2>
                                <div className="p-8 bg-white border-2 border-slate-100 rounded-[3rem] shadow-xl space-y-8">
                                    <div className="space-y-4">
                                        <label className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2"><Icon name="bell" size={14} /> Giorni pre-avviso scadenza</label>
                                        <div className="flex items-center gap-4">
                                            <input type="number" value={settings.alertDays} onChange={e => setSettings({...settings, alertDays: parseInt(e.target.value) || 0})} className="w-24 bg-slate-50 border-2 border-slate-100 rounded-2xl px-4 py-3 font-black text-xl focus:border-red-500 outline-none transition-all" />
                                            <span className="text-slate-400 font-bold">Giorni</span>
                                        </div>
                                    </div>
                                    <button onClick={() => { if(confirm("Cancellare tutto?")) { localStorage.clear(); location.reload(); } }} className="w-full flex items-center justify-center gap-3 text-red-600 font-black p-5 bg-red-50 rounded-[2rem] hover:bg-red-100 transition-all active:scale-95">
                                        <Icon name="trash-2" size={22} /> Resetta l'App
                                    </button>
                                </div>
                            </div>
                        )}
                    </main>

                    {moveItem && (
                        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-end justify-center">
                            <div className="bg-white w-full max-w-md p-6 rounded-t-[3rem] animate-in slide-in-from-bottom duration-300">
                                <h3 className="text-xl font-black mb-4 flex items-center gap-2 text-slate-800"><Icon name="truck" /> Sposta in Credenza</h3>
                                <p className="text-sm text-slate-400 font-bold mb-6">Stai spostando: <span className="text-red-600">{moveItem.name}</span></p>
                                <button onClick={() => { setActiveTab('scan'); }} className="w-full bg-red-600 text-white font-black py-5 rounded-[2rem] shadow-xl shadow-red-200 mb-3 uppercase tracking-widest text-xs">Scegli Categoria e Scadenza</button>
                                <button onClick={() => setMoveItem(null)} className="w-full bg-slate-100 text-slate-400 font-black py-4 rounded-[2rem] uppercase tracking-widest text-xs">Annulla</button>
                            </div>
                        </div>
                    )}

                    <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto glass-nav border-t border-slate-100 flex justify-around p-4 z-40 pb-8 rounded-t-[3rem] shadow-[0_-10px_40px_rgba(0,0,0,0.05)]">
                        <NavButton active={activeTab === 'pantry'} count={currentPantry.items.length} onClick={() => setActiveTab('pantry')} icon="grid" label="Credenza" />
                        <NavButton active={activeTab === 'shopping'} count={shoppingList.length} onClick={() => setActiveTab('shopping')} icon="shopping-bag" label="Spesa" />
                        <div className="relative -mt-12">
                            <button onClick={() => { setMoveItem(null); setActiveTab('scan'); }} className={`p-5 rounded-[2rem] shadow-2xl shadow-red-200 transition-all active:scale-90 ${activeTab === 'scan' ? 'bg-slate-800 text-white' : 'bg-gradient-to-tr from-red-600 to-rose-500 text-white ring-8 ring-white'}`}>
                                <Icon name="plus" size={32} />
                            </button>
                        </div>
                        <NavButton active={activeTab === 'diet'} onClick={() => setActiveTab('diet')} icon="calendar" label="Dieta" />
                        <NavButton active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} icon="settings" label="Opzioni" />
                    </nav>
                </div>
            );
        };

        const NavButton = ({ active, onClick, icon, label, count }) => (
            <button onClick={onClick} className={`relative flex flex-col items-center gap-1 transition-all ${active ? 'text-red-600 scale-110' : 'text-slate-300 hover:text-slate-500'}`}>
                <Icon name={icon} size={24} strokeWidth={active ? 2.5 : 2} />
                <span className="text-[8px] font-black uppercase tracking-tighter">{label}</span>
                {count > 0 && <span className="absolute -top-1 -right-1 bg-red-600 text-white text-[8px] font-black w-4 h-4 rounded-full flex items-center justify-center ring-2 ring-white">{count}</span>}
            </button>
        );

        const AddView = ({ onAdd, onCancel, initialName }) => {
            const [mode, setMode] = useState('manual');
            const [name, setName] = useState(initialName || '');
            const [expiry, setExpiry] = useState('');
            const [category, setCategory] = useState('Altro');
            const [barcode, setBarcode] = useState('');

            const handleSubmit = (e) => {
                if(e) e.preventDefault();
                if (!name) return;
                onAdd({ name, expiry, category, barcode });
            };

            return (
                <div className="space-y-8 animate-in fade-in zoom-in-95 duration-300">
                    <div className="flex bg-slate-100 p-1.5 rounded-3xl mb-4 shadow-inner">
                        <button onClick={() => setMode('manual')} className={`flex-1 py-3 rounded-2xl text-xs font-black transition-all uppercase tracking-widest ${mode === 'manual' ? 'bg-white shadow-sm text-red-600' : 'text-slate-400'}`}>Manuale</button>
                        <button onClick={() => setMode('scan')} className={`flex-1 py-3 rounded-2xl text-xs font-black transition-all uppercase tracking-widest ${mode === 'scan' ? 'bg-white shadow-sm text-red-600' : 'text-slate-400'}`}>Scanner</button>
                    </div>

                    {mode === 'scan' ? (
                        <div className="space-y-6">
                            <div id="reader" className="overflow-hidden rounded-[3rem] border-8 border-slate-50 bg-slate-100 min-h-[300px] shadow-2xl relative">
                                <div className="absolute inset-0 border-[2px] border-red-500/30 animate-pulse pointer-events-none rounded-[2.5rem] m-8"></div>
                            </div>
                            <ScannerComponent onResult={(res) => { setBarcode(res); setMode('manual'); }} />
                            <button onClick={() => setMode('manual')} className="w-full py-5 text-slate-400 font-black text-xs uppercase tracking-widest bg-slate-100 rounded-[2rem]">Annulla e usa manuale</button>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-8">
                            <div className="space-y-6">
                                <div>
                                    <label className="text-[10px] font-black text-slate-300 uppercase tracking-[0.3em] mb-3 block px-2">Cos'è?</label>
                                    <input autoFocus type="text" required value={name} onChange={e => setName(e.target.value)} className="w-full bg-slate-50 border-4 border-slate-50 rounded-[2rem] px-6 py-5 font-black text-xl focus:bg-white focus:border-red-100 outline-none transition-all placeholder:text-slate-200" placeholder="Esempio: Mele..." />
                                </div>
                                <div className="space-y-6">
                                    <label className="text-[10px] font-black text-slate-300 uppercase tracking-[0.3em] mb-2 block px-2">Categoria</label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {Object.keys(CATEGORY_MAP).map(cat => (
                                            <button key={cat} type="button" onClick={() => setCategory(cat)} className={`p-3 rounded-2xl border-2 flex flex-col items-center gap-1 transition-all ${category === cat ? 'border-red-500 bg-red-50 text-red-600' : 'border-slate-50 bg-slate-50 text-slate-400'}`}>
                                                <Icon name={CATEGORY_MAP[cat].icon} size={20} />
                                                <span className="text-[8px] font-black uppercase truncate w-full text-center">{cat}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div>
                                    <label className="text-[10px] font-black text-slate-300 uppercase tracking-[0.3em] mb-3 block px-2">Data Scadenza</label>
                                    <input type="date" value={expiry} onChange={e => setExpiry(e.target.value)} className="w-full bg-slate-50 border-4 border-slate-50 rounded-[2rem] px-6 py-5 font-black text-lg focus:bg-white focus:border-red-100 outline-none transition-all" />
                                </div>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button type="button" onClick={onCancel} className="flex-1 py-6 text-slate-400 font-black uppercase tracking-widest bg-slate-100 rounded-[2rem] text-xs">Annulla</button>
                                <button type="submit" className="flex-1 py-6 bg-gradient-to-r from-red-600 to-rose-500 text-white font-black uppercase tracking-widest rounded-[2rem] shadow-xl shadow-red-200 text-xs text-center">AGGIUNGI</button>
                            </div>
                        </form>
                    )}
                </div>
            );
        };

        const ScannerComponent = ({ onResult }) => {
            useEffect(() => {
                const html5QrCode = new Html5Qrcode("reader");
                html5QrCode.start({ facingMode: "environment" }, { fps: 15, qrbox: 250 }, (decodedText) => { html5QrCode.stop().then(() => onResult(decodedText)); }).catch(err => console.error(err));
                return () => { if(html5QrCode.isScanning) html5QrCode.stop().catch(e => console.log(e)); };
            }, []);
            return null;
        };

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
