import os
from weasyprint import HTML, CSS
from jinja2 import Template
from parser import (
    split_sentences, extract_definition, extract_verdicts,
    extract_years, extract_key_terms, extract_conclusion,
    extract_items, get_title, highlight, escape
)

# Colors used in JS
CC = ['navy', 'maroon', 'green', 'purple', 'teal', 'mustard', 'indigo', 'rose']

CSS_CONTENT = """
@import url('https://fonts.googleapis.com/css2?family=Georgia&family=Inter:wght@400;500;600;700&display=swap');
body { background: #e8e2d8; font-family: 'Inter', sans-serif; padding: 20px; color: #222; }
.note-page { 
    background: #fefcf6; border-radius: 12px; padding: 24px; margin-bottom: 24px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #dcd4c6;
    page-break-inside: avoid;
}
.note-header { display: table; width: 100%; border-bottom: 2px solid #e0d8ca; padding-bottom: 16px; margin-bottom: 20px; }
.note-title-card { display: table-cell; width: 35%; border-right: 1px solid #e0d8ca; padding-right: 16px; position: relative; vertical-align: top; }
.crown-icon { font-size: 24px; position: absolute; top: -10px; right: 10px; opacity: 0.2; }
.q-label-card { font-size: 0.9rem; font-weight: 700; color: #8a6d3b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.q-title-card { font-size: 1.4rem; font-family: Georgia, serif; color: #1a3a6b; font-weight: 700; line-height: 1.3; }
.q-subject-card { font-size: 0.8rem; color: #777; margin-top: 12px; text-transform: uppercase; letter-spacing: 1px; }
.note-header-right { display: table-cell; width: 62%; padding-left: 16px; vertical-align: top; }
.note-question-box { background: #f4f0e6; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #1a3a6b; margin-bottom: 12px; }
.qb-label { font-size: 0.75rem; font-weight: 700; color: #1a3a6b; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 1px; }
.qb-text { font-size: 0.95rem; line-height: 1.5; color: #333; }
.note-index-box { font-size: 0.85rem; color: #555; background: #fff; padding: 10px 16px; border-radius: 6px; border: 1px dashed #ccc; }
.ib-label { font-weight: 700; margin-bottom: 4px; color: #444; }
.ib-list { margin: 0; padding-left: 20px; column-count: 2; column-gap: 20px; }
.ib-list li { margin-bottom: 2px; }
.ib-list a { color: #1a3a6b; text-decoration: none; }
.answer-box { margin-bottom: 20px; }
.ab-label { font-size: 0.85rem; font-weight: 700; color: #2e7d32; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px; }
.options-list { list-style: none; padding: 0; margin: 0; }
.options-list li { background: #fdfbf7; padding: 10px 14px; border-radius: 6px; border: 1px solid #e0d8ca; font-size: 0.95rem; margin-bottom: 8px; }
.options-list li.correct { background: #e8f5e9; border-color: #a5d6a7; font-weight: 600; color: #1b5e20; }
.opt-letter { display: inline-block; width: 24px; height: 24px; background: #e0d8ca; color: #555; border-radius: 50%; text-align: center; line-height: 24px; font-size: 0.8rem; font-weight: 700; margin-right: 12px; vertical-align: middle; }
.correct .opt-letter { background: #4caf50; color: #fff; }
.opt-tick { float: right; font-size: 1.1rem; }
.def-box { background: #e3f2fd; border-left: 4px solid #1976d2; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-bottom: 20px; }
.def-box-label { font-size: 0.75rem; font-weight: 700; color: #1565c0; text-transform: uppercase; display: block; margin-bottom: 6px; letter-spacing: 1px; }
.def-box p { margin: 0; font-size: 0.95rem; line-height: 1.5; color: #0d47a1; }
.section-box { margin-bottom: 20px; padding: 16px; border-radius: 8px; border: 1px solid transparent; }
.sb-heading { font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
.sh-icon { font-size: 1.1rem; margin-right: 8px; }
.navy { background: #f0f4f8; border-color: #d1e1ec; } .navy .sb-heading { color: #102a43; }
.maroon { background: #fcedec; border-color: #fad1d1; } .maroon .sb-heading { color: #621010; }
.green { background: #f1f8f1; border-color: #d8ead8; } .green .sb-heading { color: #194a19; }
.purple { background: #f6f0fa; border-color: #e5d4ef; } .purple .sb-heading { color: #441c60; }
.teal { background: #eefafa; border-color: #ccf0f0; } .teal .sb-heading { color: #0f4c4c; }
.mustard { background: #fffcf0; border-color: #fcebb6; } .mustard .sb-heading { color: #6b5204; }
.indigo { background: #f2f2fc; border-color: #d8d8f2; } .indigo .sb-heading { color: #29297a; }
.rose { background: #fff0f5; border-color: #f7d4e3; } .rose .sb-heading { color: #8a1c4a; }
.verdict-table, .comp-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; background: #fff; }
.verdict-table th, .comp-table th { text-align: left; padding: 10px; background: rgba(0,0,0,0.04); font-weight: 600; border-bottom: 2px solid rgba(0,0,0,0.1); color: #333; }
.verdict-table td, .comp-table td { padding: 10px; border-bottom: 1px solid rgba(0,0,0,0.06); vertical-align: top; }
.tag-correct { display: inline-block; padding: 2px 8px; background: #e8f5e9; color: #2e7d32; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.tag-incorrect { display: inline-block; padding: 2px 8px; background: #ffebee; color: #c62828; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.key-points-list { margin: 0; padding: 0; list-style: none; }
.key-points-list li { font-size: 0.95rem; line-height: 1.5; margin-bottom: 8px; }
.kp-bullet { color: #1a3a6b; font-size: 1.1rem; margin-right: 10px; }
.conclusion-box { background: #fff8e1; border: 1px solid #ffecb3; padding: 16px; border-radius: 8px; margin-bottom: 20px; }
.cb-icon { font-size: 2rem; color: #f57f17; float: left; margin-right: 16px; }
.cb-label { font-size: 0.8rem; font-weight: 700; color: #f57f17; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 1px; }
.conclusion-box p { margin: 0 0 8px 0; font-size: 0.95rem; line-height: 1.5; color: #3e2723; }
.conclusion-box p:last-child { margin: 0; }
.cb-content { overflow: hidden; }
.timeline { position: relative; padding-left: 20px; }
.timeline::before { content: ''; position: absolute; left: 5px; top: 0; bottom: 0; width: 2px; background: rgba(0,0,0,0.1); }
.tl-item { position: relative; margin-bottom: 10px; }
.tl-item::before { content: ''; position: absolute; left: -19px; top: 6px; width: 8px; height: 8px; border-radius: 50%; background: #1a3a6b; box-shadow: 0 0 0 3px rgba(26,58,107,0.2); }
.tl-year { font-weight: 700; color: #1a3a6b; font-size: 0.9rem; margin-bottom: 2px; }
.tl-text { font-size: 0.9rem; color: #444; line-height: 1.4; }
.terms-strip { display: block; }
.term-chip { display: inline-block; background: #fff; border: 1px solid rgba(0,0,0,0.1); padding: 4px 10px; border-radius: 16px; font-size: 0.85rem; font-weight: 500; color: #333; margin: 0 8px 8px 0; }
.revision-box { border: 2px dashed #ccc; padding: 16px; border-radius: 8px; background: #fafafa; margin-bottom: 20px; }
.rb-title { font-size: 0.9rem; font-weight: 700; color: #555; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 1px; }
.revision-list { margin: 0; padding: 0; list-style: none; }
.revision-list li { font-size: 0.9rem; line-height: 1.4; color: #444; margin-bottom: 8px; }
.chk { color: #999; font-size: 1.2rem; margin-right: 10px; }
.quote-box { text-align: center; font-family: Georgia, serif; font-size: 1.1rem; color: #666; font-style: italic; padding: 20px; position: relative; margin-top: 20px; border-top: 1px solid #eee; }
.quote-box cite { display: block; font-size: 0.8rem; color: #999; margin-top: 8px; font-style: normal; text-transform: uppercase; letter-spacing: 1px; }
.kw-article { background: #e3f2fd; padding: 0 4px; border-radius: 3px; font-weight: 600; color: #1565c0; border: 1px solid #bbdefb; }
.kw-year { background: #fff3e0; padding: 0 4px; border-radius: 3px; font-weight: 600; color: #e65100; border: 1px solid #ffe0b2; }
.kw-act { background: #f3e5f5; padding: 0 4px; border-radius: 3px; font-weight: 600; color: #6a1b9a; border: 1px solid #e1bee7; }
.kw-pct { background: #e8f5e9; padding: 0 4px; border-radius: 3px; font-weight: 600; color: #2e7d32; border: 1px solid #c8e6c9; }
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Study Notes</title>
<style>{{ css }}</style>
</head>
<body>
{% for q in questions %}
    {% set title = q.title %}
    {% set et = q.explanationText %}
    {% set qt = q.questionText %}
    {% set sents = q.sents %}
    {% set def = q.def %}
    {% set verdicts = q.verdicts %}
    {% set years = q.years %}
    {% set terms = q.terms %}
    {% set concls = q.concls %}
    {% set pts = q.pts %}
    {% set items = q.q_items %}
    {% set revPts = q.revPts %}
    {% set last = q.last %}
    {% set secs = q.secs %}
    {% set n = q.num %}

<div class="note-page" id="qpage-{{ n }}">
    {% if q.warnings %}
        <div class="parse-warning">&#9888; {{ escape(q.warnings|join(', ')) }}</div>
    {% endif %}

    <div class="note-header">
        <div class="note-title-card">
            <span class="crown-icon">&#128218;</span>
            <div class="q-label-card">Q {{ n }}</div>
            <div class="q-title-card">{{ escape(title[:60]) }}</div>
            <div class="q-subject-card">UPSC Study Notes</div>
        </div>
        <div class="note-header-right">
            {% if qt %}
                <div class="note-question-box">
                    <div class="qb-label">&#10022; Question</div>
                    <div class="qb-text">{{ highlight(escape(qt)) }}</div>
                </div>
            {% endif %}
            {% if secs|length > 0 %}
                <div class="note-index-box">
                    <div class="ib-label">&#128203; Index</div>
                    <ol class="ib-list">
                    {% for s in secs %}
                        <li>{{ loop.index }}. <a href="#{{ s.id }}-{{ n }}">{{ escape(s.label) }}</a></li>
                    {% endfor %}
                    </ol>
                </div>
            {% endif %}
        </div>
    </div>

    {% if q.options|length > 0 %}
        {% set ltrs = ['A','B','C','D','E','F'] %}
        <div id="sa-{{ n }}" class="answer-box">
            <div class="ab-label">&#9989; MCQ Options &amp; Correct Answer</div>
            <ul class="options-list">
            {% for o in q.options %}
                {% set cls = 'correct' if o.correct else 'wrong' %}
                <li class="{{ cls }}">
                    <span class="opt-letter">{{ ltrs[loop.index0] if loop.index0 < ltrs|length else loop.index }}</span>
                    {{ highlight(escape(o.text)) }}
                    {% if o.correct %}<span class="opt-tick">&#9989;</span>{% endif %}
                </li>
            {% endfor %}
            </ul>
        </div>
    {% endif %}

    {% if def %}
        <div id="sd-{{ n }}" class="def-box">
            <span class="def-box-label">&#128214; DEFINITION</span>
            <p>{{ highlight(escape(def)) }}</p>
        </div>
    {% endif %}

    {% if verdicts|length > 0 %}
        <div id="sv-{{ n }}" class="section-box {{ q.next_color() }}">
            <div class="sb-heading"><span class="sh-icon">&#9878;</span> Statement-wise Verdict</div>
            <table class="verdict-table">
                <thead><tr><th>Statement / Pair</th><th>Verdict</th><th>Details</th></tr></thead>
                <tbody>
                {% for v in verdicts %}
                    <tr>
                        <td><strong>{{ escape(v.label) }}</strong></td>
                        <td>
                            {% if v.verdict %}
                                <span class="tag-correct">&#9989; Correct</span>
                            {% else %}
                                <span class="tag-incorrect">&#10060; Incorrect</span>
                            {% endif %}
                        </td>
                        <td style="font-size:.78rem;color:#555">{{ highlight(escape(v.raw)) }}</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    {% endif %}

    {% if pts|length > 0 %}
        {% set icons = ['&#10022;','&#9733;','&#10148;','&#128313;','&#9670;','&#9656;','&#8226;'] %}
        <div id="sp-{{ n }}" class="section-box {{ q.next_color() }}">
            <div class="sb-heading"><span class="sh-icon">&#128204;</span> Key Points</div>
            <ul class="key-points-list">
            {% for p in pts[:12] %}
                <li>
                    <span class="kp-bullet">{{ icons[loop.index0 % icons|length] }}</span>
                    <span>{{ highlight(escape(p)) }}</span>
                </li>
            {% endfor %}
            </ul>
        </div>
    {% endif %}

    {% if items|length > 1 %}
        <div id="si-{{ n }}" class="section-box {{ q.next_color() }}">
            <div class="sb-heading"><span class="sh-icon">&#128202;</span> Item Analysis</div>
            <table class="comp-table">
                <thead><tr><th>#</th><th>Item</th><th>Note from Explanation</th></tr></thead>
                <tbody>
                {% for it in items %}
                    {% set rel = q.get_rel_for_item(it) %}
                    <tr>
                        <td><strong>{{ escape(it.num) }}</strong></td>
                        <td>{{ highlight(escape(it.text)) }}</td>
                        <td style="font-size:.78rem;color:#444">{{ highlight(escape(rel[:140])) }}</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    {% endif %}

    {% if concls|length > 0 %}
        <div id="sc-{{ n }}" class="conclusion-box">
            <div class="cb-icon">&#128161;</div>
            <div class="cb-content">
                <div class="cb-label">Conclusion / Answer Rationale</div>
                {% for c in concls %}
                    <p>{{ highlight(escape(c)) }}</p>
                {% endfor %}
            </div>
        </div>
    {% endif %}

    {% if years|length > 0 %}
        <div id="st-{{ n }}" class="section-box {{ q.next_color() }}">
            <div class="sb-heading"><span class="sh-icon">&#128197;</span> Timeline / Key Dates</div>
            <div class="timeline">
            {% for y in years %}
                <div class="tl-item">
                    <div class="tl-year">{{ escape(y.year) }}</div>
                    <div class="tl-text">{{ highlight(escape(y.text[:160])) }}</div>
                </div>
            {% endfor %}
            </div>
        </div>
    {% endif %}

    {% if terms|length > 0 %}
        <div id="sk-{{ n }}" class="section-box {{ q.next_color() }}">
            <div class="sb-heading"><span class="sh-icon">&#128273;</span> Key Terms</div>
            <div class="terms-strip">
            {% for t in terms %}
                <span class="term-chip">{{ escape(t) }}</span>
            {% endfor %}
            </div>
        </div>
    {% endif %}

    {% if revPts|length > 0 %}
        <div id="sr-{{ n }}" class="revision-box">
            <div class="rb-title">&#9744; Quick Revision Checklist</div>
            <ul class="revision-list">
            {% for p in revPts %}
                <li>
                    <span class="chk">&#9744;</span>
                    <span>{{ highlight(escape(p[:200])) }}</span>
                </li>
            {% endfor %}
            </ul>
        </div>
    {% endif %}

    {% if last and last|length > 20 and last|length < 200 and sents|length > 3 %}
        <div class="quote-box">&ldquo;{{ escape(last) }}&rdquo;<cite>&mdash; Explanation, Q{{ n }}</cite></div>
    {% endif %}
</div>
{% endfor %}
</body>
</html>
"""

