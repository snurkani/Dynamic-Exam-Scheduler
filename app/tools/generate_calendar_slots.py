from datetime import datetime, timedelta
import argparse
from app.db_sql import execute, query_all

# Gün isimlerini Python weekday() ile eşle:
# Monday=0 ... Sunday=6
WEEKDAY_MAP = {"PZT":0,"SAL":1,"ÇAR":2,"PER":3,"CUM":4,"CTS":5,"PAZ":6}

def parse_hhmm(s):
    return datetime.strptime(s, "%H:%M").time()

def daterange(d1, d2):
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="Başlangıç tarihi: YYYY-MM-DD")
    ap.add_argument("--end",   required=True, help="Bitiş tarihi: YYYY-MM-DD")
    ap.add_argument("--days",  required=True, help="Günler: örn 'PZT,SAL,ÇAR,PER,CUM'")
    ap.add_argument("--day-start", default="09:00", help="Gün başlangıcı (HH:MM)")
    ap.add_argument("--day-end",   default="18:00", help="Gün bitişi (HH:MM)")
    ap.add_argument("--exam-min",  type=int, default=75, help="Sınav süresi (dk)")
    ap.add_argument("--gap-min",   type=int, default=15, help="Slotlar arası boşluk (dk)")
    ap.add_argument("--clear", action="store_true", help="Eski exam_slots kayıtlarını temizle")
    args = ap.parse_args()

    if args.clear:
        execute("DELETE FROM exam_slots")

    d1 = datetime.strptime(args.start, "%Y-%m-%d").date()
    d2 = datetime.strptime(args.end,   "%Y-%m-%d").date()
    wanted = {WEEKDAY_MAP[g.strip().upper()] for g in args.days.split(",") if g.strip()}

    day_start = parse_hhmm(args.day_start)
    day_end   = parse_hhmm(args.day_end)

    created = 0
    for d in daterange(d1, d2):
        if d.weekday() not in wanted:
            continue
        # Günün zaman bandı
        cur = datetime.combine(d, day_start)
        stop = datetime.combine(d, day_end)
        while True:
            slot_start = cur
            slot_end   = slot_start + timedelta(minutes=args.exam_min)
            if slot_end > stop:
                break
            # slot ismi: 2025-11-03 09:00 gibi
            name = slot_start.strftime("%Y-%m-%d %H:%M")
            execute("INSERT INTO exam_slots(name,starts_at,ends_at) VALUES(?,?,?)",
                    (name, slot_start.strftime("%Y-%m-%d %H:%M"), slot_end.strftime("%Y-%m-%d %H:%M")))
            created += 1
            # boşluk ekle
            cur = slot_end + timedelta(minutes=args.gap_min)

    print(f"Üretilen slot sayısı: {created}")
