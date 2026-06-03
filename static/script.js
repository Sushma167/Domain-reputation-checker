async function checkDomain(){

    let domain =
        document.getElementById("domainInput").value;

    let res =
        await fetch(`/domain/${domain}`);

    let data =
        await res.json();

    let html = `
    <div class="row">

        <div class="col-md-4">
            <div class="result-card">
                <h5>SPF</h5>
                <p>${data.spf.length}</p>
            </div>
        </div>

        <div class="col-md-4">
            <div class="result-card">
                <h5>DMARC</h5>
                <p>${data.dmarc.length}</p>
            </div>
        </div>

        <div class="col-md-4">
            <div class="result-card">
                <h5>MX</h5>
                <p>${data.mx.length}</p>
            </div>
        </div>

    </div>
    `;

    document.getElementById(
        "domainResults"
    ).innerHTML = html;
}

async function checkIP(){

    let ip =
        document.getElementById("ipInput").value;

    let res =
        await fetch(`/ip/${ip}`);

    let data =
        await res.json();

    let html = "";

    for(let k in data){

        html += `
        <div class="result-card">
            <strong>${k}</strong> :
            ${data[k]}
        </div>
        `;
    }

    document.getElementById(
        "ipResults"
    ).innerHTML = html;
}

async function bulkScan(){

    let cidr =
        document.getElementById("cidrInput").value;

    let res =
        await fetch(`/bulk/${cidr}`);

    let data =
        await res.json();

    let html = `
    <table class="table table-dark">

    <tr>
        <th>IP</th>
        <th>Status</th>
    </tr>
    `;

    data.forEach(row => {

        html += `
        <tr>
            <td>${row.ip}</td>
            <td>${row.status}</td>
        </tr>
        `;
    });

    html += "</table>";

    document.getElementById(
        "bulkResults"
    ).innerHTML = html;
}
