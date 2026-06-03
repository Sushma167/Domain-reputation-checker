async function checkDomain(){

    let domain =
        document.getElementById("domain").value;

    let response =
        await fetch(`/domain/${domain}`);

    let data =
        await response.json();

    document.getElementById("result")
        .innerHTML =
        `<pre>${JSON.stringify(data,null,4)}</pre>`;
}


async function checkIP(){

    let ip =
        document.getElementById("ip").value;

    let response =
        await fetch(`/ip/${ip}`);

    let data =
        await response.json();

    document.getElementById("ipresult")
        .innerHTML =
        `<pre>${JSON.stringify(data,null,4)}</pre>`;
}
