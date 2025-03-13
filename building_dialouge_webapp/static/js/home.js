document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#continue-btn').addEventListener('click', redirect);
    document.querySelector('#reset-btn').addEventListener('click', resetSession);
    document.querySelector('#close-btn').addEventListener('click', closeModal);
    document.querySelector('#close-btn-header').addEventListener('click', closeModal);
    
    const openModalBtn = document.querySelector('#open-start-modal-btn');
    if (openModalBtn) {
      openModalBtn.addEventListener('click', checkSession);
    }
    
    function checkSession() {
      const session = JSON.parse(document.getElementById("session").textContent);
      if (!session.flow_data_present) {
        redirect();
        return;
      }
      
      // Show modal
      const modal = document.getElementById('ask_user');
      modal.classList.add('show');
      modal.style.display = 'block';
      document.body.classList.add('modal-open');
      
      // Add backdrop
      const backdrop = document.createElement('div');
      backdrop.className = 'modal-backdrop fade show';
      document.body.appendChild(backdrop);
    }
    
    // Close modal
    function closeModal() {
      const modal = document.getElementById('ask_user');
      modal.classList.remove('show');
      modal.style.display = 'none';
      document.body.classList.remove('modal-open');
      
      // Remove backdrop
      const backdrop = document.querySelector('.modal-backdrop');
      if (backdrop) {
        document.body.removeChild(backdrop);
      }
    }
    
    function redirect() {
      const session = JSON.parse(document.getElementById("session").textContent);
      window.location = session.flow_url;
    }
    
    async function resetSession() {
      await fetch("/reset_session/", {
        method: "GET",
      });
      redirect();
    }
  });