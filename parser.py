import re

def parse_file(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    q_starts = []
    
    for i, line in enumerate(lines):
        if re.match(r'^Q\d+\.', line.strip()):
            q_starts.append(i)
            
    if not q_starts:
        return []
        
    q_starts.append(len(lines))
    result = []
    
    for qi in range(len(q_starts) - 1):
        p = parse_one_question(lines[q_starts[qi]:q_starts[qi+1]])
        if p:
            result.append(p)
            
    return result

def parse_one_question(bl):
    fl = bl[0]
    qm = re.match(r'^Q(\d+)\.(.*)', fl)
    if not qm:
        return None
        
    q_num = int(qm.group(1))
    warnings = []
    q_lines = []
    o_lines = []
    e_lines = []
    phase = 'question'
    
    # Emoji regex simplified for python: any character from common emoji ranges
    emoji_rx = re.compile(r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\u2600-\u27BF\U0001FA00-\U0001FFFF]')
    ex_rx = re.compile(r'^Ex:', re.IGNORECASE)
    tick_rx = re.compile(r'\u2705')
    
    for i in range(len(bl)):
        line = bl[i].strip()
        if phase == 'question':
            cl = re.sub(r'^Q\d+\.', '', bl[i]).strip() if i == 0 else line
            if len(line) == 0 and i > 0:
                q_lines.append('')
                continue
            if emoji_rx.match(line) and len(line) <= 6:
                phase = 'options'
                continue
            if ex_rx.match(line):
                phase = 'explanation'
                t = re.sub(r'^Ex:', '', line, flags=re.IGNORECASE).strip()
                if t:
                    e_lines.append(t)
                continue
            if tick_rx.search(line) and i > 2:
                phase = 'options'
                o_lines.append(cl)
                continue
            q_lines.append(cl if i == 0 else line)
        elif phase == 'options':
            if ex_rx.match(line):
                phase = 'explanation'
                t2 = re.sub(r'^Ex:', '', line, flags=re.IGNORECASE).strip()
                if t2:
                    e_lines.append(t2)
                continue
            if len(line) > 0:
                o_lines.append(line)
        else:
            e_lines.append(line)
            
    exp_text = '\n'.join(e_lines).strip()
    q_text = '\n'.join([l.strip() for l in q_lines if l.strip()]).strip()
    
    if not q_text:
        warnings.append('Question text missing')
    if not exp_text:
        warnings.append('Explanation (Ex:) missing')
        
    opts = []
    ca = None
    for o in o_lines:
        ic = '\u2705' in o
        co = o.replace('\u2705', '').strip()
        if co:
            opts.append({'text': co, 'correct': ic})
            if ic:
                ca = co
                
    if len(opts) > 0 and not ca:
        warnings.append('No correct answer detected')
    if len(opts) == 0:
        warnings.append('Options not found')
        
    return {
        'num': q_num,
        'questionText': q_text,
        'options': opts,
        'correctAnswer': ca,
        'explanationText': exp_text,
        'warnings': warnings
    }

def split_sentences(text):
    s = text
    abbrs = ['e.g', 'i.e', 'etc', 'vs', 'Dr', 'Mr', 'Mrs', 'Prof', 'No', 'Art', 'Sec']
    phs = {}
    
    for idx, a in enumerate(abbrs):
        rx = re.compile(r'\b' + a.replace('.', r'\.') + r'\.(?=\s)')
        ph = f'__A{idx}__'
        phs[ph] = a + '.'
        s = rx.sub(ph, s)
        
    s = re.sub(r'(\d)\.(\d)', r'\1__D__\2', s)
    
    # split by punctuation followed by space and capital letter or quote
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"])', s)
    
    res = []
    for p in parts:
        r = p
        for ph, val in phs.items():
            r = r.replace(ph, val)
        r = r.replace('__D__', '.').strip()
        if len(r) > 10:
            res.append(r)
    return res

def extract_definition(text):
    pats = [
        re.compile(r'^([^.]{5,120})\s+(?:is|are|was|were|refers to|means|defined as|known as|called)\s+(.{10,250}[.!?])', re.IGNORECASE),
        re.compile(r'([^.]{5,80})\s+(?:is defined as|is referred to as|is known as)\s+([^.]{10,250}\.)', re.IGNORECASE)
    ]
    for pat in pats:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None

def extract_verdicts(text):
    results = []
    seen = {}
    pats = [
        {'rx': re.compile(r'[Ss]tatement[\s-]*([I1-9]+)\s+is\s+(correct|not correct|incorrect|true|false)', re.IGNORECASE), 't': 'Statement'},
        {'rx': re.compile(r'[Pp]air\s+(\d+)\s+is\s+(correctly matched|not correctly matched|incorrectly matched)', re.IGNORECASE), 't': 'Pair'},
        {'rx': re.compile(r'[Hh]ence[,]?\s+[Ss]tatement[\s-]*([I1-9]+)\s+is\s+(correct|not correct|incorrect)', re.IGNORECASE), 't': 'Statement'},
        {'rx': re.compile(r'[Hh]ence[,]?\s+[Pp]air\s+(\d+)\s+is\s+(correctly matched|not correctly matched|incorrectly matched)', re.IGNORECASE), 't': 'Pair'}
    ]
    
    for pat in pats:
        for m in pat['rx'].finditer(text):
            k = f"{pat['t']}-{m.group(1)}"
            if k not in seen:
                seen[k] = 1
                vt = m.group(2).lower()
                ok = ('not' not in vt and 'in' not in vt and ('correct' in vt or 'true' in vt))
                results.append({
                    'label': f"{pat['t']} {m.group(1)}",
                    'verdict': ok,
                    'raw': m.group(0)
                })
    return results

def extract_years(text):
    evts = []
    seen = {}
    rx = re.compile(r'\b(1[6-9]\d{2}|20[0-2]\d)\b[^.!\n]{0,160}')
    for m in rx.finditer(text):
        yr = m.group(1)
        if yr not in seen:
            seen[yr] = 1
            tt = m.group(0).replace(yr, '').lstrip(' ,-').strip()
            if len(tt) > 3:
                evts.append({'year': yr, 'text': tt[:150]})
    return evts[:8]

def extract_key_terms(text):
    freq = {}
    rx = re.compile(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,2})\b')
    stops = {"Consider":1,"Which":1,"Statement":1,"Both":1,"Following":1,"India":1,"Select":1,"Correct":1,"Regarding":1,"Reference":1,"Statements":1,"Given":1,"Above":1,"Answer":1,"How":1,"Many":1,"Other":1,"Most":1,"Recent":1,"Using":1,"Code":1,"With":1,"What":1,"Where":1,"When":1,"The":1,"This":1,"That":1,"These":1}
    for m in rx.finditer(text):
        t = m.group(1).strip()
        if t not in stops and len(t) > 3:
            freq[t] = freq.get(t, 0) + 1
    
    return sorted(freq.keys(), key=lambda k: freq[k], reverse=True)[:7]

