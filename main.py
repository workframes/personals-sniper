import requests, json, time, threading, random
from urllib3.exceptions import InsecureRequestWarning

settings = json.load(open("settings.json", "r"))

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

session = requests.session()
session.cookies['.ROBLOSECURITY'] = settings["cookie"]

token = "abcabcabc"
payload = [{ "itemType": "Asset", "id": id } for id in settings["items"]]
cache = []

def refresh_tokens():
    while True:
        _set_auth()
        time.sleep(150)

def generate_watch_preflight():
    watch_preflight_octets = [random.randint(0, 255) for _ in range(4)]
    preflight_address = ".".join(str(octet) for octet in watch_preflight_octets)
    return preflight_address

def _set_auth():
    global token, session
    try:
        conn = session.post("https://auth.roblox.com/v2/logout")
        if conn.headers.get("x-csrf-token"):
            token = conn.headers["x-csrf-token"]
    except:
        time.sleep(5)
        return _set_auth()
    
def get_product_id(id):
    try:
        conn = session.get(f"https://economy.roblox.com/v2/assets/{id}/details", verify=False)
        data = conn.json()

        if conn.status_code == 200:
            return  {
                "id": data["ProductId"],
                "creator": data["Creator"]["Id"]
            }
        else:
            time.sleep(1)
            return get_product_id(id)
    except:
        time.sleep(1)
        return get_product_id(id)

def buy_item(product_id, seller_id, price):
    try:
        body = {
            "expectedCurrency": 1,
            "expectedPrice": price,
            "expectedSellerId": seller_id
        }
        headers = {
            "x-csrf-token": token,
            "x-forwarded-for": str(generate_watch_preflight())
        }
        conn = session.post(f"https://economy.roblox.com/v1/purchases/products/{product_id}", headers=headers, json=body)
        data = conn.json()
        if conn.status_code == 200:
            if ("purchased" in data) and data["purchased"] == True:
                print(f"Bought {data['assetName']}")
        else:
            return buy_item(product_id, seller_id, price)
    except:
        return buy_item(product_id, seller_id, price)

def watcher():
    global token, session
    while True:
        try:
            headers = {
                "x-csrf-token": token,
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "X-Forwarded-For": str(generate_watch_preflight())
            }
            conn = session.post("https://catalog.roblox.com/v1/catalog/items/details", json={ "items": payload }, headers=headers, verify=False)

            data = conn.json()
            if conn.status_code == 200:
                if "data" in data:
                    for item in data["data"]:
                        if "price" in item and not item["id"] in cache and not item["price"] > settings["items"][str(item["id"])]:
                            cache.append(item["id"])
                            r_data = get_product_id(item["id"])
                            print("Buying item")
                            buy_item(r_data["id"], r_data["creator"], item["price"])
            elif conn.status_code == 403:
                _set_auth()
        except:
            pass
        time.sleep(1)


if __name__ == '__main__':
    threading.Thread(target=refresh_tokens,).start()
    threading.Thread(target=watcher,).start()
