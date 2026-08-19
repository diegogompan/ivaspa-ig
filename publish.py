#!/usr/bin/env python3
"""
Publicador automatico de IVASPA en Instagram (Graph API).
Lee queue.json y publica el/los post(s) cuya hora ya ha llegado (hora de Madrid).
Publica como maximo 1 por ejecucion, para respetar el espaciado del feed.
Requiere variables de entorno:
  IG_ACCESS_TOKEN  - token de acceso de Pagina (no caduca) con permisos de publicacion
  IG_USER_ID       - ID de la cuenta de Instagram Business
  IMG_BASE_URL     - base publica de las imagenes (ej. https://raw.githubusercontent.com/USER/REPO/main/hosting_img)
"""
import os, json, time
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.request, urllib.parse

TOKEN   = os.environ.get("IG_ACCESS_TOKEN")
IG_USER = os.environ.get("IG_USER_ID")
IMG_BASE= (os.environ.get("IMG_BASE_URL") or "").rstrip("/")
GRAPH   = "https://graph.facebook.com/v21.0"
TZ      = ZoneInfo("Europe/Madrid")
QUEUE   = os.path.join(os.path.dirname(__file__), "queue.json")

def api(path, params, method="GET"):
    if method == "GET":
        url = f"{GRAPH}/{path}?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
    else:
        url = f"{GRAPH}/{path}"
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:300]}")

def container_image(img_url, caption):
    return api(f"{IG_USER}/media", {"image_url": img_url, "caption": caption, "access_token": TOKEN}, "POST")["id"]

def container_child(img_url):
    return api(f"{IG_USER}/media", {"image_url": img_url, "is_carousel_item": "true", "access_token": TOKEN}, "POST")["id"]

def container_carousel(children, caption):
    return api(f"{IG_USER}/media", {"media_type": "CAROUSEL", "children": ",".join(children),
                                     "caption": caption, "access_token": TOKEN}, "POST")["id"]

def publish(creation_id):
    return api(f"{IG_USER}/media_publish", {"creation_id": creation_id, "access_token": TOKEN}, "POST")

def main():
    if not (TOKEN and IG_USER and IMG_BASE):
        print("Secretos de Meta aún no configurados (IG_ACCESS_TOKEN / IG_USER_ID / IMG_BASE_URL). Nada que hacer.")
        return
    now = datetime.now(TZ)
    q = json.load(open(QUEUE, encoding="utf-8"))
    for post in q:
        if post["status"] != "pending":
            continue
        due = datetime.fromisoformat(post["datetime"]).replace(tzinfo=TZ)
        if due > now:
            break  # la cola esta ordenada por fecha; si este no toca, los siguientes tampoco
        try:
            if post["type"] == "image":
                cid = container_image(f"{IMG_BASE}/{post['images'][0]}", post["caption"])
                time.sleep(6)
                publish(cid)
            else:  # carousel
                children = []
                for name in post["images"]:
                    children.append(container_child(f"{IMG_BASE}/{name}"))
                    time.sleep(3)
                cid = container_carousel(children, post["caption"])
                time.sleep(6)
                publish(cid)
            post["status"] = "published"
            post["published_at"] = now.isoformat()
            print(f"OK  #{post['n']}  {post['id']}  ({post['type']})")
        except Exception as e:
            post["status"] = "error"
            post["error"] = str(e)
            print(f"ERROR  #{post['n']}  {post['id']}: {e}")
        json.dump(q, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return  # 1 post por ejecucion
    print("Nada pendiente para publicar ahora.")

if __name__ == "__main__":
    main()
