import re
from datetime import datetime
from django.utils import timezone
from dateparser.search import search_dates
import calendar
from .templatetags.ceske_data import chytre_datum


# Tvoje parádní vylepšená mapa
SMART_REPLACEMENTS = {
    # Časy
    r'\bráno\b': 'v 8:00',
    r'\bdopoledne\b': 'v 10:00',
    r'\bv poledne\b': 'v 12:00',
    r'\bodpoledne\b': 'v 15:00',
    r'\bvečer\b': 'v 20:00',
    r'\bv noci\b': 'v 23:00',
    r'\bpřed půlnocí\b': 'v 23:59', # Zde je vyšší priorita správně!
    r'\bpůlnoc\w*\b': 'v 0:00',
    r'\bpo škole\b': 'v 14:30',
    r'\bpo práci\b': 'v 17:00',
    r'\bpo obědě\b': 'v 13:00',
    r'\bpo večeři\b': 'v 19:00',
    
    
    # Svátky a události
    r'\bvánoc\w*': '24. 12.',
    r'\bsilvestr\w*': '31. 12.',
    r'\bprázdnin\w*': '1. 7.',
    r'\bvalentýn\w*': '14. 2.',
    r'\bmikuláš\w*': '5. 12.',
    r'\bzimn\w* slunovrat\w*': '21. 12.',
    r'\bl[eé]tn\w* slunovrat\w*': '21. 6.', # Ošetřeno "letní" i "létní"
    r'\bnov\w* rok\w*': '1. 1.',
    r'\bjarn\w* rovnodennost\w*': '20. 3.',
    r'\bpodzim\w* rovnodennost\w*': '22. 9.',
}

# NOVÉ: Přesné rozsahy. Definujeme Start a End hodiny/minuty.
EXACT_RANGES = {
    r'\bve škole\b': {'start': (7, 45), 'end': (14, 0)},
    r'\bcelý den\b': {'start': (0, 0), 'end': (23, 59)},
    r'\bcelé dopoledne\b': {'start': (8, 0), 'end': (12, 0)},
    r'\bcelé odpoledne\b': {'start': (12, 0), 'end': (18, 0)},
    r'\bpracovní dob\w*': {'start': (8, 0), 'end': (16, 30)},
}

PAST_INDICATORS = [
    r'\w+l jsem', r'\w+la jsem', r'\w+li jsme',
    r'\bbyl', r'\bproběhlo', r'\bměl', r'\bstalo', 
    r'\bminul\w+', r'\bnaposledy', r'\bpřed\b'
]

FUTURE_INDICATORS = [
    r'\bbudu', r'\bpůjdu', r'\bnaplánuj', r'\budělám', 
    r'\bpříšt\w+', r'\bdalš\w+', r'\bza\b', r'\bzítra', r'\bdo\b', r'\bdeadline', r'\buntil\b',
]

MONTHS_MAP = {
    'leden': 1, 'ledna': 1,
    'únor': 2, 'února': 2,
    'březen': 3, 'března': 3,
    'duben': 4, 'dubna': 4,
    'květen': 5, 'května': 5,
    'červen': 6, 'června': 6,
    'červenec': 7, 'července': 7,
    'srpen': 8, 'srpna': 8,
    'září': 9,
    'říjen': 10, 'října': 10,
    'listopad': 11, 'listopadu': 11,
    'prosinec': 12, 'prosince': 12
}


def detect_tense_intent(text):
    text_lower = text.lower()
    if any(re.search(pattern, text_lower) for pattern in PAST_INDICATORS):
        return 'past'
    if any(re.search(pattern, text_lower) for pattern in FUTURE_INDICATORS):
        return 'future'
    return None

