import re
from datetime import datetime
from django.utils import timezone
from dateparser.search import search_dates

FUZZY_TIME_MAP = {
    'ráno': 'v 8:00', 'dopoledne': 'v 10:00', 'v poledne': 'v 12:00',
    'odpoledne': 'v 15:00', 'večer': 'v 20:00', 'v noci': 'v 23:00',
}

PAST_INDICATORS = [
    r'\w+l jsem', r'\w+la jsem', r'\w+li jsme',
    r'\bbyl', r'\bproběhlo', r'\bměl', r'\bstalo', 
    r'\bminul\w+', r'\bnaposledy', r'\bpřed\b'
]

FUTURE_INDICATORS = [
    r'\bbudu', r'\bpůjdu', r'\bnaplánuj', r'\budělám', 
    r'\bpříšt\w+', r'\bdalš\w+', r'\bza\b', r'\bzítra', r'\bdo\b', r'\bdeadline'
]

def detect_tense_intent(text):
    text_lower = text.lower()
    if any(re.search(pattern, text_lower) for pattern in PAST_INDICATORS):
        return 'past'
    if any(re.search(pattern, text_lower) for pattern in FUTURE_INDICATORS):
        return 'future'
    return None

def _evaluate_time_chunk(query_text):
    """Pomocná funkce: Vrací slovníky {'text': str, 'dt': datetime}."""
    now = timezone.localtime(timezone.now())
    intent = detect_tense_intent(query_text)
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
        found = search_dates(query_text, languages=languages, settings=settings)
        if not found: return None
        
        clean_dates = []
        for text_chunk, dt in found:
            if ':' not in text_chunk:
                dt = dt.replace(minute=0, second=0, microsecond=0)
            # Uložíme i text_chunk pro potřeby frontendu!
            clean_dates.append({'text': text_chunk, 'dt': dt})
        return clean_dates

    past_cands = get_dates('past')
    future_cands = get_dates('future')
    
    if not past_cands and not future_cands:
        return None, None, intent

    final_start, final_end = None, None

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

    return final_start, final_end, intent

def extract_smart_dates(query_text):
    processed_query = query_text.lower()
    for word, time_replacement in FUZZY_TIME_MAP.items():
        processed_query = processed_query.replace(word, time_replacement)

    # 1. RANGE DETEKCE
    range_match = re.search(r'\b(?:od|from)\b(.*?)\b(?:do|to|until)\b(.*)', processed_query)
    
    matched_full_string = None

    if range_match:
        matched_full_string = range_match.group(0).strip() # "od minulého prosince do dalšího prosince"
        start_text = range_match.group(1).strip()
        end_text = range_match.group(2).strip()
        
        s_start, _, s_intent = _evaluate_time_chunk(start_text)
        e_start, _, e_intent = _evaluate_time_chunk(end_text)
        
        final_start = s_start
        final_end = e_start
        choice_reason = f"range (start:{s_intent}, end:{e_intent})"
        
    else:
        final_start, final_end, intent = _evaluate_time_chunk(processed_query)
        choice_reason = intent if intent else "proximity"
        
        # Deadline logika (pokud jde o termín do budoucna a máme jen jedno datum)
        is_deadline_intent = any(re.search(r'\b' + prep + r'\b', processed_query) for prep in ['do', 'k', 'deadline', 'until'])
        if final_start and not final_end and is_deadline_intent:
            final_end = final_start
            final_start = None

    # Ošetření, aby to nepadalo, pokud se nic nenajde
    start_dt = final_start['dt'] if final_start else None
    end_dt = final_end['dt'] if final_end else None

    return {
        'success': bool(start_dt or end_dt),
        'choice_reason': choice_reason,
        
        # Strojová data
        'start': start_dt.isoformat() if start_dt else None,
        'end': end_dt.isoformat() if end_dt else None,
        
        # Lidská data
        'display_start': start_dt.strftime('%d. %m. %Y %H:%M') if start_dt else None,
        'display_end': end_dt.strftime('%d. %m. %Y %H:%M') if end_dt else None,

        # Texty pro frontendové zvýraznění
        'matched_string_start': final_start['text'] if final_start else None,
        'matched_string_end': final_end['text'] if final_end else None,
        'matched_string_full': matched_full_string,
        
        # Původní čistý text pro debug nebo fuzzy-hledání
        'processed_query': processed_query 
    }