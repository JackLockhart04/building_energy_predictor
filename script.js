import { Client } from "https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js";

let client = null;
let buildings = [];
let selected = null;
let histories = { xgb: [], lr: [] };
let charts = { xgb: null, lr: null };

async function init() {
    try {
        console.log("Connecting to Hugging Face...");
        
        // This will now work because 'Client' is imported above
        client = await Client.connect("JackRabbit14/ua_electricity_prediction_engine");
        console.log("Connected to Hugging Face Backend");

        // Your CSV loading code
        // IMPORTANT: In a module, the path is relative to the SCRIPT file location
        const res = await fetch('../buildings/building_data.csv'); 
        const text = await res.text();
        
        buildings = text.split('\n').slice(1).filter(r => r.trim()).map(row => {
            const [name, floors, usage, sqft, sub_usage, year] = row.split(',').map(i => i.trim());
            return { name, floors, usage, sqft, sub_usage, year };
        });

        const now = new Date();
        const localNow = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
        document.getElementById('prediction-date').value = localNow;
        
    } catch (err) {
        console.error("Initialization Error:", err);
    }
}

async function runPredict(isDay = false) {
    if (!selected || !client) return;

    const timeInput = document.getElementById('prediction-date').value; 
    const modeLabel = isDay ? "Full Day" : "Single Hour";

    const payload = {
        prediction_time: timeInput,
        sqft: parseFloat(selected.sqft),
        usage: selected.usage,
        sub_type: selected.sub_usage,
        year: parseFloat(selected.year),
        floors: parseFloat(selected.floors),
        model_choice: "XGBoost",
        mode: modeLabel
    };

    try {
        const [xgbRes, lrRes] = await Promise.all([
            client.predict("/predict_json", [payload]),
            client.predict("/predict_json", [{ ...payload, model_choice: "Linear Regression" }])
        ]);

        // Gradio returns data[0] for the JSON output
        const xgbData = xgbRes.data[0];
        const lrData = lrRes.data[0];

        document.getElementById('forecast-container').classList.remove('hidden');
        updateSide('xgb', xgbData, isDay);
        updateSide('lr', lrData, isDay);

    } catch (e) {
        console.error("Prediction Error:", e);
    }
}

function updateSide(type, data, isDay) {
    const total = data.reduce((sum, item) => sum + item.kwh, 0);
    const displayVal = isDay ? total.toFixed(1) : data[0].kwh.toFixed(2);
    
    document.getElementById(`${type}-kwh`).innerText = `${displayVal} kWh`;
    const temp = isDay ? (data.reduce((s,i)=>s+i.temp,0)/24).toFixed(0) : data[0].temp.toFixed(0);
    document.getElementById(`${type}-weather`).innerText = `Temp: ${temp}°F`;

    document.getElementById(`${type}-list`).innerHTML = data.map(d => `
        <div class="hour-card">
            <span>${d.time}</span>
            <b>${d.kwh.toFixed(1)} kWh</b>
            <span style="color:#e67e22">${d.temp.toFixed(0)}°</span>
        </div>
    `).join('');

    const chartBox = document.getElementById(`${type}-chart-box`);
    if (isDay) {
        chartBox.classList.remove('hidden');
        renderChart(type, data);
    } else {
        chartBox.classList.add('hidden');
    }
    
    // Pass the building name and the prediction type to the history function
    addHistory(type, selected.name, displayVal, isDay);
}

function renderChart(type, data) {
    const ctx = document.getElementById(`${type}Chart`).getContext('2d');
    if (charts[type]) charts[type].destroy();

    charts[type] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.time),
            datasets: [{
                data: data.map(d => d.kwh),
                borderColor: type === 'xgb' ? '#9e1b32' : '#444',
                borderWidth: 2,
                fill: false, tension: 0.3, pointRadius: 0
            }]
        },
        options: { 
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { ticks: { display: false } }, y: { beginAtZero: true, ticks: { callback: (v) => v + ' kWh' } } }
        }
    });
}

function addHistory(type, name, val, isDay) {
    const typeLabel = isDay ? "Daily" : "Hourly";
    histories[type].unshift({ name, val, typeLabel });
    
    document.getElementById(`${type}-history`).innerHTML = histories[type].slice(0, 5).map(h => `
        <div class="history-item">
            <span>${h.name}: <b>${h.val} kWh</b> (${h.typeLabel})</span>
        </div>
    `).join('');
}

document.getElementById('search').oninput = (e) => {
    const val = e.target.value.toLowerCase();
    const list = document.getElementById('results');
    if (val.length < 1) return list.classList.add('hidden');
    const matches = buildings.filter(b => b.name.toLowerCase().includes(val)).slice(0, 5);
    list.innerHTML = matches.map(b => `<div class="item" data-name="${b.name}">${b.name}</div>`).join('');
    list.classList.remove('hidden');
    document.querySelectorAll('.item').forEach(el => {
        el.onclick = () => {
            selected = buildings.find(b => b.name === el.dataset.name);
            document.getElementById('search').value = selected.name;
            document.getElementById('b-name').innerText = selected.name;
            document.getElementById('b-sqft').innerText = Number(selected.sqft).toLocaleString();
            document.getElementById('b-year').innerText = selected.year;
            document.getElementById('b-floors').innerText = selected.floors;
            document.getElementById('details').classList.remove('hidden');
            list.classList.add('hidden');
        };
    });
};

document.getElementById('predict-hour-btn').onclick = () => runPredict(false);
document.getElementById('predict-day-btn').onclick = () => runPredict(true);
init().catch(console.error);