def _evaluate_time_chunk(query_text):
    now = timezone.localtime(timezone.now())
    intent = detect_tense_intent(query_text)
    
    # 1. Kontrola a odebrání Pevných Rozsahů ("ve škole", "celý den")
    forced_range = None
    matched_exact_phrase = None
    text_to_parse = query_text
    
    for pattern, times in EXACT_RANGES.items():
        match = re.search(pattern, text_to_parse)
        if match:
            forced_range = times
            matched_exact_phrase = match.group(0) # Uložíme pro frontend ("ve škole")
            # Odstraníme z textu, aby parser hledal jen den (např. "zítra")
            text_to_parse = re.sub(pattern, '', text_to_parse).strip()
            break
            
    # Pokud uživatel napsal JEN "celý den", text_to_parse je teď prázdný. Dosadíme "dnes".
    if not text_to_parse and forced_range:
        text_to_parse = "dnes"

    languages = ['cs', 'en']
    base_settings = {
        'DATE_ORDER': 'DMY',
        'RETURN_AS_TIMEZONE_AWARE': True,
        'TIMEZONE': 'Europe/Prague',
        'PREFER_DAY_OF_MONTH': 'first',
    }

    def get_dates(preference):
        settings = base_settings.copy()
        settings['PREFER_DATES_FROM'] = preference
        found = search_dates(text_to_parse, languages=languages, settings=settings)
        if not found: return None
        
        clean_dates = []
        for text_chunk, dt in found:
            # Filtr proti matematice "1 + 1"
            if re.fullmatch(r'[\d\s\+\-\*\/\?]+', text_chunk):
                continue
            if ':' not in text_chunk:
                dt = dt.replace(minute=0, second=0, microsecond=0)
            clean_dates.append({'text': text_chunk, 'dt': dt})
        return clean_dates if clean_dates else None

    past_cands = get_dates('past')
    future_cands = get_dates('future')
    
    if not past_cands and not future_cands:
        return None, None, intent

    final_start, final_end = None, None

    # Zbytek rozhodovací logiky (Blízkost vs Intent)...
    if past_cands and future_cands:
        if intent == 'past':
            final_start = past_cands[0]
            if len(past_cands) > 1: final_end = past_cands[-1]
        elif intent == 'future':
            final_start = future_cands[0]
            if len(future_cands) > 1: final_end = future_cands[-1]
        else:
            p_cand, f_cand = past_cands[0], future_cands[0]
            diff_past = abs((now - p_cand['dt']).total_seconds())
            diff_future = abs((f_cand['dt'] - now).total_seconds())

            if diff_past <= diff_future:
                final_start = p_cand
                if len(past_cands) > 1: final_end = past_cands[-1]
            else:
                final_start = f_cand
                if len(future_cands) > 1: final_end = future_cands[-1]
    elif past_cands or future_cands:
        cands = past_cands or future_cands
        final_start = cands[0]
        if len(cands) > 1: final_end = cands[-1]

    # 2. APLIKACE PEVNÉHO ROZSAHU (pokud byl nalezen)
    if forced_range and final_start:
        s_h, s_m = forced_range['start']
        e_h, e_m = forced_range['end']
        
        start_dt = final_start['dt'].replace(hour=s_h, minute=s_m, second=0, microsecond=0)
        end_dt = final_start['dt'].replace(hour=e_h, minute=e_m, second=0, microsecond=0)
        
        final_start['dt'] = start_dt
        final_start['text'] = matched_exact_phrase # Frontend uvidí "ve škole"
        
        final_end = {
            'text': matched_exact_phrase,
            'dt': end_dt
        }

    return final_start, final_end, intent

