import requests, json, time, threading, random, os
from urllib3.exceptions import InsecureRequestWarning

settings = json.load(open("settings.json", "r"))

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

session = requests.session()
session.cookies['.ROBLOSECURITY'] = settings["cookie"]

token = None
payload = [{ "itemType": "Asset", "id": id } for id in settings["items"]]
cache = []

logs = []
checks = 0

def refresh_tokens():
    while True:
        _set_auth()
        time.sleep(150)

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
    global logs

    try:
        body = {
            "expectedCurrency": 1,
            "expectedPrice": price,
            "expectedSellerId": seller_id
        }
        headers = {
            "x-csrf-token": token,
        }
        conn = session.post(f"https://economy.roblox.com/v1/purchases/products/{product_id}", headers=headers, json=body)
        data = conn.json()
        if conn.status_code == 200:
            if ("purchased" in data) and data["purchased"] == True:
                logs.append(f"Bought {data['assetName']}")
        else:
            return buy_item(product_id, seller_id, price)
    except:
        return buy_item(product_id, seller_id, price)

def status_update():
    global checks, logs

    while True:
        print("made by frames, discord.gg/mewt")
        print(f"Checks: {checks}")
        print(f"Logs: \n" + "\n".join(log for log in logs[-10:]))

        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear')

def watcher():
    global token, session, checks, logs
    while True:
        try:
            headers = {
                "x-csrf-token": token,
                "cache-control": "no-cache",
                "pragma": "no-cache",
            }
            conn = session.post("https://catalog.roblox.com/v1/catalog/items/details", json={ "items": payload }, headers=headers, verify=False)

            data = conn.json()
            if conn.status_code == 200:
                checks+= 1
                if "data" in data:
                    for item in data["data"]:
                        if "price" in item and not item["id"] in cache and not int(item.get("price", 0)) > int(settings["items"].get(str(item["id"]), 0)):
                            cache.append(item["id"])
                            r_data = get_product_id(item["id"])
                            logs.append("Buying item")
                            buy_item(r_data["id"], r_data["creator"], item["price"])
            elif conn.status_code == 403:
                logs.append('force refreshing auth token')
                _set_auth()
            else:
                logs.append(f"{data}, status: {conn.status_code}")
        except Exception as error:
            logs.append(str(error))
            pass
        time.sleep(settings["watch_speed"])


if __name__ == '__main__':
    threading.Thread(target=refresh_tokens,).start()
    print("Waiting to fetch token, restart if it takes too long")
    while token == None:
        time.sleep(1)
    print("Fetched token")
    threading.Thread(target=status_update,).start()
    threading.Thread(target=watcher,).start()
