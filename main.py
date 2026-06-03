from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import dns.resolver
import ipaddress
import socket

app = FastAPI(title="Domain Reputation Checker")

app.mount("/static", StaticFiles(directory="static"), name="static")

DNSBLS = {
    "Spamhaus": "zen.spamhaus.org",
    "Spamcop": "bl.spamcop.net",
    "Barracuda": "b.barracudacentral.org"
}

# ---------------------------
# HOME
# ---------------------------
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# ---------------------------
# SPF
# ---------------------------
def get_spf(domain):
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        for record in answers:
            txt = "".join(
                s.decode() if isinstance(s, bytes) else str(s)
                for s in record.strings
            )
            if "v=spf1" in txt.lower():
                return txt
    except:
        pass
    return "NOT_FOUND"

# ---------------------------
# DMARC
# ---------------------------
def get_dmarc(domain):
    try:
        answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
        for record in answers:
            txt = "".join(
                s.decode() if isinstance(s, bytes) else str(s)
                for s in record.strings
            )
            if "v=dmarc1" in txt.lower():
                return txt
    except:
        pass
    return "NOT_FOUND"

# ---------------------------
# BLACKLIST CHECK
# ---------------------------
def check_blacklists(ip):
    reversed_ip = ".".join(reversed(ip.split(".")))
    results = {}

    for name, zone in DNSBLS.items():
        try:
            query = f"{reversed_ip}.{zone}"
            answers = dns.resolver.resolve(query, "A")

            results[name] = {
                "listed": True,
                "codes": [str(a) for a in answers]
            }

        except dns.resolver.NXDOMAIN:
            results[name] = {"listed": False}

        except Exception as e:
            results[name] = {"error": str(e)}

    return results

# ---------------------------
# MX
# ---------------------------
def get_mx(domain):
    records = []

    try:
        mx_records = dns.resolver.resolve(domain, "MX")

        for mx in mx_records:
            host = str(mx.exchange).rstrip(".")
            ips = []

            try:
                a_records = dns.resolver.resolve(host, "A")

                for a in a_records:
                    ip = str(a)
                    ips.append({
                        "ip": ip,
                        "blacklists": check_blacklists(ip)
                    })

            except:
                pass

            records.append({
                "host": host,
                "priority": mx.preference,
                "ips": ips
            })

    except:
        pass

    return records

# ---------------------------
# DOMAIN API
# ---------------------------
@app.get("/domain/{domain}")
async def domain_check(domain: str):
    return {
        "domain": domain,
        "spf": get_spf(domain),
        "dmarc": get_dmarc(domain),
        "mx": get_mx(domain)
    }

# ---------------------------
# SINGLE IP
# ---------------------------
@app.get("/ip/{ip}")
async def ip_check(ip: str):
    return {
        "ip": ip,
        "blacklists": check_blacklists(ip)
    }

# ---------------------------
# BULK IP (/24 max safe)
# ---------------------------
@app.get("/bulk/{cidr:path}")
async def bulk_scan(cidr: str):

    network = ipaddress.ip_network(cidr, strict=False)

    if network.num_addresses > 256:
        return {"error": "Max range allowed is /24 only"}

    results = []

    for ip in network.hosts():
        ip = str(ip)

        bl = check_blacklists(ip)

        status = "CLEAN"
        if any(v.get("listed") for v in bl.values()):
            status = "LISTED"

        results.append({
            "ip": ip,
            "status": status,
            "blacklists": bl
        })

    return {
        "range": cidr,
        "results": results
    }