def extract_smart_dates(query_text):
    processed_query = query_text.lower()
    
    for pattern, replacement in SMART_REPLACEMENTS.items():
        processed_query = re.sub(pattern, replacement, processed_query)

    matched_full_string = None
    final_start = None
    final_end = None
    choice_reason = None

    # --- 1. NOVÁ LOGIKA: DETEKCE CELÝCH MĚSÍCŮ A ROKŮ ---
    # Tento Regex chytí: "celý rok 2025", "celý únor", "celý příští březen", atd.
    month_names = "|".join(MONTHS_MAP.keys())
    whole_period_pattern = fr'\bcel[ýé](?:\s+(tento|příšt\w+|minul\w+|dalš\w+))?\s+(rok|{month_names})(?:\s+(\d{{4}}))?\b'
    whole_period_match = re.search(whole_period_pattern, processed_query)

    if whole_period_match:
        matched_full_string = whole_period_match.group(0).strip()
        modifier = whole_period_match.group(1) # např. "příští", "minulý"
        period_str = whole_period_match.group(2) # "rok" nebo "únor"
        year_str = whole_period_match.group(3)   # "2025"

        now = timezone.localtime(timezone.now())
        
        # Logika pro určení správného roku
        if year_str:
            year = int(year_str)
        else:
            year = now.year
            # Modifikátory (příští, minulý) mají přednost
            if modifier:
                if re.search(r'příšt|dalš', modifier): year += 1
                elif re.search(r'minul', modifier): year -= 1
            else:
                # Pokud není modifikátor, zkusíme hádat podle gramatiky věty
                intent = detect_tense_intent(processed_query)
                if period_str == 'rok':
                    if intent == 'future': year += 1
                    elif intent == 'past': year -= 1
                else:
                    month_num = MONTHS_MAP[period_str]
                    if intent == 'future' and month_num < now.month: year += 1
                    elif intent == 'past' and month_num > now.month: year -= 1

        # Vytvoření start/end objektů (Používáme datetime bez .replace(), 
        # abychom zabránili chybě, kdyby byl zrovna dneska 29. únor)
        if period_str == 'rok':
            s_dt = timezone.make_aware(datetime(year, 1, 1, 0, 0, 0))
            e_dt = timezone.make_aware(datetime(year, 12, 31, 23, 59, 0))
        else:
            month_num = MONTHS_MAP[period_str]
            last_day = calendar.monthrange(year, month_num)[1] # Zjistí, kolik má měsíc dní!
            s_dt = timezone.make_aware(datetime(year, month_num, 1, 0, 0, 0))
            e_dt = timezone.make_aware(datetime(year, month_num, last_day, 23, 59, 0))

        final_start = {'text': matched_full_string, 'dt': s_dt}
        final_end = {'text': matched_full_string, 'dt': e_dt}
        choice_reason = f"whole_period ({period_str})"

    else:
        # --- 2. TVOJE EXISTUJÍCÍ LOGIKA PRO "OD-DO" ---
        range_match = re.search(r'(.*?)\b(?:od|from)\b(.*?)\b(?:do|to|until)\b(.*)', processed_query)
        
        if range_match:
            matched_full_string = range_match.group(0).strip()
            
            prefix = range_match.group(1).strip()
            start_part = range_match.group(2).strip()
            end_part = range_match.group(3).strip()
            
            start_text = f"{prefix} {start_part}".strip()
            end_text = f"{prefix} {end_part}".strip()
            
            s_start, _, s_intent = _evaluate_time_chunk(start_text)
            e_start, _, e_intent = _evaluate_time_chunk(end_text)
            
            final_start = s_start
            final_end = e_start
            choice_reason = f"range (start:{s_intent}, end:{e_intent})"
            
        else:
            # --- 3. STANDARDNÍ JEDNOZNAČNÉ ZHODNOCENÍ ---
            final_start, final_end, intent = _evaluate_time_chunk(processed_query)
            choice_reason = intent if intent else "proximity"
            
            is_deadline_intent = any(re.search(r'\b' + prep + r'\b', processed_query) for prep in ['do', 'k', 'deadline', 'until'])
            if final_start and not final_end and is_deadline_intent:
                final_end = final_start
                final_start = None

    # Příprava výstupu
    start_dt = final_start['dt'] if final_start else None
    end_dt = final_end['dt'] if final_end else None

    return {
        'success': bool(start_dt or end_dt),
        'choice_reason': choice_reason,
        'start': start_dt.isoformat() if start_dt else None,
        'end': end_dt.isoformat() if end_dt else None,
        'display_start': chytre_datum(start_dt) if start_dt else None,
        'display_end': chytre_datum(end_dt) if end_dt else None,
        'matched_string_start': final_start['text'] if final_start else None,
        'matched_string_end': final_end['text'] if final_end else None,
        'matched_string_full': matched_full_string,
        'processed_query': processed_query 
    }