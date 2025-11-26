// static/js/app.js - Versión mejorada
document.addEventListener('DOMContentLoaded', function() {
    // Detectar estado de conexión
    function updateOnlineStatus() {
      if (!navigator.onLine) {
        document.body.classList.add('offline');
        showOfflineNotification();
      } else {
        document.body.classList.remove('offline');
      }
    }
  
    function showOfflineNotification() {
      // Solo mostrar una notificación si no existe ya
      if (document.getElementById('offline-notification')) return;
      
      const notification = document.createElement('div');
      notification.id = 'offline-notification';
      notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #ffc107;
        color: #000;
        padding: 10px 15px;
        border-radius: 5px;
        z-index: 1000;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
      `;
      notification.innerHTML = `
        <div style="display: flex; align-items: center;">
          <span style="margin-right: 10px;">📶 Modo offline</span>
          <button onclick="this.parentElement.parentElement.remove()" 
                  style="background: none; border: none; font-size: 16px; cursor: pointer;">×</button>
        </div>
      `;
      
      document.body.appendChild(notification);
      
      // Auto-eliminar después de 5 segundos
      setTimeout(() => {
        if (notification.parentElement) {
          notification.remove();
        }
      }, 5000);
    }
  
    // Configurar listeners de conexión
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    
    // Verificar estado inicial
    updateOnlineStatus();
  
    // Validación de formularios básica
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
      form.addEventListener('submit', function(e) {
        const inputs = this.querySelectorAll('input[required]');
        let isValid = true;
        
        inputs.forEach(input => {
          if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = '#dc3545';
          } else {
            input.style.borderColor = '';
          }
        });
        
        if (!isValid) {
          e.preventDefault();
          alert('Por favor completa todos los campos requeridos');
        }
      });
    });
  
    // Función para copiar códigos offline
    window.copyOfflineCode = function() {
      const codeElement = document.getElementById('offlineCode');
      if (codeElement) {
        navigator.clipboard.writeText(codeElement.textContent)
          .then(() => alert('Código copiado al portapapeles'))
          .catch(() => alert('No se pudo copiar el código'));
      }
    };
  });