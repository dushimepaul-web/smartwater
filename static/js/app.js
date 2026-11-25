// Menu mobile
document.querySelector('.burger')?.addEventListener('click',()=>document.querySelector('.sidebar').classList.toggle('open'));
// Onglets (page paramètres)
document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.tabs button,.pane').forEach(e=>e.classList.remove('on'));
  b.classList.add('on');document.getElementById(b.dataset.pane).classList.add('on');}));
// Modales (ajout appareil)
document.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>document.getElementById(b.dataset.open).classList.add('open')));
document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();b.closest('.modal').classList.remove('open')}));
// Afficher / masquer le mot de passe
document.querySelectorAll('.field button').forEach(btn => {
  btn.addEventListener('click', e => {
    e.preventDefault();
    const input = btn.parentElement.querySelector('input[type="password"], input[type="text"]');
    if (input) {
      input.type = input.type === 'password' ? 'text' : 'password';
    }
  });
});
