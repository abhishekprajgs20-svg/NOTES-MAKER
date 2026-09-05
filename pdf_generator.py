import os
import tempfile
from jinja2 import Template
from pypdf import PdfWriter
from parser import (
    split_sentences, extract_definition, extract_verdicts,
    extract_years, extract_key_terms, extract_conclusion,
    extract_items, get_title, highlight, escape
)

CC = ['navy', 'maroon', 'green', 'purple', 'teal', 'mustard', 'indigo', 'rose']

CSS_CONTENT = """
:root{--font-title:Georgia,"Bookman Old Style","Times New Roman",serif;--font-body:"Segoe UI",Calibri,Arial,sans-serif;--cream:#faf6ee;--cream2:#f3ead8;--paper:#fefcf6;--navy:#1a3a6b;--maroon:#8b1a1a;--green:#1a6b3a;--purple:#5a1a8b;--teal:#1a6b6b;--mustard:#8b6a00;--indigo:#2d2d8b;--rose:#8b2d5a;--navy-bg:#e8eef7;--maroon-bg:#f7e8e8;--green-bg:#e8f7ee;--purple-bg:#f0e8f7;--teal-bg:#e8f7f7;--mustard-bg:#f7f3e8;--indigo-bg:#eeeef7;--rose-bg:#f7e8ef;--sidebar-w:270px;--header-h:56px;--radius:10px;--shadow:0 2px 10px rgba(0,0,0,.10);--shadow-sm:0 1px 4px rgba(0,0,0,.08)}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font-body);font-size:15px;background:#e8e2d8;color:#1a1a1a;min-height:100vh;overflow-x:hidden}
#upload-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;background:linear-gradient(135deg,#1a3a6b 0%,#5a1a8b 50%,#8b1a1a 100%);padding:24px}
.brand{font-family:var(--font-title);font-size:2.4rem;color:#fff;text-align:center;margin-bottom:8px;text-shadow:0 2px 12px rgba(0,0,0,.3)}
.brand span{color:#ffd700}
.subtitle{color:rgba(255,255,255,.8);font-size:1rem;text-align:center;margin-bottom:40px}
#drop-zone{background:rgba(255,255,255,.12);border:2.5px dashed rgba(255,255,255,.5);border-radius:18px;width:100%;max-width:520px;padding:56px 32px;text-align:center;cursor:pointer;transition:all .25s;backdrop-filter:blur(8px)}
#drop-zone:hover,#drop-zone.drag-over{background:rgba(255,255,255,.22);border-color:#ffd700;transform:scale(1.01)}
.drop-icon{font-size:3.5rem;display:block;margin-bottom:16px}
#drop-zone p{color:rgba(255,255,255,.85);font-size:1.05rem;margin-bottom:20px}
#drop-zone small{color:rgba(255,255,255,.55);font-size:.8rem}
#file-input{display:none}
.btn-upload{display:inline-block;background:linear-gradient(135deg,#ffd700,#ffb300);color:#1a1a1a;font-weight:700;font-size:.95rem;padding:12px 32px;border-radius:30px;border:none;cursor:pointer;transition:all .2s;margin-top:12px;box-shadow:0 4px 16px rgba(255,200,0,.35)}
.btn-upload:hover{transform:translateY(-2px)}
#error-msg{margin-top:16px;background:rgba(255,80,80,.15);border:1.5px solid rgba(255,80,80,.5);color:#fff;border-radius:10px;padding:12px 20px;font-size:.9rem;display:none;max-width:520px;text-align:center}
#loading-screen{display:none;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;background:linear-gradient(135deg,#1a3a6b 0%,#5a1a8b 50%,#8b1a1a 100%)}
.spinner{width:60px;height:60px;border:5px solid rgba(255,255,255,.2);border-top-color:#ffd700;border-radius:50%;animation:spin .8s linear infinite;margin-bottom:24px}
@keyframes spin{to{transform:rotate(360deg)}}
#loading-text{color:#fff;font-size:1.1rem;text-align:center}
#loading-progress{width:300px;height:6px;background:rgba(255,255,255,.2);border-radius:3px;margin-top:16px;overflow:hidden}
#loading-bar{height:100%;background:linear-gradient(90deg,#ffd700,#ffb300);border-radius:3px;width:0%;transition:width .3s ease}
#app-screen{display:none;height:100vh;flex-direction:column}
#toolbar{height:var(--header-h);background:linear-gradient(90deg,#1a3a6b,#2d2d8b);display:flex;align-items:center;padding:0 16px;gap:10px;box-shadow:0 2px 8px rgba(0,0,0,.3);z-index:100;flex-shrink:0;overflow:hidden}
.toolbar-brand{font-family:var(--font-title);color:#ffd700;font-size:1.05rem;font-weight:700;white-space:nowrap;flex-shrink:0}
.sep{color:rgba(255,255,255,.2);flex-shrink:0}
.tbtn{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);color:#fff;border-radius:7px;padding:6px 12px;font-size:.8rem;cursor:pointer;transition:all .18s;white-space:nowrap;display:flex;align-items:center;gap:5px;flex-shrink:0}
.tbtn:hover{background:rgba(255,255,255,.22)}
.tbtn:disabled{opacity:.4;cursor:not-allowed}
#nav-info{color:rgba(255,255,255,.65);font-size:.8rem;white-space:nowrap;flex-shrink:0}
.toolbar-spacer{flex:1;min-width:8px}
.font-ctrl{display:flex;align-items:center;gap:4px;flex-shrink:0}
.font-ctrl label{color:rgba(255,255,255,.6);font-size:.75rem}
.font-btn{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);color:#fff;width:26px;height:26px;border-radius:5px;cursor:pointer;font-size:.95rem;display:flex;align-items:center;justify-content:center;transition:all .15s}
.font-btn:hover{background:rgba(255,255,255,.2)}
#sidebar-toggle{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);color:#fff;width:32px;height:32px;border-radius:6px;cursor:pointer;font-size:1.1rem;display:flex;align-items:center;justify-content:center;flex-shrink:0}
#sidebar-toggle:hover{background:rgba(255,255,255,.2)}
#app-body{display:flex;flex:1;overflow:hidden}
#sidebar{width:var(--sidebar-w);background:#f7f3ea;border-right:2px solid #d4cbb8;display:flex;flex-direction:column;overflow:hidden;flex-shrink:0;transition:width .25s,opacity .25s}
#sidebar.collapsed{width:0;opacity:0;pointer-events:none}
#sidebar-header{padding:12px 14px 10px;border-bottom:1.5px solid #d4cbb8;background:#ede7d5;flex-shrink:0}
#sidebar-header h3{font-family:var(--font-title);font-size:.92rem;color:#1a3a6b;margin-bottom:8px}
#search-input{width:100%;padding:7px 10px;border:1.5px solid #c4b89a;border-radius:7px;background:#faf6ee;font-size:.82rem;color:#333;outline:none;transition:border-color .2s}
#search-input:focus{border-color:#1a3a6b}
#sidebar-list{flex:1;overflow-y:auto;padding:8px 0}
#sidebar-list::-webkit-scrollbar{width:5px}
#sidebar-list::-webkit-scrollbar-thumb{background:#c4b89a;border-radius:3px}
.sidebar-item{padding:9px 14px;cursor:pointer;border-left:3px solid transparent;transition:all .15s;border-bottom:1px solid rgba(0,0,0,.05)}
.sidebar-item:hover{background:#ede7d5;border-left-color:#8b6a00}
.sidebar-item.active{background:#e8eef7;border-left-color:#1a3a6b;font-weight:600}
.q-num-label{font-size:.7rem;color:#8b6a00;font-weight:700;letter-spacing:.5px;display:block;margin-bottom:2px}
.q-title-label{font-size:.82rem;color:#333;line-height:1.35;display:block}
.sidebar-item.active .q-title-label{color:#1a3a6b}
.sidebar-item.hidden{display:none}
#main-panel{flex:1;overflow-y:auto;background:#e8e2d8;padding:20px 24px}
#main-panel::-webkit-scrollbar{width:7px}
#main-panel::-webkit-scrollbar-thumb{background:#c4b89a;border-radius:4px}
#no-question{display:flex;align-items:center;justify-content:center;height:100%;color:#888;font-style:italic;font-size:1.1rem}
.note-page{background:#fefcf6;background-image:repeating-linear-gradient(transparent,transparent 27px,rgba(0,0,0,.055) 27px,rgba(0,0,0,.055) 28px);border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.13),0 1px 3px rgba(0,0,0,.08);padding:28px 32px 36px;max-width:960px;margin:0 auto;position:relative}
.parse-warning{position:absolute;top:10px;right:14px;background:#fff3cd;border:1px solid #ffc107;color:#856404;font-size:.72rem;padding:3px 9px;border-radius:12px}
.note-header{display:grid;grid-template-columns:200px 1fr;gap:20px;margin-bottom:22px;align-items:start}
.note-title-card{border:2px solid var(--navy);border-radius:var(--radius);padding:14px 16px;background:linear-gradient(135deg,#e8eef7,#dde5f5);text-align:center}
.crown-icon{font-size:1.8rem;display:block;margin-bottom:6px}
.q-label-card{font-size:.68rem;font-weight:700;color:var(--navy);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px}
.q-title-card{font-family:var(--font-title);font-size:1.05rem;color:var(--navy);line-height:1.3;font-weight:700}
.q-subject-card{font-size:.68rem;color:#8b6a00;margin-top:6px;font-style:italic;border-top:1px solid rgba(26,58,107,.2);padding-top:5px}
.note-header-right{display:flex;flex-direction:column;gap:12px}
.note-question-box{background:var(--navy-bg);border:1.5px solid var(--navy);border-radius:var(--radius);padding:12px 16px}
.qb-label{font-size:.68rem;font-weight:700;color:var(--navy);letter-spacing:1px;text-transform:uppercase;margin-bottom:6px}
.qb-text{font-size:.87rem;line-height:1.55;color:#222}
.note-index-box{background:var(--mustard-bg);border:1.5px solid var(--mustard);border-radius:var(--radius);padding:10px 14px}
.ib-label{font-size:.68rem;font-weight:700;color:var(--mustard);letter-spacing:1px;text-transform:uppercase;margin-bottom:7px}
.ib-list{list-style:none;padding:0;columns:2;column-gap:12px}
.ib-list li{font-size:.76rem;color:#444;margin-bottom:3px;break-inside:avoid}
.ib-list li a{color:#8b6a00;text-decoration:none}
.ib-list li a:hover{color:#1a3a6b;text-decoration:underline}
.section-box{border-radius:var(--radius);border:1.5px solid;padding:14px 16px;margin-bottom:15px;box-shadow:var(--shadow-sm)}
.sb-heading{font-family:var(--font-title);font-size:.88rem;font-weight:700;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:7px;padding-bottom:6px;border-bottom:1px dashed rgba(0,0,0,.12)}
.sh-icon{font-size:1rem}
.section-box.navy{border-color:var(--navy);background:var(--navy-bg)}.section-box.navy .sb-heading{color:var(--navy)}
.section-box.maroon{border-color:var(--maroon);background:var(--maroon-bg)}.section-box.maroon .sb-heading{color:var(--maroon)}
.section-box.green{border-color:var(--green);background:var(--green-bg)}.section-box.green .sb-heading{color:var(--green)}
.section-box.purple{border-color:var(--purple);background:var(--purple-bg)}.section-box.purple .sb-heading{color:var(--purple)}
.section-box.teal{border-color:var(--teal);background:var(--teal-bg)}.section-box.teal .sb-heading{color:var(--teal)}
.section-box.mustard{border-color:var(--mustard);background:var(--mustard-bg)}.section-box.mustard .sb-heading{color:var(--mustard)}
.section-box.indigo{border-color:var(--indigo);background:var(--indigo-bg)}.section-box.indigo .sb-heading{color:var(--indigo)}
.section-box.rose{border-color:var(--rose);background:var(--rose-bg)}.section-box.rose .sb-heading{color:var(--rose)}
.def-box{background:linear-gradient(135deg,#fff8e1,#fff3cd);border:2px solid #ffb300;border-radius:var(--radius);padding:12px 16px;margin-bottom:14px}
.def-box-label{font-size:.68rem;font-weight:700;color:#7a5000;letter-spacing:1px;margin-bottom:7px;display:block}
.def-box p{font-size:.88rem;line-height:1.6;color:#333;font-style:italic}
.key-points-list{list-style:none;padding:0}
.key-points-list li{display:flex;align-items:flex-start;gap:8px;font-size:.87rem;line-height:1.55;color:#2a2a2a;margin-bottom:7px}
.kp-bullet{flex-shrink:0;margin-top:2px;color:var(--navy);font-size:.8rem}
.verdict-table{width:100%;border-collapse:collapse;font-size:.84rem;margin-top:4px}
.verdict-table th{background:#1a3a6b;color:#fff;padding:7px 10px;text-align:left;font-size:.75rem}
.verdict-table td{padding:7px 10px;border-bottom:1px solid rgba(0,0,0,.08);vertical-align:top}
.verdict-table tr:nth-child(even) td{background:rgba(0,0,0,.03)}
.verdict-table tr:hover td{background:rgba(26,58,107,.06)}
.tag-correct{display:inline-flex;align-items:center;gap:4px;background:#d4edda;color:#155724;border:1px solid #c3e6cb;border-radius:12px;padding:2px 9px;font-size:.74rem;font-weight:700;white-space:nowrap}
.tag-incorrect{display:inline-flex;align-items:center;gap:4px;background:#f8d7da;color:#721c24;border:1px solid #f5c6cb;border-radius:12px;padding:2px 9px;font-size:.74rem;font-weight:700;white-space:nowrap}
.comp-table{width:100%;border-collapse:collapse;font-size:.84rem}
.comp-table th{background:var(--green);color:#fff;padding:6px 10px;text-align:left;font-size:.75rem}
.comp-table td{padding:6px 10px;border-bottom:1px solid rgba(0,0,0,.08)}
.comp-table tr:nth-child(even) td{background:rgba(26,107,58,.04)}
.conclusion-box{background:linear-gradient(135deg,#e8f5e9,#c8e6c9);border:2px solid #388e3c;border-radius:var(--radius);padding:12px 16px;margin-bottom:14px;display:flex;gap:10px;align-items:flex-start}
.cb-icon{font-size:1.4rem;flex-shrink:0}
.cb-label{font-size:.68rem;font-weight:700;color:#1b5e20;letter-spacing:1px;text-transform:uppercase;margin-bottom:5px}
.conclusion-box p{font-size:.87rem;line-height:1.5;color:#1b5e20;font-weight:600}
.answer-box{background:#faf6ee;border:2px solid var(--navy);border-radius:var(--radius);padding:14px 16px;margin-bottom:15px}
.ab-label{font-size:.68rem;font-weight:700;color:#1a3a6b;letter-spacing:1px;text-transform:uppercase;margin-bottom:9px}
.options-list{list-style:none;padding:0}
.options-list li{padding:6px 12px;border-radius:7px;font-size:.85rem;margin-bottom:5px;border:1.5px solid transparent;display:flex;align-items:center;gap:8px}
.opt-letter{font-weight:700;font-size:.78rem;width:20px;text-align:center;flex-shrink:0}
.options-list li.correct{background:#d4edda;border-color:#28a745;color:#155724;font-weight:600}
.options-list li.wrong{background:#f8f9fa;border-color:#dee2e6;color:#666}
.opt-tick{margin-left:auto;font-size:.95rem}
.timeline{position:relative;padding-left:28px}
.timeline::before{content:'';position:absolute;left:10px;top:0;bottom:0;width:2px;background:linear-gradient(to bottom,var(--navy),var(--teal));border-radius:1px}
.tl-item{position:relative;margin-bottom:14px}
.tl-item::before{content:'';position:absolute;left:-22px;top:6px;width:10px;height:10px;background:var(--navy);border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 2px var(--navy)}
.tl-year{font-weight:700;font-size:.78rem;color:var(--navy);display:inline-block;background:var(--navy-bg);border:1px solid var(--navy);border-radius:4px;padding:1px 7px;margin-bottom:4px}
.tl-text{font-size:.84rem;color:#333;line-height:1.4}
.terms-strip{display:flex;flex-wrap:wrap;gap:7px;padding-top:4px}
.term-chip{background:#f3ead8;border:1.5px solid #b8a980;border-radius:20px;padding:4px 12px;font-size:.78rem;font-weight:600;color:#5a4500}
.term-chip:hover{background:var(--mustard-bg);border-color:var(--mustard)}
.revision-box{background:linear-gradient(135deg,#ede7d5,#e8eef7);border:2px dashed #1a3a6b;border-radius:var(--radius);padding:14px 18px;margin-top:18px}
.rb-title{font-family:var(--font-title);font-size:.95rem;color:var(--navy);margin-bottom:10px;display:flex;align-items:center;gap:7px}
.revision-list{list-style:none;padding:0}
.revision-list li{display:flex;align-items:flex-start;gap:8px;font-size:.85rem;color:#333;margin-bottom:7px;line-height:1.45}
.chk{font-size:1rem;flex-shrink:0;color:#666}
.quote-box{background:#f3ead8;border-left:4px solid var(--mustard);padding:10px 16px;margin-top:16px;border-radius:0 8px 8px 0;font-style:italic;font-size:.88rem;color:#555}
.quote-box cite{display:block;font-style:normal;font-size:.76rem;color:#888;margin-top:5px}
.kw-article{color:var(--maroon);font-weight:700}
.kw-year{color:var(--indigo);font-weight:700}
.kw-act{color:var(--purple);font-weight:700}
.kw-pct{color:var(--teal);font-weight:700}
@media print{#toolbar,#sidebar,#upload-screen,#loading-screen{display:none!important}#app-screen{display:block!important;height:auto!important}#app-body{display:block!important}#main-panel{padding:0!important;background:#fff!important;overflow:visible!important}.note-page{box-shadow:none!important;border-radius:0!important;margin:0!important;max-width:100%!important;page-break-after:always}body{background:#fff!important}}
@media(max-width:768px){.note-page{padding:16px}.note-header{grid-template-columns:1fr}}
@media(max-width:560px){#sidebar{position:absolute;z-index:200;height:calc(100vh - var(--header-h));top:var(--header-h);left:0;box-shadow:4px 0 20px rgba(0,0,0,.2)}.ib-list{columns:1}.note-header{grid-template-columns:1fr}}
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
    from weasyprint import HTML, CSS
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
