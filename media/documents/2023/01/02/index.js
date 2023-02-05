$(function () {
    $(document).scroll(function () {
      var $nav = $("nav");
      $nav.toggleClass('fixed-top', $(document).scrollTop() > 70);
    });
});

const hamburger = document.querySelector('#btnHamburger');
const menu = document.querySelector('.navbar-menu');

hamburger.addEventListener('click', () => {
    if(menu.classList.contains('open')){
      menu.classList.remove('open');
    }
    else {
      menu.classList.add('open')
    }
});
