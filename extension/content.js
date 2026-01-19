// content.js - Final Version (Auto-Scroll + Hybrid Logic + Video Support)

(() => {
  const API_BASE = "http://127.0.0.1:8000";
  const PREDICT_URL = `${API_BASE}/predict`;
  const EXPLAIN_URL = `${API_BASE}/explain`;

  // --- 1. ROBUST SELECTORS (Updated for Videos) ---
  function findReviewElements() {
    const selList = [
      '[data-hook="review"]',            // Standard Desktop
      '.review',                         // Generic Fallback
      '.a-section.review.aok-relative',  // Specific Amazon container
      '.review-item',                    // Mobile/Other layouts
      '.review-text-content',            // Isolated text blocks
      
      // 🎥 NEW: Video Review Specific Selectors
      '.a-section.celwidget',            // Often wraps video reviews
      '[id^="customer_review-"]'         // Catches ALL reviews by ID (Best Catch-All)
    ];
    
    let allNodes = [];
    selList.forEach(sel => {
        const found = document.querySelectorAll(sel);
        allNodes = [...allNodes, ...Array.from(found)];
    });

    // Deduplicate: If we found a child AND its parent, keep only the unique references
    const uniqueNodes = new Set(allNodes);
    return [...uniqueNodes];
  }

  function extractReviews() {
    // Auto-expand "Read more" links
    try {
        document.querySelectorAll('.a-expander-header a').forEach(btn => btn.click());
    } catch(e) {}

    const reviewEls = findReviewElements();
    const reviews = [];
    
    reviewEls.forEach(el => {
      // SKIP if already analyzed or processed
      if (el.querySelector('.reviewguard-wrapper') || el.closest('.reviewguard-processed')) {
          return; 
      }
      
      // Mark as processed immediately
      el.classList.add('reviewguard-processed');

      // Check for Verified Purchase Badge
      const isVerified = !!el.innerText.match(/Verified Purchase/i);

      // --- TEXT EXTRACTION STRATEGY (Updated) ---
      // 1. Try standard text container
      let textEl = el.querySelector('[data-hook="review-body"] span') || 
                   el.querySelector('.review-text-content span');

      // 2. 🎥 Video Review Fallback: 
      // Sometimes text is just in a sibling div or the raw innerText of the body
      if (!textEl) {
          textEl = el.querySelector('.video-block .a-size-base') || 
                   el.querySelector('.review-text-sub-content');
      }

      // 3. Last Resort: Use the raw text, but clean it up
      let fullText = "";
      if (textEl) {
          fullText = textEl.innerText.trim();
      } else {
          // Clone node to safely remove junk (buttons, dates) without breaking UI
          const clone = el.cloneNode(true);
          clone.querySelectorAll('button, .review-date, .review-title, .a-icon-alt').forEach(n => n.remove());
          fullText = clone.innerText.trim();
      }

      // Clean up common Amazon noise
      fullText = fullText.replace(/Read more/g, '').replace(/Helpful/g, '').replace(/Report/g, '').trim();
      
      // Final Validity Check
      if (fullText.length > 15) { 
          reviews.push({ text: fullText, node: el, isVerified: isVerified });
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

  // --- 3. BADGE LOGIC (Hybrid System) ---
  function makeBadge(label, confidence, isVerified) {
    const span = document.createElement('span');
    span.className = 'reviewguard-badge';
    span.style.cssText = 'display:inline-block;padding:2px 6px;margin-left:8px;border-radius:4px;font-weight:600;font-size:12px;color:white;vertical-align:middle;';
    
    // HYBRID LOGIC: If AI says FAKE but Amazon says VERIFIED -> Downgrade to "SUSPICIOUS"
    let finalLabel = label;
    let color = '#f57c00'; // Default Orange

    if (label === 'FAKE') {
        if (isVerified) {
            finalLabel = 'SUSPICIOUS'; // Soften the blow
            color = '#ff9800'; // Darker Orange
        } else {
            color = '#e53935'; // Red
        }
    } else if (label === 'GENUINE') {
        color = '#43a047'; // Green
    }

    if (label === 'ERR') {
        color = '#777';
        span.textContent = 'Error';
    } else {
        const dispConf = Math.min(confidence, 0.99) * 100;
        span.textContent = `${finalLabel} (${Math.round(dispConf)}%)`;
    }
    
    span.style.background = color;
    return { span, finalLabel };
  }

  // --- 4. UI ANNOTATION ---
  async function annotateReview(r) {
    const res = r.result;
    
    // Create Wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'reviewguard-wrapper';
    wrapper.style.cssText = 'margin-top:5px; margin-bottom:5px; display:flex; align-items:center; gap:10px;';

    // Create Badge
    const { span, finalLabel } = makeBadge(res.label, res.confidence ?? 0, r.isVerified);
    wrapper.appendChild(span);

    // Create "Why?" Button
    if (res.label !== 'ERR') {
        const btn = document.createElement('button');
        btn.textContent = '💡 Why?';
        btn.style.cssText = 'border:1px solid #ccc; background:#fff; cursor:pointer; font-size:11px; padding:2px 8px; border-radius:10px; color:#333;';
        
        // Expansion Box
        const explainBox = document.createElement('div');
        explainBox.style.cssText = 'display:none; margin-top:5px; font-size:13px; color:#333; background:#f0f2f5; padding:8px; border-radius:4px; width:100%;';
        
        btn.onclick = (e) => {
            e.preventDefault();
            btn.style.display = 'none'; // Hide button
            explainBox.style.display = 'block'; // Show box
            // Pass the ORIGINAL label to the AI, not the "Suspicious" one, so it knows context
            fetchExplanation(r.text, res.label, res.confidence, explainBox);
        };
        
        wrapper.appendChild(btn);
        
        // Insert Wrapper first, then ExplainBox below it
        const header = r.node.querySelector('.a-profile') || r.node.querySelector('.review-header') || r.node.querySelector('.a-row');
        if (header) {
            header.insertAdjacentElement('afterend', wrapper);
            wrapper.insertAdjacentElement('afterend', explainBox);
        } else {
            r.node.prepend(wrapper);
            wrapper.insertAdjacentElement('afterend', explainBox);
        }
    } else {
        // Fallback insertion
        r.node.prepend(wrapper);
    }
  }

  // --- 5. MAIN LOGIC (Queue System) ---
  let processing = false;

  async function processQueue() {
      if (processing) return;
      processing = true;

      const reviews = extractReviews();
      if (reviews.length > 0) {
          console.log(`[ReviewGuard] Processing ${reviews.length} new reviews...`);
          
          for (const r of reviews) {
              // 20ms delay to keep UI smooth
              await new Promise(res => setTimeout(res, 20)); 
              const result = await analyzeReviewText(r.text);
              r.result = result;
              await annotateReview(r);
          }
      }
      processing = false;
  }

  // --- 6. AUTO-OBSERVER (The Magic) ---
  const observer = new MutationObserver((mutations) => {
      let shouldProcess = false;
      mutations.forEach(m => {
          if (m.addedNodes.length) shouldProcess = true;
      });
      if (shouldProcess) processQueue();
  });

  observer.observe(document.body, { childList: true, subtree: true });
  
  // Initial Run
  setTimeout(processQueue, 1500);

  // Manual Trigger
  window.ReviewGuard = { processQueue };

})();