(function($) {
"use strict";
   jQuery(document).ready(function(){

      //Category accordion 
      $('.widget_product_categories  ul.product-categories > li:has(ul)').addClass("has-sub");
      $('.widget_product_categories  ul.product-categories > li:has(ul) > a').after('<span class="cat-caret"></span>');
        $('.widget_product_categories  ul.product-categories > li .cat-caret').click(function() {
          var checkElement = $(this).next();
          
          $('.widget_product_categories  ul.product-categories li').removeClass('active');
          $(this).closest('li').addClass('active'); 
          
          if((checkElement.is('ul')) && (checkElement.is(':visible'))) {
            $(this).closest('li').removeClass('active');
            checkElement.slideUp('normal');
          }
          
          if((checkElement.is('ul')) && (!checkElement.is(':visible'))) {
            $('.widget_product_categories ul.product-categories ul:visible').slideUp('normal');
            checkElement.slideDown('normal');
          }
          
          if (checkElement.is('ul')) {
            return false;
          } else {
            return true;  
          }   
        });
   });

  jQuery(document).on('click', '.qty-plus', function(e) {
    e.preventDefault();
    var quantityInput = jQuery(this).parents('.quantity').find('input.qty'),
      step = parseInt(quantityInput.attr('step'), 10),
      newValue = parseInt(quantityInput.val(), 10) + step,
      maxValue = parseInt(quantityInput.attr('max'), 10);

    if (!maxValue) {
      maxValue = 9999999999;
    }

    if ( newValue <= maxValue ) {
      quantityInput.val(newValue);
      quantityInput.change();
    }
  });

  // Decrease
  jQuery(document).on('click', '.qty-minus', function(e) {
    e.preventDefault();
    var quantityInput = jQuery(this).parents('.quantity').find('input.qty'),
      step = parseInt(quantityInput.attr('step'), 10),
      newValue = parseInt(quantityInput.val(), 10) - step,
      minValue = parseInt(quantityInput.attr('min'), 10);

    if (!minValue) {
      minValue = 1;
    }

    if ( newValue >= minValue ) {
      quantityInput.val(newValue);
      quantityInput.change();
    }
  });
})(jQuery);