// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
  // PDF.js configuration
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

  const canvas = document.getElementById('pdf-canvas');
  const ctx = canvas.getContext('2d');
  const linkLayer = document.getElementById('link-layer');
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');

  let pdfDoc = null;
  let currentPage = 1;
  let pageRendering = false;
  let pageNumPending = null;
  const scale = 1.0;

  /**
   * Load a new PDF
   */
  function loadPDF(pdfPath) {
    const baseUrl = canvas.getAttribute('data-pdf-base-url');
    const pdfUrl = baseUrl + pdfPath;

    console.log('Loading PDF:', pdfUrl);

    pdfjsLib.getDocument(pdfUrl).promise.then(function(pdf) {
      pdfDoc = pdf;
      currentPage = 1;
      renderPage(currentPage);
    }).catch(function(error) {
      console.error('Error loading PDF:', error);
    });
  }

  /**
   * Render a specific page
   */
  function renderPage(num) {
    pageRendering = true;

    pdfDoc.getPage(num).then(function(page) {
      // Calculate the scale based on available width in pdf-content
      const pdfContent = document.querySelector('.pdf-content');
      const availableWidth = pdfContent.offsetWidth - 120 - 20; // minus nav buttons and padding
      const viewport = page.getViewport({scale: 1.0});
      const scaleToFit = (availableWidth / viewport.width) * 0.73; // 75% of available width
      const scaledViewport = page.getViewport({scale: scaleToFit});

      console.log('Available width:', availableWidth);
      console.log('PDF viewport width:', viewport.width);
      console.log('Scale to fit:', scaleToFit);
      console.log('Scaled viewport:', scaledViewport.width, 'x', scaledViewport.height);

      canvas.height = scaledViewport.height;
      canvas.width = scaledViewport.width;

      // Clear link layer and set exact size
      linkLayer.innerHTML = '';
      linkLayer.style.width = scaledViewport.width + 'px';
      linkLayer.style.height = scaledViewport.height + 'px';

      const renderContext = {
        canvasContext: ctx,
        viewport: scaledViewport
      };

      const renderTask = page.render(renderContext);

      renderTask.promise.then(function() {
        pageRendering = false;
        if (pageNumPending !== null) {
          renderPage(pageNumPending);
          pageNumPending = null;
        }

        // Render links
        return page.getAnnotations();
      }).then(function(annotations) {

        annotations.forEach(function(annotation) {
          if (annotation.subtype === 'Link') {
            console.log('Link annotation:', annotation);

            const rect = scaledViewport.convertToViewportRectangle(annotation.rect);
            const link = document.createElement('a');

            // Handle external links
            if (annotation.url) {
              link.href = annotation.url;
              link.target = '_blank';
              console.log('External link:', annotation.url);
            }
            // Handle internal links
            else if (annotation.dest) {
              link.href = '#';
              link.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Internal link clicked:', annotation.dest);
                handleInternalLink(annotation.dest);
              });
              console.log('Internal link:', annotation.dest);
            }
            // Handle action-based links
            else if (annotation.action) {
              link.href = '#';
              link.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Action link clicked:', annotation.action);
                if (annotation.action.includes('GoTo')) {
                  handleInternalLink(annotation.action);
                }
              });
            }

            // Use pixel coordinates - link layer is same size as canvas
            const x = Math.min(rect[0], rect[2]);
            const y = Math.min(rect[1], rect[3]);
            const width = Math.abs(rect[2] - rect[0]);
            const height = Math.abs(rect[3] - rect[1]);

            link.style.position = 'absolute';
            link.style.left = x + 'px';
            link.style.top = y + 'px';
            link.style.width = width + 'px';
            link.style.height = height + 'px';
            link.style.cursor = 'pointer';

            console.log('Link position:', x, y, width, height);

            linkLayer.appendChild(link);
          }
        });

        updateButtons();
      });
    });
  }

  /**
   * Handle internal PDF links
   */
  function handleInternalLink(dest) {
    // If dest is already an array (explicit destination), use it directly
    if (Array.isArray(dest)) {
      pdfDoc.getPageIndex(dest[0]).then(function(pageIndex) {
        const targetPage = pageIndex + 1;
        console.log('Navigating to page:', targetPage);
        currentPage = targetPage;
        queueRenderPage(currentPage);
      }).catch(function(error) {
        console.error('Error navigating to page:', error);
      });
    }
    // If dest is a string (named destination), look it up first
    else {
      pdfDoc.getDestination(dest).then(function(destination) {
        if (destination) {
          pdfDoc.getPageIndex(destination[0]).then(function(pageIndex) {
            const targetPage = pageIndex + 1;
            console.log('Navigating to page:', targetPage);
            currentPage = targetPage;
            queueRenderPage(currentPage);
          });
        }
      }).catch(function(error) {
        console.error('Error handling internal link:', error);
      });
    }
  }

  /**
   * Queue page rendering
   */
  function queueRenderPage(num) {
    if (pageRendering) {
      pageNumPending = num;
    } else {
      renderPage(num);
    }
  }

  /**
   * Navigate to previous page
   */
  function onPrevPage() {
    if (currentPage <= 1) {
      return;
    }
    currentPage--;
    queueRenderPage(currentPage);
  }

  /**
   * Navigate to next page
   */
  function onNextPage() {
    if (currentPage >= pdfDoc.numPages) {
      return;
    }
    currentPage++;
    queueRenderPage(currentPage);
  }

  /**
   * Update button states
   */
  function updateButtons() {
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= pdfDoc.numPages;
  }

  // Add event listeners for navigation buttons
  prevBtn.addEventListener('click', onPrevPage);
  nextBtn.addEventListener('click', onNextPage);

  /**
   * Add click handlers for PDF buttons
   */
  document.querySelectorAll('[data-pdf]').forEach(button => {
    button.addEventListener('click', function() {
      const pdfFile = this.getAttribute('data-pdf');
      console.log('Button clicked, loading:', pdfFile);
      loadPDF(pdfFile);
    });
  });

  /**
   * Load default PDF on page load
   */
  loadPDF('Guideline.pdf');

  /**
   * Re-render on window resize to keep links aligned
   */
  let resizeTimeout;
  window.addEventListener('resize', function() {
    if (pdfDoc && !pageRendering) {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(function() {
        renderPage(currentPage);
      }, 250);
    }
  });
});
