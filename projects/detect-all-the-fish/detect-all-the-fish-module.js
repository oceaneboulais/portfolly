// detect-all-the-fish-module.js
// Module to display and interact with the cluster.jpg image for fish detection demo

export function renderFishClusterModule(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Clear container
  container.innerHTML = '';

  // Create image element
  const img = document.createElement('img');
  img.src = './imgs/cluster.jpg';
  img.alt = 'Fish Cluster';
  img.className = 'project-image';
  img.style.cursor = 'zoom-in';

  // Optional: Add click-to-zoom functionality
  img.addEventListener('click', () => {
    if (img.style.maxWidth === '100%') {
      img.style.maxWidth = 'none';
      img.style.width = 'auto';
      img.style.cursor = 'zoom-out';
    } else {
      img.style.maxWidth = '100%';
      img.style.width = '';
      img.style.cursor = 'zoom-in';
    }
  });

  // Caption
  const caption = document.createElement('div');
  caption.textContent = 'Detected fish clusters in sample image.';
  caption.style.margin = '12px 0 0 0';
  caption.style.fontSize = '15px';
  caption.style.color = '#555';

  container.appendChild(img);
  container.appendChild(caption);
}
