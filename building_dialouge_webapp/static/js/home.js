// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
  // PDF.js configuration
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

  let pdfDoc = null;
  let pageNum = 1;
  let pageRendering = false;
  let pageNumPending = null;
  const scale = 1.0;
  const canvas = document.getElementById('pdf-canvas');
  const ctx = canvas.getContext('2d');
  const textLayerDiv = document.getElementById('text-layer');

  // Set initial canvas size
  canvas.width = 800;
  canvas.height = 600;

  // Draw initial placeholder
  ctx.fillStyle = '#999';
  ctx.font = '20px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('PDF wird geladen...', canvas.width / 2, canvas.height / 2);

  /**
   * Load a new PDF
   */
  function loadPDF(pdfPath) {
    // Get the base URL from the data attribute on the canvas element
    const baseUrl = canvas.getAttribute('data-pdf-base-url');
    const currentPdfUrl = baseUrl + pdfPath;
    pageNum = 1;

    console.log('Loading PDF:', currentPdfUrl);

    pdfjsLib.getDocument(currentPdfUrl).promise.then(function(pdfDoc_) {
      pdfDoc = pdfDoc_;
      renderPage(pageNum);
      updateButtons();
    }).catch(function(error) {
      console.error('Error loading PDF:', error);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#999';
      ctx.font = '20px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('PDF konnte nicht geladen werden', canvas.width / 2, canvas.height / 2);
      ctx.fillText(pdfPath, canvas.width / 2, canvas.height / 2 + 30);
    });
  }

  /**
   * Render the page
   */
  function renderPage(num) {
    pageRendering = true;
    pdfDoc.getPage(num).then(function(page) {
      const viewport = page.getViewport({scale: scale});
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      // Clear text layer
      textLayerDiv.innerHTML = '';
      textLayerDiv.style.width = canvas.width + 'px';
      textLayerDiv.style.height = canvas.height + 'px';

      const renderContext = {
        canvasContext: ctx,
        viewport: viewport
      };

      const renderTask = page.render(renderContext);
      renderTask.promise.then(function() {
        // Render text layer for links
        return Promise.all([
          page.getTextContent(),
          page.getAnnotations()
        ]).then(function([textContent, annotations]) {
          // Render text layer
          pdfjsLib.renderTextLayer({
            textContentSource: textContent,
            container: textLayerDiv,
            viewport: viewport,
            textDivs: []
          });

          // Render annotations (links)
          annotations.forEach(function(annotation) {
            if (annotation.subtype === 'Link' && annotation.url) {
              const rect = viewport.convertToViewportRectangle(annotation.rect);
              const link = document.createElement('a');
              link.href = annotation.url;
              link.target = '_blank';
              link.style.position = 'absolute';
              link.style.left = Math.min(rect[0], rect[2]) + 'px';
              link.style.top = Math.min(rect[1], rect[3]) + 'px';
              link.style.width = Math.abs(rect[2] - rect[0]) + 'px';
              link.style.height = Math.abs(rect[3] - rect[1]) + 'px';
              link.style.cursor = 'pointer';
              textLayerDiv.appendChild(link);
            }
          });
        });
      }).then(function() {
        pageRendering = false;
        if (pageNumPending !== null) {
          renderPage(pageNumPending);
          pageNumPending = null;
        }
      });
    });
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
   * Show previous page
   */
  function onPrevPage() {
    if (pageNum <= 1) {
      return;
    }
    pageNum--;
    queueRenderPage(pageNum);
    updateButtons();
  }

  /**
   * Show next page
   */
  function onNextPage() {
    if (pageNum >= pdfDoc.numPages) {
      return;
    }
    pageNum++;
    queueRenderPage(pageNum);
    updateButtons();
  }

  /**
   * Update button states
   */
  function updateButtons() {
    document.getElementById('prev-page').disabled = pageNum <= 1;
    document.getElementById('next-page').disabled = pageNum >= pdfDoc.numPages;
  }

  // Add event listeners
  document.getElementById('prev-page').addEventListener('click', onPrevPage);
  document.getElementById('next-page').addEventListener('click', onNextPage);

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
});
