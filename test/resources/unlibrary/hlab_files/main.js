(function($) {
  	"use strict";
  	var GaviasTheme = {
		init: function(){
			this.initResponsive();
			this.initCarousel();
			this.menuMobile();
			this.postMasonry();
			this.scrollTop();
			this.stickyMenu();
			this.other();
	
			$('.team__progress-bar').each(function(){
			  	var $progressbar = $(this);
			  	$progressbar.css('width', $progressbar.data('progress-max'));
			})
			$('.review__progress-bar').each(function(){
			  	var $progressbar = $(this);
			  	$progressbar.css('width', $progressbar.data('progress-max'));
			})
		},

	 	initResponsive: function(){
		  	var _event = $.event,
		  	$special, resizeTimeout;
		  	$special = _event.special.debouncedresize = {
				setup: function () {
					$(this).on("resize", $special.handler);
				},
			 	teardown: function () {
					$(this).off("resize", $special.handler);
			 	},
			 	handler: function (event, execAsap) {
					var context = this,
				  		args = arguments,
				  		dispatch = function () {
					 		event.type = "debouncedresize";
					 		_event.dispatch.apply(context, args);
				  		};
				  	if (resizeTimeout) {
					 	clearTimeout(resizeTimeout);
				  	}
					execAsap ? dispatch() : resizeTimeout = setTimeout(dispatch, $special.threshold);
			 	},
		  		threshold: 150
			};
	 	},

	 	initCarousel: function(){
			$('.init-carousel-owl-theme').each(function(){
		  		var items = GaviasTheme.carouselOptInit('items', this);
		  		var items_lg = GaviasTheme.carouselOptInit('items_lg', this);
		  		var items_md = GaviasTheme.carouselOptInit('items_md', this);
		  		var items_sm = GaviasTheme.carouselOptInit('items_sm', this);
		  		var items_xs = GaviasTheme.carouselOptInit('items_xs', this);
		  		var loop = GaviasTheme.carouselOptInit('loop', this);
		  		var speed = GaviasTheme.carouselOptInit('speed', this);
		  		var auto_play = GaviasTheme.carouselOptInit('auto_play', this);
		  		var auto_play_speed = GaviasTheme.carouselOptInit('auto_play_speed', this);
		  		var auto_play_timeout = GaviasTheme.carouselOptInit('auto_play_timeout', this);
		  		var auto_play_hover = GaviasTheme.carouselOptInit('auto_play_hover', this);
		  		var navigation = GaviasTheme.carouselOptInit('navigation', this);
		  		var rewind_nav = GaviasTheme.carouselOptInit('rewind_nav', this);
		  		var pagination = GaviasTheme.carouselOptInit('pagination', this);
		  		var mouse_drag = GaviasTheme.carouselOptInit('mouse_drag', this);
		  		var touch_drag = GaviasTheme.carouselOptInit('touch_drag', this);
		  		$(this).owlCarousel({
			 		nav: navigation,
			 		autoplay: auto_play,
			 		autoplayTimeout: auto_play_timeout,
			 		autoplaySpeed: auto_play_speed,
			 		autoplayHoverPause: auto_play_hover,
			 		navText: [ '<span><i class="fas fa-arrow-left"></i></span>', '<span><i class="fas fa-arrow-right"></i></span>' ],
			 		autoHeight: false,
			 		loop: loop, 
			 		dots: pagination,
			 		rewind: rewind_nav,
			 		smartSpeed: speed,
			 		mouseDrag: mouse_drag,
			 		touchDrag: touch_drag,
			 		responsive : {
						0 : {
						  items: 1,
						  nav: false
						},
						580 : {
						  items : items_xs,
						  nav: false
						},
						768 : {
						  items : items_sm,
						  nav: false
						},
						992: {
						  items : items_md
						},
						1200: {
						  items: items_lg
						},
						1400: {
						  items: items
						}
				 	}
		  		}); 
			}); 
	 	},

	 	carouselOptInit: function(opt, context){
			const opts = {
			  	items: 5, 
			  	items_lg: 4,
			  	items_md: 3, 
			  	items_sm: 2, 
			  	items_xs: 1,
			  	loop: false, 
			  	speed: 200, 
			  	auto_play: false,
			  	auto_play_speed: false,
			  	auto_play_timeout: 1000,
			  	auto_play_hover: false,
			  	navigation: false,
			  	rewind_nav: false,
			  	pagination: false,
			  	mouse_drag: false,
			  	touch_drag: false
				}
			return $(context).data(opt) ? $(context).data(opt) : opts[opt];
	 	},

	 	menuMobile: function(){
			$('.gva-offcanvas-content ul.gva-mobile-menu > li:has(ul)').addClass("has-sub");
			$('.gva-offcanvas-content ul.gva-mobile-menu > li:has(ul) > a').after('<span class="caret"></span>');
			$( document ).on('click', '.gva-offcanvas-content ul.gva-mobile-menu > li > .caret', function(e){
			  	e.preventDefault();
			  	var checkElement = $(this).next();
			  	$('.gva-offcanvas-content ul.gva-mobile-menu > li').removeClass('menu-active');
			  	$(this).closest('li').addClass('menu-active'); 
			  
			  	if((checkElement.is('.submenu-inner')) && (checkElement.is(':visible'))) {
				 	$(this).closest('li').removeClass('menu-active');
				 	checkElement.slideUp('normal');
			  	}
		  
		  		if((checkElement.is('.submenu-inner')) && (!checkElement.is(':visible'))) {
			 		$('.gva-offcanvas-content ul.gva-mobile-menu .submenu-inner:visible').slideUp('normal');
			 		checkElement.slideDown('normal');
		  		}
		  
		  		if (checkElement.is('.submenu-inner')) {
			 		return false;
		  		} else {
			 		return true;  
		  		}   
			})

			$( document ).on( 'click', '.canvas-menu.gva-offcanvas > a.dropdown-toggle', function(e) {
		  		e.preventDefault();
		  		var $style = $(this).data('canvas');
			  	if($('.gva-offcanvas-content' + $style).hasClass('open')){
				 	$('.gva-offcanvas-content' + $style).removeClass('open');
				 	$('#gva-overlay').removeClass('open');
				 	$('#wp-main-content').removeClass('blur');
			  	}else{
				 	$('.gva-offcanvas-content' + $style).addClass('open');
				 	$('#gva-overlay').addClass('open');
				 	$('#wp-main-content').addClass('blur');
			  	}
			});
			$( document ).on( 'click', '#gva-overlay', function(e) {
			  	e.preventDefault();
			  	$(this).removeClass('open');
			  	$('.gva-offcanvas-content').removeClass('open');
			  	$('#wp-main-content').removeClass('blur');
			})
			$( document ).on( 'click', '.close-canvas', function(e) {
			  	e.preventDefault();
			  	$('.gva-offcanvas-content').removeClass('open');
			  	$('#gva-overlay').removeClass('open');
			  	$('#wp-main-content').removeClass('blur');
			})
	 	},

	 	postMasonry: function(){
			var $container = $('.post-masonry-style');
			$container.imagesLoaded( function(){
		  		$container.masonry({
			 		itemSelector : '.item-masory',
			 		gutterWidth: 0,
			 		columnWidth: 1,
		  		}); 
			});
	 	},

		scrollTop: function(){
			var offset = 300;
			var duration = 500;

			jQuery(window).scroll(function() {
			  	if (jQuery(this).scrollTop() > offset) {
				 	jQuery('.return-top').fadeIn(duration);
			  	} else {
				 	jQuery('.return-top').fadeOut(duration);
			  	}
			});

			$( document ).on('click', '.return-top', function(event){
			  	event.preventDefault();
			  	jQuery('html, body').animate({scrollTop: 0}, duration);
			  	return false;
			});
		},

	 	carouselProductThumbnail: function(){
			$('ol.flex-control-nav').each(function(){
			  	$(this).owlCarousel({
				 	nav: false,
				 	navText: [ '<span><i class="fas fa-arrow-left"></i></span>', '<span><i class="fas fa-arrow-right"></i></span>' ],
				 	margin: 10,
				 	dots: false,
				 	responsive : {
						0 : {
						  items: 2,
						  nav: false
						},
						640 : {
						  items : 3,
						  nav: false
						},
						768 : {
						  items : 4,
						  nav: false
						},
						992: {
						  items : 4
						},
						1200: {
						  items: 4
						},
						1400: {
						  items: 4
						}
				 	}
			  	});
			});
	 	},

	 	stickyMenu: function(){
		
			if( $('.gv-sticky-menu').length > 0 ){

				$( ".gv-sticky-menu" ).wrap( "<div class='gv-sticky-wrapper'></div>" );

		      var headerHeight = $('.gv-sticky-menu').height();
		      var menu = $('.gv-sticky-wrapper');

		      $(window).on('scroll', function () {
		         if ($(window).scrollTop() > menu.offset().top) {
		            menu.addClass('is-fixed');
		            $('body').addClass('header-is-fixed');
		            menu.css('height', headerHeight);
		         } else {
		            menu.removeClass('is-fixed');
		            menu.css('height', 'auto');
		            $('body').removeClass('header-is-fixed');
		         }
		      });
		   }
	 	},

		other: function(){
			$('.gva_widget_recent_give .give-block .give__progress-bar, .content-single-give-form .give-progress-information .give__progress-bar').each(function(){
        		var $progressbar = $(this);
        		$progressbar.css('width', $progressbar.data('progress-max'));
      	})

			$('.popup-video').magnificPopup({
			  	type: 'iframe',
			  	fixedContentPos: false
			});

			$( document ).on( 'click', '.yith-wcwl-add-button.show a', function() {
			  $(this).addClass('loading');
			});

			$(document).on('click', '.gva-search > a.control-search', function(){
			  	if($(this).hasClass('search-open')){
				 	$(this).parents('.gva-search').removeClass('open');
				 	$(this).removeClass('search-open');
			  	}else{
				 	$(this).parents('.gva-search').addClass('open');
				 	$(this).addClass('search-open');
			  	}
			});

			$('.gva-offcanvas-content .sidebar, .mini-cart-header .dropdown .minicart-content').perfectScrollbar();

			$('a.tribe-events-button').each(function(e){
			  	if($(this).children().length == 0){
				 	$(this).wrapInner('<span></span>')
			  	}
			});

			$('.scroll-link[href*="#"]:not([href="#"])').click(function() {
		      if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
		        var target = $(this.hash);
		        target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
		        if (target.length) {
		          $('html, body').animate({
		            scrollTop: target.offset().top - 100
		          }, 1500);
		          return false;
		        }
		      }
		   });
		}
	}

  	$(document).ready(function(){
	 	GaviasTheme.init();
  	})

  	$(window).load(function(){
	 	GaviasTheme.carouselProductThumbnail();
  	})

})(jQuery);
