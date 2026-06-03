function loader(){
    return `<div class="card">Scanning...</div>`;
}

// ---------------- DOMAIN ----------------
async function checkDomain(){

    document.getElementById("domainResults").innerHTML =
        `<div class="card">Scanning...</div>`;

    let domain = document.getElementById("domainInput").value;

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
}

// ---------------- IP ----------------
async function checkIP(){

    document.getElementById("ipResults").innerHTML = loader();

    let ip = document.getElementById("ipInput").value;

    let res = await fetch(`/ip/${ip}`);
    let data = await res.json();

    let html = `<div class="card"><h4>IP: ${data.ip}</h4></div>`;

    for(let k in data.blacklists){

        let r = data.blacklists[k];

        let status = "UNKNOWN";
        let cls = "status-warn";

        if(r.listed){ status="LISTED"; cls="status-bad"; }
        else if(r.listed===false){ status="CLEAN"; cls="status-good"; }
        else if(r.error){ status="ERROR"; cls="status-warn"; }

        html += `
        <div class="card">
            <b>${k}</b> :
            <span class="${cls}">${status}</span>
        </div>
        `;
    }

    document.getElementById("ipResults").innerHTML = html;
}

// ---------------- BULK ----------------
async function bulkScan(){

    document.getElementById("bulkResults").innerHTML = loader();

    let cidr = document.getElementById("cidrInput").value;

    let res = await fetch(`/bulk/${cidr}`);
    let data = await res.json();

    if(data.error){
        document.getElementById("bulkResults").innerHTML =
            `<div class="card status-bad">${data.error}</div>`;
        return;
    }

    let html = `
    <div class="card">
    <table class="table table-dark">
        <tr><th>IP</th><th>Status</th></tr>
    `;

    data.results.forEach(r=>{
        let color = r.status==="LISTED" ? "status-bad" : "status-good";

        html += `
        <tr>
            <td>${r.ip}</td>
            <td class="${color}">${r.status}</td>
        </tr>
        `;
    });

    html += "</table></div>";

    document.getElementById("bulkResults").innerHTML = html;
}
