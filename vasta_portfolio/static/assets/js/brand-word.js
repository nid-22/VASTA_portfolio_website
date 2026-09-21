(() => {
  'use strict';
  // Removing this file and its two script tags restores the original text.
  const excluded = 'script, style, noscript, textarea, option, .wordmark, .legacy-wordmark, .brand-word, .brand-name, a[href*="instagram.com"]';
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const textNodes = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    const parent = node.parentElement;
    if (parent && !parent.closest(excluded) && /\bvast\b/i.test(node.nodeValue)) textNodes.push(node);
  }
  textNodes.forEach(node => {
    const fragment = document.createDocumentFragment();
    const expression = /\bvast(?:\s+architects)?\b/gi;
    let cursor = 0;
    let match;
    while ((match = expression.exec(node.nodeValue)) !== null) {
      fragment.append(node.nodeValue.slice(cursor, match.index));
      const styledWord = document.createElement('span');
      const isStudioName = /\s+architects/i.test(match[0]);
      styledWord.className = isStudioName ? 'brand-name' : 'brand-word';
      styledWord.textContent = isStudioName ? 'vast architects' : 'vast';
      fragment.append(styledWord);
      cursor = match.index + match[0].length;
    }
    fragment.append(node.nodeValue.slice(cursor));
    node.replaceWith(fragment);
  });
})();
