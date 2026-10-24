import os
import requests, time, threading
from datetime import datetime
try:
    cfg=dict(l.split("=",1) for l in open("config.env") if "=" in l)
except:
    cfg={}
TOKEN=os.getenv("BOT_TOKEN") or cfg.get("TOKEN","").strip()
CHAT_ID=os.getenv("CHAT_ID") or cfg.get("CHAT_ID","").strip()

def send(p):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":p}, timeout=20)
    except:
        pass

def get_5m(tk):
    try:
        r=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}?range=1d&interval=5m", headers={"User-Agent":"Mozilla/5.0"}, timeout=12).json()
        q=r["chart"]["result"][0]["indicators"]["quote"][0]
        return q["open"],q["high"],q["low"],q["close"],q["volume"]
    except:
        return None

def cek(tk):
    cde=tk.replace(".JK","")
    d=get_5m(tk)
    if not d:
        return None
    o,h,l,c,v=d
    data=[(o[i],h[i],l[i],c[i],v[i]) for i in range(len(c)) if None not in (o[i],h[i],l[i],c[i],v[i])]
    if len(data)<3:
        return None
    o,h,l,c,v=zip(*data)
    last=c[-1]
    if last<=20 or last>=5000:
        return None
    cum_pv=cum_v=0
    vwap=[]
    for i in range(len(c)):
        tp=(h[i]+l[i]+c[i])/3
        cum_pv+=tp*v[i]
        cum_v+=v[i]
        vwap.append(cum_pv/cum_v if cum_v else c[i])
    pct=(c[-1]/c[-2]-1)*100 if c[-2] else 0
    if c[-1]>vwap[-1] and vwap[-1]>vwap[-2] and o[-1]==l[-1] and c[-1]>o[-1] and c[-1]>c[-2]*1.02 and v[-1]>0:
        return {"code":cde,"price":int(last),"pct":pct,"tp":int(last*1.06)}
    return None

IDX=[x.strip() for x in open("idx_full.txt").read().split() if ".JK" in x]

def do_scan():
    now=datetime.now().strftime("%d-%m %H:%M WIB")
    hits=[]
    for tk in IDX:
        res=cek(tk)
        if res:
            hits.append(res)
        time.sleep(0.2)
    if not hits:
        send(f"📭 SCAN SELESAI {len(IDX)} saham\n⏰ {now}\nTidak ada O=L supertrend\n(Wajar Sabtu bursa tutup) 😴")
    else:
        hits=sorted(hits, key=lambda x: x["pct"], reverse=True)
        msg=f"🔥🔥🔥 {len(hits)} SAHAM POTENSIAL KETEMU 🔥🔥🔥\n⏰ {now} | 📈 IDX LIVE\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for i,s in enumerate(hits,1):
            msg+=f"{i}️⃣ {s['code']} - Rp{s['price']}\n🔥 O=L supertrend | +{s['pct']:.1f}%\n🚀 ENTRY KUY 🫵 | TP Rp{s['tp']} (+6%)\n\n"
        send(msg)

last=0
send("✅ Bot DUOBIE FINAL ON\n491 saham | 🔥 O=L supertrend\n🚀 ENTRY KUY 🫵\nKetik /test /scanall /start")

while True:
    try:
        r=requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last+1}&timeout=10", timeout=20).json()
        for upd in r.get("result",[]):
            last=upd["update_id"]
            txt=upd.get("message",{}).get("text","").lower()
            if "/test" in txt:
                now=datetime.now().strftime("%d-%m %H:%M WIB")
                msg=f"🔥🔥🔥 3 SAHAM POTENSIAL KETEMU 🔥🔥🔥\n⏰ {now} | 📈 IDX LIVE [TEST LUCU]\n━━━━━━━━━━━━━━━━━━━━\n\n"
                msg+=f"1️⃣ KBLM - Rp374\n🔥 O=L supertrend | +8.7%\n🚀 ENTRY KUY 🫵 | TP Rp396 (+6%)\n\n"
                msg+=f"2️⃣ BREN - Rp7200\n🔥 O=L supertrend | +5.2%\n🚀 ENTRY KUY 🫵 | TP Rp7632 (+6%)\n\n"
                msg+=f"3️⃣ CUAN - Rp12500\n🔥 O=L supertrend | +3.8%\n🚀 ENTRY KUY 🫵 | TP Rp13250 (+6%)\n\n"
                msg+=f"✨ Ini contoh format cantik pas market buka ya bos ✨"
                send(msg)
            elif "/start" in txt:
                send("👋 Bot siap bos!\n/test = cek format lucu 🔥\n/scanall = scan 491 saham real 📈")
            elif "/scanall" in txt:
                send(f"🔎 SCANNING {len(IDX)} SAHAM...\n⏰ {datetime.now().strftime('%d-%m %H:%M WIB')}\nTunggu 2 menit ya... ☕")
                threading.Thread(target=do_scan, daemon=True).start()
    except Exception as e:
        print(e)
    time.sleep(2)
