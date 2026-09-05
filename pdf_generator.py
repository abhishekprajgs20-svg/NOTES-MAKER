import os
import tempfile
from weasyprint import HTML, CSS
from jinja2 import Template
from pypdf import PdfWriter
from parser import (
    split_sentences, extract_definition, extract_verdicts,
    extract_years, extract_key_terms, extract_conclusion,
    extract_items, get_title, highlight, escape
)

CC = ['navy', 'maroon', 'green', 'purple', 'teal', 'mustard', 'indigo', 'rose']

CSS_CONTENT = """
:root{
  --font-title: Georgia, "Bookman Old Style", "Times New Roman", serif;
  --font-body: "Segoe UI", Calibri, Arial, sans-serif;
  --cream: #faf6ee; --cream2: #f3ead8; --paper: #fefcf6;
  --navy: #1a3a6b; --maroon: #8b1a1a; --green: #1a6b3a; --purple: #5a1a8b;
  --teal: #1a6b6b; --mustard: #8b6a00; --indigo: #2d2d8b; --rose: #8b2d5a;
  --navy-bg: #e8eef7; --maroon-bg: #f7e8e8; --green-bg: #e8f7ee; --purple-bg: #f0e8f7;
  --teal-bg: #e8f7f7; --mustard-bg: #f7f3e8; --indigo-bg: #eeeef7; --rose-bg: #f7e8ef;
  --radius: 10px;
  --shadow-sm: 0 1px 4px rgba(0,0,0,0.08);
}
body { background: #e8e2d8; font-family: var(--font-body); color: #222; }
.note-page { background: #fefcf6; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #dcd4c6; page-break-inside: avoid; }
.note-header { display: flex; justify-content: space-between; border-bottom: 2px solid #e0d8ca; padding-bottom: 16px; margin-bottom: 20px; align-items: start; }
.note-title-card { width: 35%; border-right: 1px solid #e0d8ca; padding-right: 16px; position: relative; }
.crown-icon { font-size: 24px; position: absolute; top: -10px; right: 10px; opacity: 0.2; }
.q-label-card { font-size: 0.9rem; font-weight: 700; color: #8a6d3b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.q-title-card { font-size: 1.4rem; font-family: var(--font-title); color: #1a3a6b; font-weight: 700; line-height: 1.3; }
.q-subject-card { font-size: 0.8rem; color: #777; margin-top: 12px; text-transform: uppercase; letter-spacing: 1px; }
.note-header-right { width: 62%; display: flex; flex-direction: column; gap: 12px; }
.note-question-box { background: var(--navy-bg); border: 1.5px solid var(--navy); border-radius: var(--radius); padding: 12px 16px; margin-bottom: 12px; }
.qb-label { font-size: 0.75rem; font-weight: 700; color: var(--navy); text-transform: uppercase; margin-bottom: 6px; letter-spacing: 1px; }
.qb-text { font-size: 0.95rem; line-height: 1.5; color: #333; }
.note-index-box { font-size: 0.85rem; color: #555; background: var(--mustard-bg); padding: 10px 16px; border-radius: 6px; border: 1.5px solid var(--mustard); }
.ib-label { font-weight: 700; margin-bottom: 4px; color: var(--mustard); }
.ib-list { margin: 0; padding-left: 20px; column-count: 2; column-gap: 20px; }
.ib-list li { margin-bottom: 2px; }
.ib-list a { color: #8b6a00; text-decoration: none; }
.answer-box { background: #faf6ee; border: 2px solid var(--navy); border-radius: var(--radius); padding: 14px 16px; margin-bottom: 15px; }
.ab-label { font-size: 0.85rem; font-weight: 700; color: var(--navy); text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px; }
.options-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.options-list li { padding: 10px 14px; border-radius: 6px; border: 1.5px solid transparent; display: flex; align-items: center; font-size: 0.95rem; }
.options-list li.correct { background: #d4edda; border-color: #28a745; color: #155724; font-weight: 600; }
.options-list li.wrong { background: #f8f9fa; border-color: #dee2e6; color: #666; }
.opt-letter { font-weight: 700; font-size: 0.8rem; width: 24px; text-align: center; flex-shrink: 0; margin-right: 12px; }
.opt-tick { margin-left: auto; font-size: 1.1rem; }
.def-box { background: linear-gradient(135deg, #fff8e1, #fff3cd); border: 2px solid #ffb300; border-radius: var(--radius); padding: 12px 16px; margin-bottom: 14px; }
.def-box-label { font-size: 0.75rem; font-weight: 700; color: #7a5000; text-transform: uppercase; display: block; margin-bottom: 6px; letter-spacing: 1px; }
.def-box p { margin: 0; font-size: 0.95rem; line-height: 1.5; color: #333; font-style: italic; }
.section-box { border-radius: var(--radius); border: 1.5px solid; padding: 14px 16px; margin-bottom: 15px; box-shadow: var(--shadow-sm); }
.sb-heading { font-family: var(--font-title); font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; padding-bottom: 6px; border-bottom: 1px dashed rgba(0,0,0,0.12); }
.sh-icon { font-size: 1.1rem; }
.navy { background: var(--navy-bg); border-color: var(--navy); } .navy .sb-heading { color: var(--navy); }
.maroon { background: var(--maroon-bg); border-color: var(--maroon); } .maroon .sb-heading { color: var(--maroon); }
.green { background: var(--green-bg); border-color: var(--green); } .green .sb-heading { color: var(--green); }
.purple { background: var(--purple-bg); border-color: var(--purple); } .purple .sb-heading { color: var(--purple); }
.teal { background: var(--teal-bg); border-color: var(--teal); } .teal .sb-heading { color: var(--teal); }
.mustard { background: var(--mustard-bg); border-color: var(--mustard); } .mustard .sb-heading { color: var(--mustard); }
.indigo { background: var(--indigo-bg); border-color: var(--indigo); } .indigo .sb-heading { color: var(--indigo); }
.rose { background: var(--rose-bg); border-color: var(--rose); } .rose .sb-heading { color: var(--rose); }
.verdict-table, .comp-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.verdict-table th { background: #1a3a6b; color: #fff; padding: 7px 10px; text-align: left; font-size: 0.75rem; }
.verdict-table td { padding: 7px 10px; border-bottom: 1px solid rgba(0,0,0,0.08); vertical-align: top; }
.tag-correct { display: inline-flex; align-items: center; gap: 4px; background: #d4edda; color: #155724; border: 1px solid #c3e6cb; border-radius: 12px; padding: 2px 9px; font-size: 0.75rem; font-weight: 700; }
.tag-incorrect { display: inline-flex; align-items: center; gap: 4px; background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 12px; padding: 2px 9px; font-size: 0.75rem; font-weight: 700; }
.comp-table th { background: var(--green); color: #fff; padding: 6px 10px; text-align: left; font-size: 0.75rem; }
.comp-table td { padding: 6px 10px; border-bottom: 1px solid rgba(0,0,0,0.08); }
.key-points-list { list-style: none; padding: 0; margin: 0; }
.key-points-list li { display: flex; align-items: flex-start; gap: 8px; font-size: 0.95rem; line-height: 1.5; margin-bottom: 8px; }
.kp-bullet { color: var(--navy); font-size: 1.1rem; flex-shrink: 0; }
.conclusion-box { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border: 2px solid #388e3c; padding: 16px; border-radius: var(--radius); display: flex; gap: 16px; margin-bottom: 20px; align-items: flex-start; }
.cb-icon { font-size: 2rem; color: #1b5e20; flex-shrink: 0; }
.cb-label { font-size: 0.8rem; font-weight: 700; color: #1b5e20; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 1px; }
.conclusion-box p { margin: 0 0 8px 0; font-size: 0.95rem; line-height: 1.5; color: #1b5e20; font-weight: 600; }
.conclusion-box p:last-child { margin: 0; }
.timeline { position: relative; padding-left: 28px; }
.timeline::before { content: ''; position: absolute; left: 10px; top: 0; bottom: 0; width: 2px; background: linear-gradient(to bottom, var(--navy), var(--teal)); border-radius: 1px; }
.tl-item { position: relative; margin-bottom: 14px; }
.tl-item::before { content: ''; position: absolute; left: -22px; top: 6px; width: 10px; height: 10px; background: var(--navy); border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 2px var(--navy); }
.tl-year { font-weight: 700; color: var(--navy); font-size: 0.9rem; display: inline-block; background: var(--navy-bg); border: 1px solid var(--navy); border-radius: 4px; padding: 1px 7px; margin-bottom: 4px; }
.tl-text { font-size: 0.9rem; color: #333; line-height: 1.4; }
.terms-strip { display: flex; flex-wrap: wrap; gap: 8px; }
.term-chip { background: #f3ead8; border: 1.5px solid #b8a980; padding: 4px 10px; border-radius: 16px; font-size: 0.85rem; font-weight: 500; color: #5a4500; }
.revision-box { background: linear-gradient(135deg, #ede7d5, #e8eef7); border: 2px dashed #1a3a6b; padding: 16px; border-radius: var(--radius); margin-bottom: 20px; }
.rb-title { font-family: var(--font-title); font-size: 0.95rem; font-weight: 700; color: var(--navy); text-transform: uppercase; margin-bottom: 12px; letter-spacing: 1px; display: flex; align-items: center; gap: 7px; }
.revision-list { margin: 0; padding: 0; list-style: none; }
.revision-list li { display: flex; gap: 10px; font-size: 0.9rem; line-height: 1.45; color: #333; margin-bottom: 8px; align-items: flex-start; }
.chk { color: #666; font-size: 1.2rem; flex-shrink: 0; }
.quote-box { text-align: center; font-family: var(--font-title); font-size: 1.1rem; color: #666; font-style: italic; padding: 20px; position: relative; margin-top: 20px; border-top: 1px solid #eee; }
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
{% if show_title %}
<h1 style="text-align:center;font-family:Georgia,serif;color:#1a3a6b;margin-bottom:24px;padding:16px">&#128218; Study Notes &mdash; All {{ total_count }} Questions</h1>
{% endif %}
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
            <div>
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
<div style="page-break-after:always;margin:20px 0"></div>
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

def generate_html(questions, show_title=True, total_count=None):
    if total_count is None:
        total_count = len(questions)
    prepared_qs = [prepare_question_data(q) for q in questions]
    template = Template(HTML_TEMPLATE)
    
    html_out = template.render(
        questions=prepared_qs,
        css=CSS_CONTENT,
        escape=escape,
        highlight=highlight,
        show_title=show_title,
        total_count=total_count
    )
    return html_out

def build_pdf(questions, output_path):
    """
    Builds a PDF from questions using chunking to avoid WeasyPrint OOMs.
    Generates 10 questions at a time and merges using pypdf.
    """
    chunk_size = 10
    merger = PdfWriter()
    total_count = len(questions)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(0, len(questions), chunk_size):
            chunk = questions[i:i + chunk_size]
            show_title = (i == 0)
            html_str = generate_html(chunk, show_title=show_title, total_count=total_count)
            chunk_pdf_path = os.path.join(tmpdir, f"chunk_{i}.pdf")
            
            # Generate temporary PDF
            HTML(string=html_str).write_pdf(chunk_pdf_path)
            
            # Append to merger
            merger.append(chunk_pdf_path)
            
        # Write merged PDF to the final output path
        merger.write(output_path)
        merger.close()
