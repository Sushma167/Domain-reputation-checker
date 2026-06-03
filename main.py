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


# ---------------------------
# HOME PAGE
# ---------------------------

@app.get("/", response_class=HTMLResponse)
async def home():

    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------
# SPF CHECK
# ---------------------------

def get_spf(domain):

    try:

        answers = dns.resolver.resolve(domain, "TXT")

        for record in answers:

            txt = "".join(
                s.decode() if isinstance(s, bytes) else str(s)
                for s in record.strings
            )

            if txt.lower().startswith("v=spf1"):

                return {
                    "exists": True,
                    "record": txt
                }

    except:
        pass

    return {
        "exists": False
    }


# ---------------------------
# DMARC CHECK
# ---------------------------

def get_dmarc(domain):

    try:

        answers = dns.resolver.resolve(
            f"_dmarc.{domain}",
            "TXT"
        )

        for record in answers:

            txt = "".join(
                s.decode() if isinstance(s, bytes) else str(s)
                for s in record.strings
            )

            if txt.lower().startswith("v=dmarc1"):

                return {
                    "exists": True,
                    "record": txt
                }

    except:
        pass

    return {
        "exists": False
    }


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
                "codes": [str(x) for x in answers]
            }

        except dns.resolver.NXDOMAIN:

            results[name] = {
                "listed": False
            }

        except Exception as e:

            results[name] = {
                "error": str(e)
            }

    return results


# ---------------------------
# MX RECORDS
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
# DOMAIN CHECK API
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
# IP CHECK API
# ---------------------------

@app.get("/ip/{ip}")
async def ip_check(ip: str):

    return {
        "ip": ip,
        "blacklists": check_blacklists(ip)
    }


# ---------------------------
# RANGE CHECK API
# ---------------------------

@app.get("/range/{cidr}")
async def range_check(cidr: str):

    output = []

    network = ipaddress.ip_network(cidr)

    for ip in network.hosts():

        ip = str(ip)

        output.append({
            "ip": ip,
            "blacklists": check_blacklists(ip)
        })

    return output
