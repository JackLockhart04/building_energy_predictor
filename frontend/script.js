let buildings = [];
let selected = null;
let histories = { xgb: [], lr: [] };
let charts = { xgb: null, lr: null };

async function init() {
    const res = await fetch('../buildings/building_data.csv');
    const text = await res.text();
    buildings = text.split('\n').slice(1).filter(r => r.trim()).map(row => {
        const [name, floors, usage, sqft, sub_usage, year] = row.split(',').map(i => i.trim());
        return { name, floors, usage, sqft, sub_usage, year };
    });
    const now = new Date();
    const localNow = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
    document.getElementById('prediction-date').value = localNow;
}

async function runPredict(isDay = false) {
    if (!selected) return;
    const timeInput = document.getElementById('prediction-date').value; 
    
    const payload = {
        prediction_time: timeInput,
        sqft: parseFloat(selected.sqft),
        primary_space_usage: selected.usage, 
        sub_type: selected.sub_usage,
        year_built: parseFloat(selected.year), 
        number_of_floors: parseFloat(selected.floors)
    };

    const suffix = isDay ? 'predict_day' : 'predict';

    try {
        const [xgbR, lrR] = await Promise.all([
            fetch(`http://127.0.0.1:8000/${suffix}/xgboost`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            }),
            fetch(`http://127.0.0.1:8000/${suffix}/linear`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })
        ]);

        const xgbData = await xgbR.json();
        const lrData = await lrR.json();

        document.getElementById('forecast-container').classList.remove('hidden');
        updateSide('xgb', isDay ? xgbData : [xgbData], isDay);
        updateSide('lr', isDay ? lrData : [lrData], isDay);
    } catch (e) { console.error(e); }
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
init();