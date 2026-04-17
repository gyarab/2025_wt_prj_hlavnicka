from django import template
from django.utils import timezone
from datetime import datetime, timedelta

register = template.Library()

def get_time_nick(value):
    """Vrací lidové označení času nebo formátovaný čas s předložkou."""
    h, m = value.hour, value.minute
    
    if h == 0 and m == 0:
        return "o půlnoci"
    if h == 12 and m == 0:
        return "v poledne"
    if h == 17 and m == 0:
        return "o páté"
    if h == 23 and m == 59:
        return "před půlnocí"
    
    # Standardní čas s předložkou v/ve
    prep = "ve" if h in [2, 3, 4, 12] else "v"
    return f"{prep} {h}:{m:02d}"

def get_weekday_acc(weekday_idx):
    """Vrací název dne ve 4. pádě (pro předložku 'v')."""
    days = ["pondělí", "úterý", "středu", "čtvrtek", "pátek", "sobotu", "neděli"]
    return days[weekday_idx]

@register.filter
def chytre_datum(value):
    if not isinstance(value, datetime):
        return value

    if timezone.is_aware(value):
        value = timezone.localtime(value)
    
    now = timezone.localtime(timezone.now())
    diff = now - value
    abs_diff = abs(diff)
    
    date_now = now.date()
    date_val = value.date()
    day_diff = (date_val - date_now).days
    time_nick = get_time_nick(value)

    # 1. VELMI BLÍZKÁ MINULOST / BUDOUCNOST (TEĎ)
    if abs_diff < timedelta(minutes=1):
        return "teď"

    # 2. RELATIVNÍ MINUTY A HODINY (v rámci dneška)
    if day_diff == 0:
        if abs_diff < timedelta(hours=1):
            mins = int(abs_diff.total_seconds() // 60)
            if diff.total_seconds() > 0: # Minulost
                return f"před minutou" if mins == 1 else f"před {mins} minutami"
            else: # Budoucnost
                return f"za minutu" if mins == 1 else f"za {mins} minut"
        
        if abs_diff < timedelta(hours=6):
            hrs = int(abs_diff.total_seconds() // 3600)
            if diff.total_seconds() > 0:
                return f"před hodinou" if hrs == 1 else f"před {hrs} hodinami"
            else:
                return f"za hodinu" if hrs == 1 else f"za {hrs} hodin"

    # 3. SPECIÁLNÍ DNY (-2 až +2)
    special_days = {
        -2: "předevčírem",
        -1: "včera",
        0: "dnes",
        1: "zítra",
        2: "pozítří",
    }
    if day_diff in special_days:
        return f"{special_days[day_diff]} {time_nick}"

    # 4. TÝDENNÍ RELATIVITA (v úterý / v poslední středu)
    # Pokud je to v rozmezí cca týdne, ale ne v rozmezí spec. dnů výše
    if -7 <= day_diff <= 7:
        day_name = get_weekday_acc(value.weekday())
        if day_diff > 0:
            return f"v {day_name} {time_nick}"
        else:
            return f"v poslední {day_name} {time_nick}"

    # 5. VÝROČÍ (Dnes před rokem / Za rok)
    # Pokud je stejný den a měsíc
    if date_now.day == date_val.day and date_now.month == date_val.month:
        year_diff = abs(date_now.year - date_val.year)
        if diff.total_seconds() > 0: # Minulost
            suffix = "rokem" if year_diff == 1 else (f"{year_diff} lety")
            return f"před {suffix} {time_nick}"
        else: # Budoucnost
            suffix = "rok" if year_diff == 1 else (f"{year_diff} roky" if year_diff < 5 else f"{year_diff} let")
            return f"za {suffix} {time_nick}"

    # 6. ABSOLUTNÍ FORMÁT (zbytek)
    time_clean = time_nick.replace("ve ", "").replace("v ", "").replace("o ", "")
    if value.year == now.year:
        return value.strftime(f"%d. %m., {time_clean}")
    else:
        return value.strftime(f"%d. %m. %Y, {time_clean}")