def extract_conclusion(sents):
    return [s for s in sents if re.match(r'^(Hence|Therefore|Thus|So,|As a result|Consequently|In conclusion)', s.strip(), re.IGNORECASE)]

def extract_items(qText):
    items = []
    rx = re.compile(r'^\s*(\d+)[.)]\s*(.+)$', re.MULTILINE)
    for m in rx.finditer(qText):
        items.append({'num': m.group(1), 'text': m.group(2).strip()})
    return items

def to_tc(s):
    return ' '.join([t.capitalize() for t in s.split()])

def get_title(q):
    qt = q.get('questionText', '')
    acStop = {"THE":1,"AND":1,"FOR":1,"ARE":1,"WITH":1,"THAT":1,"FROM":1,"THIS":1,"WHICH":1,"BOTH":1,"ABOVE":1,"GIVEN":1,"FOLLOWING":1,"CONSIDER":1,"REGARDING":1,"REFERENCE":1,"STATEMENTS":1,"CORRECT":1,"STATEMENT":1,"RESPECT":1,"SELECT":1,"ANSWER":1,"CODE":1,"INDIA":1,"NOT":1,"HOW":1,"MANY":1,"ONLY":1}
    rx = re.compile(r'\b([A-Z]{3,8}(?:\s+[A-Z]{2,8}){0,2})\b')
    for m in rx.finditer(qt):
        a = m.group(1).strip()
        if a not in acStop:
            return to_tc(a)
            
    qm = re.search(r'"([^"]{3,40})"', qt)
    if qm:
        return qm.group(1).strip()
        
    propStop = {"Consider":1,"Which":1,"Statement":1,"Both":1,"Following":1,"India":1,"Select":1,"Correct":1,"Regarding":1,"Reference":1,"Statements":1,"Given":1,"Above":1,"Answer":1,"How":1,"Many":1,"Other":1,"Most":1,"Recent":1,"Using":1,"Code":1,"With":1,"What":1,"Where":1,"When":1,"The":1,"This":1,"That":1,"These":1}
    prx = re.compile(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,3})\b')
    props = []
    for m in prx.finditer(qt):
        p = m.group(1).strip()
        if p not in propStop:
            props.append(p)
            
    if props:
        props.sort(key=lambda a: len(a.split()), reverse=True)
        return props[0]
        
    cleaned = re.sub(r'[^\w\s]', ' ', qt).split()
    return ' '.join(cleaned[:6]) or f"Q{q.get('num')}"

def highlight(h):
    h = re.sub(r'\b(Article[s]?\s+\d+(?:[A-Za-z])?(?:\s*(?:and|to|,)\s*\d+[A-Za-z]?)*)\b', r'<span class="kw-article">\1</span>', h)
    h = re.sub(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', r'<span class="kw-year">\1</span>', h)
    h = re.sub(r'\b(\d{4}\s+(?:Act|Amendment|Constitution|Bill))\b', r'<span class="kw-act">\1</span>', h)
    h = re.sub(r'\b((?:Act|Amendment|Bill)\s+of\s+\d{4})\b', r'<span class="kw-act">\1</span>', h)
    h = re.sub(r'(\d+(?:\.\d+)?%)', r'<span class="kw-pct">\1</span>', h)
    return h
    
def escape(s):
    if not s: return ''
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
