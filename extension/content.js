// content.js - robust extractor + analyze button + backend call

(() => {
  const BACKEND = "http://localhost:8000/predict"; // your API

  // Utility: safe query with multiple selectors
  function qs(root, selectors) {
    for (const s of selectors) {
      const el = root.querySelector(s);
      if (el) return el;
    }f
    return null;
  }

  // Try multiple selectors for review blocks used across Amazon pages
  function findReviewElements() {
    const selList = [
      '.review', // common
      '.a-section.review.aok-relative', // alternate
      '[data-hook="review"]', // data-hook style
      '.review-item' // other variants
    ];
    let nodes = [];
    for (const sel of selList) {
      const found = Array.from(document.querySelectorAll(sel));
      if (found.length) {
        nodes = found;
        break;
      }
    }
    // as fallback, try anything that looks like a review text container
    if (!nodes.length) {
      nodes = Array.from(document.querySelectorAll('.a-row .a-size-base.review-text, .review-text-content, .a-size-base.review-text'));
    }
    return nodes;
  }

function extractReviews() {
  // click any "Read more" to expand text
  document.querySelectorAll('.review-data .a-expander-header a, .a-expander-prompt').forEach(btn => btn.click());

  const reviewEls = document.querySelectorAll('[data-hook="review"]');
  const reviews = [];
  reviewEls.forEach(el => {
    const textEl = el.querySelector('.review-text-content span, [data-hook="review-body"] span');
    if (textEl) {
      const fullText = textEl.innerText.trim();
      reviews.push({ text: fullText, node: el });
    }
  });
  console.log('[ReviewGuard] Extracted', reviews.length, 'reviews');
  return reviews;
}


  // Call your backend
  async function analyzeReviewText(text) {
    try {
      const res = await fetch(BACKEND, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (!res.ok) {
        console.error('[ReviewGuard] backend returned', res.status);
        return { label: 'ERR', confidence: 0.0 };
      }
      return await res.json();
    } catch (e) {
      console.error('[ReviewGuard] network error', e);
      return { label: 'ERR', confidence: 0.0 };
    }
  }

  // Create / return a single badge element (so we can remove duplicates)
  function makeBadge(label, confidence) {
    const span = document.createElement('span');
    span.className = 'reviewguard-badge';
    span.style.cssText = [
      'display:inline-block',
      'padding:2px 6px',
      'margin-left:8px',
      'border-radius:4px',
      'font-weight:600',
      'font-size:12px',
      'color:white'
    ].join(';');
    if (label === 'OR') span.style.background = '#e53935';
    else if (label === 'CG') span.style.background = '#43a047';
    else span.style.background = '#777';
    span.textContent = `${label} (${Math.round(confidence*100)}%)`;
    return span;
  }

  function highlightKeywordsInNode(root, keywords) {
  const walker = document.createTreeWalker(
    root,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );

  let node;
  while ((node = walker.nextNode())) {
    keywords.forEach(word => {
      if (!word || word.length < 3) return;
      const regex = new RegExp(`\\b(${word})\\b`, 'gi');
      if (regex.test(node.nodeValue)) {
        const span = document.createElement('span');
        span.innerHTML = node.nodeValue.replace(
          regex,
          `<mark style="background:#ffe082;padding:1px;">$1</mark>`
        );
        node.parentNode.replaceChild(span, node);
      }
    });
  }
}


  async function annotateReview(r) {
    const badge = makeBadge(r.result.label, r.result.confidence ?? 0);
    // remove previous badge if exists
    const existing = r.node.querySelector('.reviewguard-badge');
    if (existing) existing.remove();
    // try to insert near the header of the review
    const header = qs(r.node, ['.a-row', '.review-header', '.a-profile']);
    if (header) header.insertAdjacentElement('afterend', badge);
    else r.node.appendChild(badge);

    //-----PHASE 3 MODIFICATION-----
    if(explanation){
      let expl=r.node.querySelector('.reviewguard-expl');
      if(!expl){
        expl=document.createElement('div');
        expl.className='reviewguard-expl';
        expl.style.cssText=
        'margin-top:4px;font-size:12px;color:#555;font-style:italic;';
        badge.insertAdjacentElement('afterend', expl);
      }
      expl.textContent=explanation;
    }

    if(keypwrds.length){
      highlightKeywordsInNode(r.node,keywords);
    }
  }

  async function analyzeAllReviews(ev) {
    try {
      ev && ev.preventDefault();
      console.log('[ReviewGuard] analyzeAllReviews clicked');
      const reviews = extractReviews();
      if (!reviews.length) {
        console.warn('[ReviewGuard] No reviews found to analyze.');
        alert('No reviews found on this page (try scrolling to load more reviews).');
        return;
      }

      // show quick UI: progress bar in page
      showProgress(true);

      for (let i = 0; i < reviews.length; ++i) {
        const r = reviews[i];
        // small delay so we don't flood backend
        await new Promise(res => setTimeout(res, 50));
        const result = await analyzeReviewText(r.text);
        r.result = result;
        annotateReview(r);
        console.log(`[ReviewGuard] #${i+1}/${reviews.length}`, result, r.text.slice(0,80));
      }

      showProgress(false);

      // overall score
      const orScores = reviews.filter(x => x.result && x.result.label === 'OR').map(x => x.result.confidence);
      const pageScore = orScores.length ? (orScores.reduce((a,b)=>a+b,0)/orScores.length) : 0;
      showSummary(pageScore, reviews.length, orScores.length);
    } catch (err) {
      console.error('[ReviewGuard] analyzeAllReviews error', err);
      showProgress(false);
    }
  }

  // UI helpers
  function addAnalyzeButton() {
    if (document.getElementById('reviewguard-analyze-all')) return;
    const btn = document.createElement('button');
    btn.id = 'reviewguard-analyze-all';
    btn.textContent = 'Analyze All Reviews';
    btn.style.cssText = 'position:relative;z-index:99999;padding:8px 10px;border-radius:6px;background:#ff9900;color:white;border:none;cursor:pointer;margin:8px;';
    btn.addEventListener('click', analyzeAllReviews);

    // Try to insert near review list container
    const container = document.querySelector('#cm_cr-review_list') || document.querySelector('#reviews-medley-footer') || document.body;
    if (container) container.prepend(btn);
    else document.body.appendChild(btn);

    // progress element
    const p = document.createElement('div');
    p.id = 'reviewguard-progress';
    p.style.cssText = 'display:none;margin:8px;font-size:13px;';
    btn.insertAdjacentElement('afterend', p);
  }

  function showProgress(show) {
    const p = document.getElementById('reviewguard-progress');
    if (!p) return;
    p.style.display = show ? 'block' : 'none';
    p.textContent = show ? 'Analyzing reviews... (this may take a few seconds)' : '';
  }

  function showSummary(pageScore, total, suspectCount) {
    const txt = `Page suspicious score: ${Math.round(pageScore*100)}% — ${suspectCount}/${total} flagged`;
    console.log('[ReviewGuard] SUMMARY', txt);
    // create a short overlay
    let overlay = document.getElementById('reviewguard-summary');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'reviewguard-summary';
      overlay.style.cssText = 'position:fixed;right:16px;bottom:16px;background:#222;color:white;padding:10px;border-radius:8px;z-index:999999;font-size:13px;';
      document.body.appendChild(overlay);
    }
    overlay.textContent = txt;
    setTimeout(()=> overlay.remove(), 8000);
  }

  // MutationObserver so we can add the button when reviews appear
  const observer = new MutationObserver((mutations) => {
    // add button only once reviews are present
    const nodes = findReviewElements();
    if (nodes.length) addAnalyzeButton();
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Add button immediately (if page already loaded)
  window.addEventListener('load', () => {
    setTimeout(() => {
      addAnalyzeButton();
      console.log('[ReviewGuard] loaded and button added (if reviews present)');
    }, 2000);
  });

  // Also try right away
  setTimeout(() => {
    addAnalyzeButton();
  }, 1000);

  // expose for debugging
  window.ReviewGuard = {
    extractReviews,
    analyzeAllReviews,
  };
})();
