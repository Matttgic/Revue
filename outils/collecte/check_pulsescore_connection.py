#!/usr/bin/env python3
"""One-request PulseScore credential/entitlement smoke test.

Does not log/reproduce the API key or any odds, sportsbook customer data,
event names or provider responses. One read-only API call per manual/push run.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
import json,os,sys

URL="https://api.pulsescore.net/api/betclic/soccer/events?page=1&limit=1"
KEYS=("PULSESCORE_API_KEY","PULSESCORE_PRO_KEY","PULSE_SCORE_API_KEY")
OUT=Path("docs/pulsescore-connection-status.json")


def check(key:str|None,fetch=urlopen)->dict:
    result={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
            "provider":"PulseScore","resource":"betclic/soccer/events",
            "key_configured":bool(key),"status":"missing_secret","http_status":None,
            "event_count_first_page":None,
            "message":"Aucune clé PulseScore fournie au runner"}
    if not key:
        return result
    request=Request(URL,headers={"X-Secret":key,"Accept":"application/json"})
    try:
        with fetch(request,timeout=18) as response:
            result["http_status"]=getattr(response,"status",200)
            content=json.loads(response.read().decode("utf-8"))
        if not isinstance(content,dict) or not isinstance(content.get("events"),list):
            result["status"]="bad_schema"
            result["message"]="Le serveur a répondu mais pas avec le schéma événements attendu"
            return result
        result["status"]="connected"
        result["event_count_first_page"]=len(content["events"])
        result["message"]="Connexion authentifiée et schéma événements valide"
    except HTTPError as ex:
        result["http_status"]=ex.code
        if ex.code in (401,403):
            result["status"]="auth_or_entitlement_error"
            result["message"]="Clé rejetée ou accès au bookmaker/sport non inclus dans le plan"
        elif ex.code==429:
            result["status"]="rate_limited"
            result["message"]="Quota ou limitation de fréquence atteint"
        else:
            result["status"]="provider_http_error"
            result["message"]=f"HTTP {ex.code} reçu, sans divulgation de réponse"
    except (URLError,TimeoutError):
        result["status"]="network_error"
        result["message"]="Échec réseau / délai dépassé"
    except (ValueError,UnicodeDecodeError):
        result["status"]="bad_schema"
        result["message"]="Réponse non JSON valide"
    return result


def main():
    key=next((os.environ.get(k) for k in KEYS if os.environ.get(k)),None)
    result=check(key)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PULSESCORE_CONNECTION_STATUS="+result["status"])
    print("KEY_PRESENT="+str(result["key_configured"]).lower())
    print("HTTP_STATUS="+str(result["http_status"]))
    return 0


if __name__=="__main__":
    sys.exit(main())
