$(document).ready(function(){
  $('.product-image-slider').slick({
    slidesToShow: 1,
    slidesToScroll: 1,
    arrows: false,
    fade: true,
    asNavFor: '.slider-nav-thumbnails'
  });

  $('.slider-nav-thumbnails').slick({
    slidesToShow: 4,
    slidesToScroll: 1,
    asNavFor: '.product-image-slider',
    focusOnSelect: true
  });
});
