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
            const rect = scaledViewport.convertToViewportRectangle(annotation.rect);
            const link = document.createElement('a');

            // Handle external links
            if (annotation.url) {
              link.href = annotation.url;
              link.target = '_blank';
            }
            // Handle internal links
            else if (annotation.dest) {
              link.href = '#';
              link.addEventListener('click', function(e) {
                e.preventDefault();
                handleInternalLink(annotation.dest);
              });
            }
            // Handle action-based links
            else if (annotation.action) {
              link.href = '#';
              link.addEventListener('click', function(e) {
                e.preventDefault();
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

  // ========================================
  // MODAL FULLSCREEN PDF VIEWER
  // ========================================

  const modal = document.getElementById('pdf-modal');
  const modalCanvas = document.getElementById('modal-pdf-canvas');
  const modalCtx = modalCanvas.getContext('2d');
  const modalLinkLayer = document.getElementById('modal-link-layer');
  const fullscreenBtn = document.getElementById('fullscreen-btn');
  const modalCloseBtn = document.getElementById('modal-close');
  const modalZoomInBtn = document.getElementById('modal-zoom-in');
  const modalZoomOutBtn = document.getElementById('modal-zoom-out');
  const modalZoomFitBtn = document.getElementById('modal-zoom-fit');
  const modalZoomLevel = document.getElementById('modal-zoom-level');
  const modalPrevBtn = document.getElementById('modal-prev-page');
  const modalNextBtn = document.getElementById('modal-next-page');
  const modalPageInfo = document.getElementById('modal-page-info');
  const modalPdfContainer = document.getElementById('modal-pdf-container');

  let modalPdfDoc = null;
  let modalCurrentPage = 1;
  let modalPageRendering = false;
  let modalPageNumPending = null;
  let modalScale = 1.5;
  let modalIsPanning = false;
  let modalPanStart = { x: 0, y: 0 };
  let modalScrollStart = { x: 0, y: 0 };

  /**
   * Open modal with current PDF
   */
  function openModal() {
    if (!pdfDoc) return;

    modalPdfDoc = pdfDoc;
    modalCurrentPage = currentPage;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    renderModalPage(modalCurrentPage);
  }

  /**
   * Close modal
   */
  function closeModal() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }

  /**
   * Render page in modal
   */
  function renderModalPage(num) {
    modalPageRendering = true;

    modalPdfDoc.getPage(num).then(function(page) {
      const viewport = page.getViewport({scale: modalScale});

      modalCanvas.height = viewport.height;
      modalCanvas.width = viewport.width;

      // Update link layer size
      modalLinkLayer.innerHTML = '';
      modalLinkLayer.style.width = viewport.width + 'px';
      modalLinkLayer.style.height = viewport.height + 'px';

      const renderContext = {
        canvasContext: modalCtx,
        viewport: viewport
      };

      const renderTask = page.render(renderContext);

      renderTask.promise.then(function() {
        modalPageRendering = false;
        if (modalPageNumPending !== null) {
          renderModalPage(modalPageNumPending);
          modalPageNumPending = null;
        }

        // Render links
        return page.getAnnotations();
      }).then(function(annotations) {
        annotations.forEach(function(annotation) {
          if (annotation.subtype === 'Link') {
            const viewport = page.getViewport({scale: modalScale});
            const rect = viewport.convertToViewportRectangle(annotation.rect);
            const link = document.createElement('a');

            // Handle external links
            if (annotation.url) {
              link.href = annotation.url;
              link.target = '_blank';
            }
            // Handle internal links
            else if (annotation.dest) {
              link.href = '#';
              link.addEventListener('click', function(e) {
                e.preventDefault();
                handleModalInternalLink(annotation.dest);
              });
            }
            // Handle action-based links
            else if (annotation.action) {
              link.href = '#';
              link.addEventListener('click', function(e) {
                e.preventDefault();
                if (annotation.action.includes('GoTo')) {
                  handleModalInternalLink(annotation.action);
                }
              });
            }

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

            modalLinkLayer.appendChild(link);
          }
        });

        updateModalControls();
      });
    });
  }

  /**
   * Handle internal PDF links in modal
   */
  function handleModalInternalLink(dest) {
    if (Array.isArray(dest)) {
      modalPdfDoc.getPageIndex(dest[0]).then(function(pageIndex) {
        const targetPage = pageIndex + 1;
        modalCurrentPage = targetPage;
        queueRenderModalPage(modalCurrentPage);
      }).catch(function(error) {
        console.error('Error navigating to page:', error);
      });
    } else {
      modalPdfDoc.getDestination(dest).then(function(destination) {
        if (destination) {
          modalPdfDoc.getPageIndex(destination[0]).then(function(pageIndex) {
            const targetPage = pageIndex + 1;
            modalCurrentPage = targetPage;
            queueRenderModalPage(modalCurrentPage);
          });
        }
      }).catch(function(error) {
        console.error('Error handling internal link:', error);
      });
    }
  }

  /**
   * Queue page rendering in modal
   */
  function queueRenderModalPage(num) {
    if (modalPageRendering) {
      modalPageNumPending = num;
    } else {
      renderModalPage(num);
    }
  }

  /**
   * Update modal controls
   */
  function updateModalControls() {
    modalPrevBtn.disabled = modalCurrentPage <= 1;
    modalNextBtn.disabled = modalCurrentPage >= modalPdfDoc.numPages;
    modalPageInfo.textContent = `Seite ${modalCurrentPage} von ${modalPdfDoc.numPages}`;
    modalZoomLevel.textContent = Math.round(modalScale * 100) + '%';
  }

  /**
   * Zoom in
   */
  function modalZoomIn() {
    modalScale = Math.min(modalScale + 0.25, 5.0);
    renderModalPage(modalCurrentPage);
  }

  /**
   * Zoom out
   */
  function modalZoomOut() {
    modalScale = Math.max(modalScale - 0.25, 0.5);
    renderModalPage(modalCurrentPage);
  }

  /**
   * Fit to width
   */
  function modalZoomFit() {
    if (!modalPdfDoc) return;

    modalPdfDoc.getPage(modalCurrentPage).then(function(page) {
      const modalBody = document.querySelector('.pdf-modal-body');
      const availableWidth = modalBody.clientWidth - 40; // minus padding
      const viewport = page.getViewport({scale: 1.0});
      modalScale = availableWidth / viewport.width;
      renderModalPage(modalCurrentPage);
    });
  }

  /**
   * Navigate to previous page in modal
   */
  function modalOnPrevPage() {
    if (modalCurrentPage <= 1) return;
    modalCurrentPage--;
    queueRenderModalPage(modalCurrentPage);
  }

  /**
   * Navigate to next page in modal
   */
  function modalOnNextPage() {
    if (modalCurrentPage >= modalPdfDoc.numPages) return;
    modalCurrentPage++;
    queueRenderModalPage(modalCurrentPage);
  }

  // Pan/drag functionality
  modalPdfContainer.addEventListener('mousedown', function(e) {
    if (modalScale > 1.0) {
      modalIsPanning = true;
      modalPdfContainer.classList.add('dragging');
      modalPanStart = { x: e.clientX, y: e.clientY };
      const modalBody = document.querySelector('.pdf-modal-body');
      modalScrollStart = { x: modalBody.scrollLeft, y: modalBody.scrollTop };
      e.preventDefault();
    }
  });

  document.addEventListener('mousemove', function(e) {
    if (modalIsPanning) {
      const modalBody = document.querySelector('.pdf-modal-body');
      const dx = e.clientX - modalPanStart.x;
      const dy = e.clientY - modalPanStart.y;
      modalBody.scrollLeft = modalScrollStart.x - dx;
      modalBody.scrollTop = modalScrollStart.y - dy;
    }
  });

  document.addEventListener('mouseup', function() {
    if (modalIsPanning) {
      modalIsPanning = false;
      modalPdfContainer.classList.remove('dragging');
    }
  });

  // Event listeners
  fullscreenBtn.addEventListener('click', openModal);
  modalCloseBtn.addEventListener('click', closeModal);
  modalZoomInBtn.addEventListener('click', modalZoomIn);
  modalZoomOutBtn.addEventListener('click', modalZoomOut);
  modalZoomFitBtn.addEventListener('click', modalZoomFit);
  modalPrevBtn.addEventListener('click', modalOnPrevPage);
  modalNextBtn.addEventListener('click', modalOnNextPage);

  // Close modal on background click
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeModal();
    }
  });

  // Close modal on ESC key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      closeModal();
    }
  });
});