def prepare_question_data(q):
    title = get_title(q)
    et = q.get('explanationText', '')
    qt = q.get('questionText', '')
    
    sents = split_sentences(et)
    def_box = extract_definition(et)
    verdicts = extract_verdicts(et)
    years = extract_years(et)
    terms = extract_key_terms(et)
    concls = extract_conclusion(sents)
    
    pts = [s for s in sents if s not in concls]
    items = extract_items(qt)
    
    secs = []
    if len(q.get('options', [])) > 0: secs.append({'id':'sa', 'label':'Correct Answer'})
    if def_box: secs.append({'id':'sd', 'label':'Definition'})
    if len(verdicts) > 0: secs.append({'id':'sv', 'label':'Statement Verdicts'})
    if len(pts) > 0: secs.append({'id':'sp', 'label':'Key Points'})
    if len(items) > 1: secs.append({'id':'si', 'label':'Item Analysis'})
    if len(concls) > 0: secs.append({'id':'sc', 'label':'Conclusion'})
    if len(years) > 0: secs.append({'id':'st', 'label':'Timeline'})
    if len(terms) > 0: secs.append({'id':'sk', 'label':'Key Terms'})
    secs.append({'id':'sr', 'label':'Quick Revision'})
    
    revPts = sents[:5]
    last = sents[-1] if sents else ''
    
    color_index = 0
    def next_color():
        nonlocal color_index
        c = CC[color_index % len(CC)]
        color_index += 1
        return c

    def get_rel_for_item(it):
        rel = ''
        wds = it['text'].split()[:4]
        for s in sents:
            found = False
            for w in wds:
                if len(w) > 3 and w.lower() in s.lower():
                    found = True
                    break
            if found:
                rel = s
                break
        return rel

    q_data = dict(q)
    q_data.update({
        'title': title,
        'sents': sents,
        'def': def_box,
        'verdicts': verdicts,
        'years': years,
        'terms': terms,
        'concls': concls,
        'pts': pts,
        'q_items': items,
        'secs': secs,
        'revPts': revPts,
        'last': last,
        'next_color': next_color,
        'get_rel_for_item': get_rel_for_item
    })
    return q_data

def generate_html(questions):
    prepared_qs = [prepare_question_data(q) for q in questions]
    template = Template(HTML_TEMPLATE)
    
    html_out = template.render(
        questions=prepared_qs,
        css=CSS_CONTENT,
        escape=escape,
        highlight=highlight
    )
    return html_out

def build_pdf(html_str, output_path):
    HTML(string=html_str).write_pdf(output_path)
