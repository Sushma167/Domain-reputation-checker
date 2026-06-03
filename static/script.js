// -----------------------------
// DOMAIN CHECK
// -----------------------------
async function checkDomain() {

    let domain = document.getElementById("domainInput").value;

    let res = await fetch(`/domain/${domain}`);
    let data = await res.json();

    let html = `
    <div class="row">

        <div class="col-md-4">
            <div class="result-card">
                <h5>SPF</h5>
                <p>${data.spf && data.spf !== "NOT_FOUND" ? "FOUND" : "NOT FOUND"}</p>
                <small>${data.spf && data.spf !== "NOT_FOUND" ? data.spf : ""}</small>
            </div>
        </div>

        <div class="col-md-4">
            <div class="result-card">
                <h5>DMARC</h5>
                <p>${data.dmarc && data.dmarc !== "NOT_FOUND" ? "FOUND" : "NOT FOUND"}</p>
                <small>${data.dmarc && data.dmarc !== "NOT_FOUND" ? data.dmarc : ""}</small>
            </div>
        </div>

        <div class="col-md-4">
            <div class="result-card">
                <h5>MX</h5>
                <p>${Array.isArray(data.mx) ? data.mx.length : 0}</p>
            </div>
        </div>

    </div>
    `;

    document.getElementById("domainResults").innerHTML = html;
}


// -----------------------------
// SINGLE IP CHECK (FIXED OBJECT ISSUE)
// -----------------------------
async function checkIP() {

    let ip = document.getElementById("ipInput").value;

    let res = await fetch(`/ip/${ip}`);
    let data = await res.json();

    let html = `<h4>IP: ${data.ip}</h4>`;

    let bl = data.blacklists;

    for (let key in bl) {

        let status = "UNKNOWN";

        if (bl[key].listed === true) status = "LISTED";
        else if (bl[key].listed === false) status = "CLEAN";
        else if (bl[key].error) status = "ERROR";

        let color =
            status === "LISTED" ? "red" :
            status === "CLEAN" ? "green" : "orange";

        html += `
        <div class="result-card">
            <strong>${key}</strong> :
            <span style="color:${color}">
                ${status}
            </span>
        </div>
        `;
    }

    document.getElementById("ipResults").innerHTML = html;
}


// -----------------------------
// BULK IP SCAN (FIXED SAFE VERSION)
// -----------------------------
async function bulkScan() {

    let cidr = document.getElementById("cidrInput").value;

    let res = await fetch(`/bulk/${cidr}`);
    let data = await res.json();

    let html = "";

    // ERROR HANDLING
    if (data.error) {
        document.getElementById("bulkResults").innerHTML =
            `<p style="color:red">${data.error}</p>`;
        return;
    }

    html += `
    <table class="table table-dark">
        <tr>
            <th>IP</th>
            <th>Status</th>
        </tr>
    `;

    data.results.forEach(row => {

        let color = row.status === "LISTED" ? "red" : "green";

        html += `
        <tr>
            <td>${row.ip}</td>
            <td style="color:${color}">
                ${row.status}
            </td>
        </tr>
        `;
    });

    html += "</table>";

    document.getElementById("bulkResults").innerHTML = html;
}
