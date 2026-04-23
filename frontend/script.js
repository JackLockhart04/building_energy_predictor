let buildings = [];
let selected = null;
let predictionHistory = [];

const BUILDING_CSV_PATH = '../buildings/building_data.csv';
const API_URL = 'http://127.0.0.1:8000/predict';

/**
 * Load and Parse CSV Data
 */
async function init() {
    try {
        const res = await fetch(BUILDING_CSV_PATH);
        const text = await res.text();
        
        buildings = text.split('\n').slice(1).filter(r => r.trim()).map(row => {
            const [name, floors, usage, sqft, sub_usage, year] = row.split(',').map(item => item.trim());
            return { name, floors, usage, sqft, sub_usage, year };
        });
        console.log(`Loaded ${buildings.length} buildings.`);
    } catch (err) {
        console.error("Data Load Error:", err);
    }
}

/**
 * Handle Live Search
 */
function handleSearch(e) {
    const val = e.target.value.toLowerCase();
    const list = document.getElementById('results');
    
    if (val.length < 1) {
        list.classList.add('hidden');
        return;
    }

    const matches = buildings.filter(b => b.name.toLowerCase().includes(val)).slice(0, 8);
    list.innerHTML = matches.map(b => `<div class="item" data-name="${b.name}">${b.name}</div>`).join('');
    list.classList.remove('hidden');

    document.querySelectorAll('.item').forEach(el => {
        el.onclick = () => select(buildings.find(b => b.name === el.dataset.name));
    });
}

/**
 * Select Building and Update UI
 */
function select(b) {
    selected = b;
    console.log("Selected:", selected);
    
    document.getElementById('results').classList.add('hidden');
    document.getElementById('search').value = b.name;
    
    document.getElementById('b-name').innerText = b.name;
    document.getElementById('b-sqft').innerText = Number(b.sqft).toLocaleString();
    document.getElementById('b-year').innerText = b.year;
    document.getElementById('b-floors').innerText = b.floors;
    
    document.getElementById('details').classList.remove('hidden');
}

/**
 * Request Prediction from FastAPI
 */
async function requestPrediction() {
    if (!selected) return;

    const btn = document.getElementById('predict-btn');
    btn.innerText = "⌛ Processing...";
    btn.disabled = true;

    const now = new Date();
    
    const payload = {
        temperature_f: 72.0,           // Mock Temperature
        apparent_temperature_f: 75.0,
        temp_roll_3h: 70.0,
        hour: now.getHours(),
        day_week: now.getDay(),
        month: now.getMonth() + 1,
        sqft: parseFloat(selected.sqft),
        primary_space_usage: selected.usage,
        sub_type: selected.sub_usage,
        year_built: parseFloat(selected.year),
        number_of_floors: parseFloat(selected.floors)
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error("API Failure");

        const result = await response.json();
        const kwh = result.predicted_kwh.toFixed(2);
        
        // Update Current Result UI
        document.getElementById('current-kwh').innerText = `${kwh} kWh`;
        document.getElementById('history-container').classList.remove('hidden');

        // Add to History (Shift current to list, new to top)
        predictionHistory.unshift({
            name: selected.name,
            result: kwh,
            time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        });

        updateHistoryUI();
        btn.innerText = "Predict Energy Use";
        
    } catch (error) {
        console.error("Prediction Error:", error);
        btn.innerText = "❌ API Error";
    } finally {
        btn.disabled = false;
    }
}

/**
 * Update the History List UI
 */
function updateHistoryUI() {
    const list = document.getElementById('history-list');
    // Only show history items that aren't the very first/current one
    const historyData = predictionHistory.slice(1);
    
    list.innerHTML = historyData.map(item => `
        <div class="history-item">
            <span class="history-name">${item.name} <small style="color:#999; font-weight:400;">${item.time}</small></span>
            <span class="history-val">${item.result} kWh</span>
        </div>
    `).join('');
}

// Global Listeners
document.getElementById('search').oninput = handleSearch;
document.getElementById('predict-btn').onclick = requestPrediction;

// Run Init
init();