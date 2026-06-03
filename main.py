from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

import dns.resolver
import ipaddress

app = FastAPI(title="Domain Reputation Checker")

app.mount("/static", StaticFiles(directory="static"), name="static")

DNSBLS = {
    "Spamhaus": "zen.spamhaus.org",
    "Spamcop": "bl.spamcop.net",
    "Barracuda": "b.barracudacentral.org"
}

# =========================
# HOME
# =========================
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# =========================
# SPF
# =========================
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

# =========================
# DMARC
# =========================
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

# =========================
# IP BLACKLIST (FIXED + CLASSIFIED)
# =========================
def check_blacklists(ip):

    try:
        parts = ip.split(".")
        if len(parts) != 4:
            return {"ERROR": "Invalid IP"}

        reversed_ip = ".".join(reversed(parts))
    except:
        return {"ERROR": "Invalid IP"}

    results = {}

    for name, zone in DNSBLS.items():

        try:
            query = f"{reversed_ip}.{zone}"
            answers = dns.resolver.resolve(query, "A")

            codes = [str(a) for a in answers]

            listed = False
            tags = []

            for code in codes:
                if not code.startswith("127.0.0."):
                    continue

                listed = True

                # =========================
                # SPAMHAUS CLASSIFICATION
                # =========================
                if name == "Spamhaus":

                    if code == "127.0.0.2":
                        tags.append("SBL")
                    elif code == "127.0.0.3":
                        tags.append("CSS")
                    elif code == "127.0.0.4":
                        tags.append("XBL")
                    elif code in ["127.0.0.10", "127.0.0.11"]:
                        tags.append("PBL")
                    else:
                        tags.append("LISTED")

                elif name == "Spamcop":
                    tags.append("SPAMCOP")

                elif name == "Barracuda":
                    tags.append("BARRACUDA")

                else:
                    tags.append("LISTED")

            if listed:
                results[name] = ", ".join(tags)
            else:
                results[name] = "CLEAN"

        except dns.resolver.NXDOMAIN:
            results[name] = "CLEAN"

        except Exception:
            results[name] = "ERROR"

    return results

# =========================
# MX RECORDS
# =========================
def get_mx(domain):

    output = []

    try:
        mx_records = dns.resolver.resolve(domain, "MX")

        for mx in mx_records:
            host = str(mx.exchange).rstrip(".")
            output.append(f"{host} (priority {mx.preference})")

    except:
        pass

    return output

# =========================
# DOMAIN API
# =========================
@app.get("/domain/{domain}")
async def domain_check(domain: str):

    return {
        "domain": domain,
        "spf": get_spf(domain),
        "dmarc": get_dmarc(domain),
        "mx": get_mx(domain)
    }

# =========================
# SINGLE IP API
# =========================
@app.get("/ip/{ip}")
async def ip_check(ip: str):

    return {
        "ip": ip,
        "blacklists": check_blacklists(ip)
    }

# =========================
# BULK SCAN (/24 max)
# =========================
@app.get("/bulk/{cidr:path}")
async def bulk_scan(cidr: str):

    try:
        network = ipaddress.ip_network(cidr, strict=False)

        if network.num_addresses > 256:
            return {"error": "Only /24 or smaller allowed"}

        results = []

        for ip in network.hosts():

            ip = str(ip)
            bl = check_blacklists(ip)

            status = "CLEAN"

            for v in bl.values():
                if v != "CLEAN" and v != "ERROR":
                    status = "LISTED"
                    break

            results.append({
                "ip": ip,
                "status": status,
                "blacklists": bl
            })

        return {
            "range": cidr,
            "results": results
        }

    except:
        return {"error": "Invalid CIDR range"}
