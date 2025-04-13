// Registro del Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/serviceWorker.js')
      .then(registration => {
        console.log('Service Worker registrado con éxito:', registration.scope);
      })
      .catch(error => {
        console.log('Error al registrar el Service Worker:', error);
      });
  });
}

// Código para mostrar el banner de instalación en dispositivos móviles
let deferredPrompt;
const addBtn = document.querySelector('.add-button');

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevenir que Chrome muestre la mini-infobar
  e.preventDefault();
  // Guardar el evento para poder activarlo más tarde
  deferredPrompt = e;
  // Mostrar nuestro botón personalizado de instalación
  if (addBtn) {
    addBtn.style.display = 'block';
  }
});

// Evento para el botón de instalación
if (addBtn) {
  addBtn.addEventListener('click', (e) => {
    // Ocultar nuestro botón
    addBtn.style.display = 'none';
    // Mostrar el prompt de instalación
    deferredPrompt.prompt();
    // Esperar a que el usuario responda
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('Usuario aceptó la instalación');
      } else {
        console.log('Usuario rechazó la instalación');
      }
      deferredPrompt = null;
    });
  });
} 