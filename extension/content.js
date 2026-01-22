// content.js - FINAL "Unique ID" Version (Duplicate Killer)

(() => {
  const API_BASE = "http://127.0.0.1:8000";
  const PREDICT_URL = `${API_BASE}/predict`;
  const EXPLAIN_URL = `${API_BASE}/explain`;

  // --- 1. STRICT SELECTORS ---
  function findReviewElements() {
    const selList = [
      '[id^="customer_review-"]',  // The Master Key
      '[data-hook="review"]'       
    ];
    
    let allNodes = [];
    selList.forEach(sel => {
        const found = document.querySelectorAll(sel);
        allNodes = [...allNodes, ...Array.from(found)];
    });

    return [...new Set(allNodes)];
  }

  // Helper to get a unique ID for every review
  function getReviewId(node) {
      // 1. Try to get the actual Amazon ID (Best)
      if (node.id && node.id.startsWith('customer_review-')) {
          return node.id;
      }
      // 2. Fallback: Generate a random ID and stick it to the node
      if (!node.dataset.rgUniqueId) {
          node.dataset.rgUniqueId = 'rg-rev-' + Math.random().toString(36).substr(2, 9);
      }
      return node.dataset.rgUniqueId;
  }

  function extractReviews() {
    try { document.querySelectorAll('.a-expander-header a').forEach(btn => btn.click()); } catch(e) {}

    const reviewEls = findReviewElements();
    const reviews = [];
    
    reviewEls.forEach(el => {
      const revId = getReviewId(el);

      // 🛑 STOP DUPLICATES (Level 1: Memory Check)
      // Check if a badge for THIS specific ID already exists anywhere in the DOM
      if (document.getElementById(`badge-wrapper-${revId}`)) {
          return; 
      }

      // 🛑 SAFETY CHECK
      if (!el.querySelector('.a-icon-alt') && !el.querySelector('.review-date')) return;

      const isVerified = !!el.innerText.match(/Verified Purchase/i);
      
      // --- TEXT EXTRACTION ---
      let fullText = "";
      const standardBox = el.querySelector('[data-hook="review-body"] span') || 
                          el.querySelector('.review-text-content span');
      
      if (standardBox) {
          fullText = standardBox.innerText.trim();
      } else {
          const clone = el.cloneNode(true);
          const junk = ['.a-profile', '.review-date', '.review-title', '.a-icon-alt', 
                        '.review-comments', '.cr-footer-line', 'button', '.helpful-button-wrapper', '.video-block'];
          junk.forEach(s => clone.querySelectorAll(s).forEach(n => n.remove()));
          fullText = clone.innerText.trim();
      }

      fullText = fullText.replace(/Read more|Helpful|Report/gi, '').trim();

      if (fullText.length > 5 && fullText.includes(' ')) { 
          reviews.push({ text: fullText, node: el, isVerified: isVerified, id: revId });
      }
    });
    
    return reviews;
  }

  // --- 2. BACKEND API ---
  async function analyzeReviewText(text) {
    try {
      const res = await fetch(PREDICT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (!res.ok) return { label: 'ERR', confidence: 0.0 };
      return await res.json();
    } catch (e) {
      return { label: 'ERR', confidence: 0.0 };
    }
  }

  async function fetchExplanation(text, label, confidence, container) {
    try {
        container.innerHTML = '<span class="loading-spinner">↻</span> <i>Asking AI...</i>';
        const res = await fetch(EXPLAIN_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, label, confidence })
        });
        const data = await res.json();
        
        if (data.explanation) {
            container.innerHTML = `<b>AI Logic:</b> ${data.explanation}`;
            container.style.borderLeft = `3px solid ${label === 'FAKE' ? '#e53935' : '#43a047'}`;
        } else {
            container.innerHTML = 'Could not generate explanation.';
        }
    } catch (e) {
        container.innerHTML = 'Error connecting to AI.';
    }
  }

  // --- 3. UI HELPERS ---
  function makeBadge(label, confidence, isVerified) {
    const span = document.createElement('span');
    span.className = 'reviewguard-badge';
    span.style.cssText = 'display:inline-block;padding:2px 6px;margin-left:8px;border-radius:4px;font-weight:600;font-size:12px;color:white;vertical-align:middle;';
    
    let finalLabel = label;
    let color = '#f57c00'; 

    if (label === 'FAKE') {
        if (isVerified) { finalLabel = 'SUSPICIOUS'; color = '#ff9800'; } 
        else { color = '#e53935'; }
    } else if (label === 'GENUINE') { color = '#43a047'; }

    if (label === 'ERR') {
        span.style.background = '#777'; span.textContent = 'Error';
    } else {
        const dispConf = Math.min(confidence, 0.99) * 100;
        span.style.background = color;
        span.textContent = `${finalLabel} (${Math.round(dispConf)}%)`;
    }
    return { span, finalLabel };
  }

  async function annotateReview(r, result) {
    // 🛑 STOP DUPLICATES (Level 2: Strict DOM Check)
    // We assign a specific ID to the wrapper based on the review ID.
    // If that ID exists, we DO NOT add another one.
    const wrapperId = `badge-wrapper-${r.id}`;
    if (document.getElementById(wrapperId)) return;

    const wrapper = document.createElement('div');
    wrapper.id = wrapperId; // <--- THIS IS THE KEY FIX
    wrapper.className = 'reviewguard-wrapper';
    wrapper.style.cssText = 'margin-top:5px; margin-bottom:5px; display:flex; align-items:center; gap:10px;';

    const { span } = makeBadge(result.label, result.confidence ?? 0, r.isVerified);
    wrapper.appendChild(span);

    if (result.label !== 'ERR') {
        const btn = document.createElement('button');
        btn.textContent = '💡 Why?';
        btn.style.cssText = 'border:1px solid #ccc; background:#fff; cursor:pointer; font-size:11px; padding:2px 8px; border-radius:10px; color:#333;';
        
        const explainBox = document.createElement('div');
        explainBox.style.cssText = 'display:none; margin-top:5px; font-size:13px; color:#333; background:#f0f2f5; padding:8px; border-radius:4px; width:100%;';
        
        btn.onclick = (e) => {
            e.preventDefault();
            btn.style.display = 'none'; 
            explainBox.style.display = 'block'; 
            fetchExplanation(r.text, result.label, result.confidence, explainBox);
        };
        wrapper.appendChild(btn);
        
        const header = r.node.querySelector('.a-profile') || r.node.querySelector('.review-header') || r.node.querySelector('.a-row');
        if (header) {
            header.insertAdjacentElement('afterend', wrapper);
            wrapper.insertAdjacentElement('afterend', explainBox);
        } else {
            r.node.prepend(wrapper);
            wrapper.insertAdjacentElement('afterend', explainBox);
        }
    } else {
        r.node.prepend(wrapper);
    }
  }

  // --- 4. BUTTON & TRIGGER LOGIC ---
  let processing = false;

  async function analyzeAllReviews() {
      if (processing) return;
      processing = true;
      
      const btn = document.getElementById('reviewguard-analyze-all');
      if (btn) { btn.textContent = '⏳ Analyzing...'; btn.style.opacity = '0.7'; }

      const reviews = extractReviews();
      
      if (reviews.length === 0) {
          alert("No new reviews found. Try scrolling down!");
          processing = false;
          if (btn) { btn.textContent = '🔍 Analyze Reviews'; btn.style.opacity = '1'; }
          return;
      }

      console.log(`[ReviewGuard] Processing ${reviews.length} reviews...`);

      const BATCH_SIZE = 3;
      for (let i = 0; i < reviews.length; i += BATCH_SIZE) {
          const chunk = reviews.slice(i, i + BATCH_SIZE);
          await Promise.all(chunk.map(async (r) => {
              const result = await analyzeReviewText(r.text);
              await annotateReview(r, result);
          }));
      }

      processing = false;
      if (btn) { btn.textContent = '🔍 Analyze More'; btn.style.opacity = '1'; }
  }

  function injectButton() {
    if (document.getElementById('reviewguard-analyze-all')) return;
    const btn = document.createElement('button');
    btn.id = 'reviewguard-analyze-all';
    btn.textContent = '🔍 Analyze Reviews';
    btn.style.cssText = `position: fixed; bottom: 20px; right: 20px; z-index: 2147483647; padding: 12px 24px; background: #232f3e; color: white; border: 2px solid white; border-radius: 50px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); cursor: pointer; transition: all 0.2s;`;
    btn.onmouseover = () => btn.style.transform = 'scale(1.05)';
    btn.onmouseout = () => btn.style.transform = 'scale(1)';
    btn.onclick = analyzeAllReviews;
    document.body.appendChild(btn);
  }

  injectButton();
  setInterval(injectButton, 1000);

})();