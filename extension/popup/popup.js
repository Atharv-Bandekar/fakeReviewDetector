document.getElementById('analyze').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      func: () => { document.getElementById('reviewguard-analyze-all')?.click(); }
    });
  });
});

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('analyze').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        func: () => {
          document.getElementById('reviewguard-analyze-all')?.click();
        }
      });
    });
  });
});

