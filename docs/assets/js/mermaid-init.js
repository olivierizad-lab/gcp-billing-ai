document.addEventListener('DOMContentLoaded', function () {
  if (typeof mermaid === 'undefined') {
    console.warn('Mermaid library not loaded');
    return;
  }

  const mermaidBlocks = document.querySelectorAll('pre code.language-mermaid');
  mermaidBlocks.forEach((block) => {
    const parent = block.parentElement;
    const container = document.createElement('div');
    container.classList.add('mermaid');
    container.innerHTML = block.textContent;
    parent.replaceWith(container);
  });

  if (mermaidBlocks.length > 0) {
    mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
    mermaid.run({ nodes: document.querySelectorAll('.mermaid') });
  }
});

