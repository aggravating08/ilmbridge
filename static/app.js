'use strict';
const $ = id => document.getElementById(id);
let sourceText = '', sourceTitle = '', practiceData = { cards: [], quiz: [] }, lastAnswer = null;
let toastTimer;
function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 6000); }
async function api(path, data) { const r = await fetch(path, data ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) } : {}); const result = await r.json(); if (!r.ok) throw new Error(result.error || 'Something went wrong. Please try again.'); return result; }
function node(tag, text, className) { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (className) el.className = className; return el; }
function wordCount() { $('word-count').textContent = `${$('notes').value.trim().split(/\s+/).filter(Boolean).length} words`; }
function clearAnswer() { lastAnswer = null; $('answer-area').hidden = true; $('empty-state').hidden = false; }
function showPanel(name) { document.querySelectorAll('.tab').forEach(tab => { const active = tab.dataset.panel === name; tab.classList.toggle('active', active); tab.setAttribute('aria-selected', String(active)); }); for (const key of ['ask', 'cards', 'quiz']) $('panel-' + key).hidden = key !== name; }
function renderPractice() {
  $('cards').replaceChildren(); $('quiz').replaceChildren(); $('score').textContent = '';
  practiceData.cards.forEach((card, i) => {
    const button = node('button', undefined, 'card'); button.type = 'button'; button.setAttribute('aria-pressed', 'false');
    const label = node('span', `CARD ${String(i + 1).padStart(2, '0')} / SOURCE [${card.source_id}]`, 'card-label');
    const text = node('span', card.front, 'card-text'); const hint = node('span', 'Click to reveal the source ↻', 'flip-label');
    button.append(label, text, hint);
    button.onclick = () => { const flipped = button.classList.toggle('flipped'); button.setAttribute('aria-pressed', String(flipped)); text.textContent = flipped ? card.back : card.front; hint.textContent = flipped ? 'Click to practise again ↻' : 'Click to reveal the source ↻'; };
    $('cards').append(button);
  });
  practiceData.quiz.forEach((q, i) => {
    const div = node('div', undefined, 'quiz-item'); const label = node('label', `${i + 1}. ${q.prompt}`); label.htmlFor = `q-${i}`;
    const input = node('input'); input.id = `q-${i}`; input.name = `q-${i}`; input.placeholder = 'The missing term…'; input.autocomplete = 'off'; input.maxLength = 120;
    const feedback = node('p', '', 'quiz-feedback'); feedback.id = `feedback-${i}`; input.setAttribute('aria-describedby', feedback.id);
    div.append(label, input, feedback); $('quiz').append(div);
  });
  if (!practiceData.cards.length) { $('cards').append(node('p', 'Add longer English sentences to generate revision cards.', 'muted')); $('quiz').append(node('p', 'No suitable English sentences found. Source search supports other scripts.', 'muted')); }
}
async function prepare(quiet = false) {
  const text = $('notes').value.trim();
  if (text.length < 30) { toast('Add at least 30 characters of course material.'); return false; }
  const data = await api('/api/practice', {text}); sourceText = text; sourceTitle = $('title').value.trim() || 'Untitled notes'; practiceData = data;
  clearAnswer(); renderPractice(); $('crumb-title').textContent = sourceTitle;
  $('source-status').textContent = `Ready to explore · ${data.cards.length} revision cards created.`;
  if (!quiet) toast('Your study space is ready. Ask your first question.'); return true;
}
$('prepare').onclick = () => prepare().catch(e => toast(e.message));
$('notes').addEventListener('input', () => { wordCount(); $('source-status').textContent = 'Notes changed. Build your study space to update.'; clearAnswer(); practiceData = {cards: [], quiz: []}; renderPractice(); });
$('title').addEventListener('input', () => { sourceTitle = $('title').value.trim() || 'Untitled notes'; $('crumb-title').textContent = sourceTitle; });
async function sample() { const data = await api('/api/sample'); $('notes').value = data.text; $('title').value = 'Biology · Photosynthesis'; wordCount(); await prepare(true); }
$('sample').onclick = () => sample().catch(e => toast(e.message));
$('upload').onchange = async event => { const file = event.target.files[0]; if (!file) return; if (file.size > 150000) { toast('Please choose a text file under 150 KB.'); return; } if (!/\.(txt|md)$/i.test(file.name)) { toast('Choose a .txt or .md file.'); return; } const text = await file.text(); if (text.length > 40000) { toast('Please use notes under 40000 characters.'); return; } $('notes').value = text; $('title').value = file.name.replace(/\.(txt|md)$/i, ''); wordCount(); try { await prepare(); } catch(e) { toast(e.message); } event.target.value = ''; };
document.querySelectorAll('.tab').forEach(tab => tab.onclick = async () => { try { if ($('notes').value.trim() !== sourceText && !await prepare(true)) return; showPanel(tab.dataset.panel); } catch(e) { toast(e.message); } });
document.querySelectorAll('[data-question]').forEach(button => button.onclick = () => { $('question').value = button.dataset.question; $('question').focus(); });
$('ask').onclick = async () => {
  const button = $('ask');
  try {
    if ($('notes').value.trim() !== sourceText && !await prepare(true)) return;
    button.disabled = true; button.textContent = $('mode').value === 'ai' ? 'Thinking locally…' : 'Finding your sources…';
    const requestText = sourceText, requestQuestion = $('question').value;
    const result = await api('/api/ask', {text: requestText, question: requestQuestion, mode: $('mode').value, language: $('language').value});
    if ($('notes').value.trim() !== requestText) { toast('Your notes changed. Ask again using the updated source.'); return; }
    lastAnswer = {...result, question: requestQuestion}; $('answer').textContent = result.answer;
    $('answer-label').textContent = result.mode === 'local_ai' ? `LOCAL AI EXPLANATION · ${result.model}` : result.mode === 'no_match' ? 'NO MATCH IN YOUR NOTES' : 'EXACT PASSAGES · SOURCE SEARCH';
    $('answer-warning').textContent = result.mode === 'local_ai' ? 'AI explanations can be wrong. Citations point to retrieved passages; they do not guarantee every claim is supported.' + (!result.citations_present ? ' This response omitted inline citations. Check the passages below.' : '') : 'Source search shows original text without AI generation. Language selection applies to AI explanations only.';
    $('source-count').textContent = `${result.sources.length} passages`; $('evidence').replaceChildren();
    result.sources.forEach(p => { const detail = node('details'); const summary = node('summary', `[${p.id}] ${p.text.slice(0, 85)}…`); detail.id = `source-${p.id}`; detail.append(summary, node('p', p.text)); $('evidence').append(detail); });
    $('answer-area').hidden = false; $('empty-state').hidden = true;
  } catch(e) { toast(e.message); } finally { button.disabled = false; button.replaceChildren(document.createTextNode('Explore question '), node('span', '↗')); }
};
$('quiz-form').onsubmit = event => { event.preventDefault(); if (!practiceData.quiz.length) return; let correct = 0; practiceData.quiz.forEach((q,i) => { const ok = $(`q-${i}`).value.trim().toLowerCase() === q.answer.toLowerCase(); if (ok) correct++; const feedback = $(`feedback-${i}`); feedback.className = `quiz-feedback ${ok ? 'correct' : 'incorrect'}`; feedback.textContent = `${ok ? '✓ Correct' : '↻ Answer: ' + q.answer} · Source [${q.source_id}]: ${q.evidence}`; }); $('score').textContent = `${correct} / ${practiceData.quiz.length} correct. Keep going.`; };
$('copy-answer').onclick = async () => { if (!lastAnswer) return; try { await navigator.clipboard.writeText(lastAnswer.answer); toast('Answer copied.'); } catch(e) { toast('Copy is unavailable. Select the answer text to copy it.'); } };
$('export').onclick = () => { if (!sourceText || sourceText !== $('notes').value.trim()) { toast('Build your study space before exporting.'); return; } const lines = [`# ${sourceTitle}`, '', 'Created with IlmBridge. Check all explanations against the source.', '', '## Your notes', sourceText, '', '## Revision cards']; practiceData.cards.forEach((c,i) => lines.push(`\n${i+1}. ${c.front}\nAnswer: ${c.back} [${c.source_id}]`)); if (lastAnswer) { lines.push('', `## ${lastAnswer.question}`, `Mode: ${lastAnswer.mode}`, lastAnswer.answer, '', '### Retrieved evidence'); lastAnswer.sources.forEach(p => lines.push(`[${p.id}] ${p.text}`)); } const url = URL.createObjectURL(new Blob([lines.join('\n')], {type: 'text/markdown;charset=utf-8'})); const a = node('a'); a.href = url; a.download = 'ilmbridge-study-pack.md'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); toast('Your study pack is downloaded.'); };
async function init() { await sample(); const s = await api('/api/status'); $('engine-label').textContent = s.ready ? 'Your local learning companion is ready.' : 'Source tools ready · local AI needs setup'; $('engine-detail').textContent = s.ready ? `${s.model} · no cloud API · notes stay on this device` : s.message; $('engine-pill').textContent = s.ready ? 'AI CONNECTED' : 'SOURCE MODE READY'; if (!s.ready) $('mode').value = 'source'; }
init().catch(e => toast(e.message));
