"""HTTP acceptance for real OpenShift HTTPS Route; never exposes backend/database."""
import argparse
import json
import re
import time
import urllib.error
import urllib.request

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--base-url", required=True, help="https://<host> from oc get route m10-frontend")
args=p.parse_args()
base=args.base_url.rstrip("/")
if not base.startswith("https://"):
    raise SystemExit("Only the edge-TLS frontend HTTPS Route is accepted")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

client=urllib.request.build_opener(NoRedirect)

def request(method,path,data=None):
    req=urllib.request.Request(base+path,method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type":"application/json"} if data is not None else {})
    try:
        with client.open(req,timeout=12) as r:
            return r.status,r.read(),r.headers
    except urllib.error.HTTPError as e:
        return e.code,e.read(),e.headers

until=time.monotonic()+90
while time.monotonic()<until:
    try:
        code,data,_=request("GET","/api/status")
        if code==200 and all(json.loads(data).values()): break
    except (OSError,KeyError,ValueError): pass
    time.sleep(2)
else:
    raise SystemExit("Not all four OpenShift services ready; inspect oc get pods and Service/Secret config")
print("PASS frontend/backend/database/redirector ready through HTTPS Route")
status,raw,_=request("GET","/")
assert status==200 and b"Shorties" in raw
bad,_,_=request("POST","/api/shorten",{"url":"ftp://invalid.example"})
assert bad==400,bad
target="https://example.org/openshift/js/learning"
status,raw,_=request("POST","/api/shorten",{"url":target})
assert status==201,(status,raw)
record=json.loads(raw)
assert re.fullmatch(r"[A-Za-z0-9_-]{7,12}",record["code"]),record
status,_,headers=request("GET",record["path"])
assert status==302 and headers.get("Location")==target,(status,headers)
print("PASS real OpenShift Route POST→C#-independent Node backend→PostgreSQL→Node redirector 302")
print("PASS Module 10 OpenShift full-stack acceptance complete; no external redirects followed")
