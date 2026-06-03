function loader(){
    return `<div class="card loading">Scanning...</div>`;
}

// ---------------- DOMAIN ----------------
async function checkDomain(){

    document.getElementById("domainResults").innerHTML = loader();

    try {
        let domain = document.getElementById("domainInput").value.trim();

        let res = await fetch(`/domain/${domain}`);
        let data = await res.json();

        let spf = (data.spf && data.spf !== "NOT_FOUND") ? data.spf : "NOT FOUND";
        let dmarc = (data.dmarc && data.dmarc !== "NOT_FOUND") ? data.dmarc : "NOT FOUND";
        let mxCount = Array.isArray(data.mx) ? data.mx.length : 0;

        let html = `
        <div class="card">
            <h4>SPF Record</h4>
            <p>${spf}</p>
        </div>

        <div class="card">
            <h4>DMARC Record</h4>
            <p>${dmarc}</p>
        </div>

        <div class="card">
            <h4>MX Records</h4>
            <p>${mxCount}</p>
        </div>
        `;

        document.getElementById("domainResults").innerHTML = html;

    } catch (err) {
        document.getElementById("domainResults").innerHTML =
            `<div class="card status-bad">Error loading domain data</div>`;
    }
}


// ---------------- IP ----------------
async function checkIP(){

    document.getElementById("ipResults").innerHTML = loader();

    try {

        let ip = document.getElementById("ipInput").value.trim();

        let res = await fetch(`/ip/${ip}`);
        let data = await res.json();

        let html = `<div class="card"><h4>IP: ${data.ip || ip}</h4></div>`;

        let bl = data.blacklists || {};

        let hasData = Object.keys(bl).length > 0;

        if(!hasData){
            document.getElementById("ipResults").innerHTML =
                `<div class="card status-warn">No blacklist data found</div>`;
            return;
        }

        for(let k in bl){

            let r = bl[k];

            let status = "UNKNOWN";
            let color = "status-warn";

            // FIXED SAFE CHECKING
            if(r && r.listed === true){
                status = "LISTED";
                color = "status-bad";
            }
            else if(r && r.listed === false){
                status = "CLEAN";
                color = "status-good";
            }
            else if(r && r.error){
                status = "ERROR";
                color = "status-warn";
            }

            html += `
            <div class="card">
                <b>${k}</b>
                <div class="${color}">${status}</div>
            </div>
            `;
        }

        document.getElementById("ipResults").innerHTML = html;

    } catch (err) {
        document.getElementById("ipResults").innerHTML =
            `<div class="card status-bad">IP lookup failed</div>`;
    }
}


// ---------------- BULK ----------------
async function bulkScan(){

    document.getElementById("bulkResults").innerHTML = loader();

    try {

        let cidr = document.getElementById("cidrInput").value.trim();

        let res = await fetch(`/bulk/${cidr}`);
        let data = await res.json();

        if(data.error){
            document.getElementById("bulkResults").innerHTML =
                `<div class="card status-bad">${data.error}</div>`;
            return;
        }

        let html = `
        <div class="card">
        <table class="table">
            <tr><th>IP</th><th>Status</th></tr>
        `;

        (data.results || []).forEach(r => {

            let color = r.status === "LISTED" ? "status-bad" : "status-good";

            html += `
            <tr>
                <td>${r.ip}</td>
                <td class="${color}">${r.status}</td>
            </tr>
            `;
        });

        html += "</table></div>";

        document.getElementById("bulkResults").innerHTML = html;

    } catch (err) {
        document.getElementById("bulkResults").innerHTML =
            `<div class="card status-bad">Bulk scan failed</div>`;
    }
}
function loader(){
    return `<div class="card">Scanning...</div>`;
}

// -----------------------------
// THEME SYSTEM (FIXED)
// -----------------------------

function setTheme(mode){
    document.body.classList.remove("light", "dark");
    document.body.classList.add(mode);
    localStorage.setItem("theme", mode);
}

function toggleTheme(){
    let current = localStorage.getItem("theme") || "dark";
    let newTheme = current === "dark" ? "light" : "dark";
    setTheme(newTheme);
}

// Load theme on startup
(function(){
    let saved = localStorage.getItem("theme") || "dark";
    setTheme(saved);
})();
