document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Select Elements
    const analyzeBtn = document.getElementById('analyzeBtn');
    const reviewInput = document.getElementById('reviewInput');
    const resultContainer = document.getElementById('resultContainer');
    const labelBadge = document.getElementById('labelBadge');
    const explainBtn = document.getElementById('explainBtn');
    const explanationBox = document.getElementById('explanationBox');
    const explanationText = document.getElementById('explanationText');

    // Store state
    let currentResult = null;

    // 2. ANALYZE FUNCTION
    analyzeBtn.addEventListener('click', async () => {
        const text = reviewInput.value.trim();
        if (!text) {
            alert("Please paste some review text first.");
            return;
        }

        // UI Updates: Show loading
        analyzeBtn.textContent = "Analyzing...";
        analyzeBtn.disabled = true;
        resultContainer.classList.add('hidden');
        explainBtn.classList.add('hidden');
        explanationBox.classList.add('hidden');

        try {
            // Call Backend
            const response = await fetch('http://127.0.0.1:8000/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();
            currentResult = data; // Save for XAI

            // Show Result
            resultContainer.classList.remove('hidden');
            
            // Set Badge Color & Text
            labelBadge.textContent = `${data.label} (${Math.round(data.confidence * 100)}%)`;
            labelBadge.className = ""; // Reset classes
            
            if (data.label === 'FAKE') {
                labelBadge.classList.add('fake');
            } else if (data.label === 'GENUINE') {
                labelBadge.classList.add('genuine');
            } else {
                labelBadge.classList.add('uncertain');
            }

            // Show "Why?" button if successful
            explainBtn.classList.remove('hidden');
            explainBtn.textContent = "💡 Why?";
            explainBtn.disabled = false;

        } catch (error) {
            console.error(error);
            labelBadge.textContent = "Error connecting to server";
            labelBadge.className = "uncertain"; // Orange fallback
            resultContainer.classList.remove('hidden');
        } finally {
            analyzeBtn.textContent = "Analyze Text";
            analyzeBtn.disabled = false;
        }
    });

    // 3. EXPLAIN FUNCTION (XAI)
    explainBtn.addEventListener('click', async () => {
        if (!currentResult) return;

        // UI Updates
        explainBtn.textContent = "Analyzing Context...";
        explainBtn.disabled = true;

        try {
            const response = await fetch('http://127.0.0.1:8000/explain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: reviewInput.value.trim(),
                    label: currentResult.label,
                    confidence: currentResult.confidence
                })
            });

            const data = await response.json();

            // Show Explanation
            explanationBox.classList.remove('hidden');
            explanationText.textContent = data.explanation || "No explanation returned.";

        } catch (error) {
            console.error(error);
            explanationText.textContent = "Could not fetch explanation.";
            explanationBox.classList.remove('hidden');
        } finally {
            explainBtn.textContent = "💡 Why?";
            explainBtn.disabled = false;
        }
    });
});