
(function($) {
  	"use strict";
  	var addonAjaxForm = {
	 	init: function(){
	 		this.ajaxLogin();
	 		this.ajaxLostPassword();
	 		this.ajaxRegistration();
	 		this.ajaxChangePassword();
	 		this.ajaxChangeUserInfo();
	 		this.ajaxWishlist();
	 		this.ajaxLoadPackage();
	 		this.ajaxApplyPackage();
	 		this.popup();
	 	},

	 	ajaxLogin: function(){

			$('form#ajax-login-form').on('submit', function(e){
				var form = $(this);
				var form_name = 'form#ajax-login-form';
				$(form_name).addClass('ajax-preload');
				$.ajax({
					type: 'POST',
					dataType: 'json',
					url: form_ajax_object.ajaxurl,
					data: { 
						'action': 'ajaxlogin',
						'username': $(form_name + ' #username').val(), 
						'password': $(form_name + ' #password').val(), 
						'security': form_ajax_object.security_nonce
					},
					success: function(data){
					 	$('.form-status', form).show().html(data.message);
					 	if (data.logged_in == true){
						  document.location.href = form_ajax_object.redirecturl;
					 	}
					 	$(form_name).removeClass('ajax-preload');
					},
					error: function(data) {
						$(form).removeClass('ajax-preload');
	          	}
		  		});
		  		e.preventDefault();
			});
		},

		ajaxLostPassword: function(){

			$('form#lost-password-form').on('submit', function(e){
				var form = $(this);
				var form_name = 'form#lost-password-form';
				$(form_name).addClass('ajax-preload');
				$.ajax({
					type: 'POST',
					dataType: 'json',
					url: form_ajax_object.ajaxurl,
					data: { 
						'action': 'halpes_lost_password', 
						'user_login': $('#forget_pwd_user_login').val(), 
						'security': form_ajax_object.security_nonce
					},
					success: function(data){                    
						$('.form-status', form).show().html(data.message);  
						$(form_name).removeClass('ajax-preload');       
					},
					error: function(data) {
						$(form).removeClass('ajax-preload');
	          	}
			  	});
				e.preventDefault();
				return false;
			});
			
		},

		ajaxChangePassword: function(){

			$('form#change_password').on('submit', function(e){
				var form = $(this);
				$(form).addClass('ajax-preload');
				$.ajax({
					type: 'POST',
					dataType: 'json',
					url: form_ajax_object.ajaxurl,
					data: { 
						'action': 'halpes_change_password', 
						'old_password': $('#old_password').val(), 
						'new_password': $('#new_password').val(), 
						're_password': $('#re_password').val(),
						'security': form_ajax_object.security_nonce
					},
					success: function(data){                    
						$('.form-status', form).show().html(data.message);       
						$(form).removeClass('ajax-preload');  
					},
					error: function(data) {
						$(form).removeClass('ajax-preload');
	          	}
			  	});
				e.preventDefault();
				$(form).removeClass('ajax-preload');
				return false;
			});
		 
			// Client side form validation
			if($('#forgot_password').length){
				//$('#forgot_password').validate();
			}
		},

		ajaxRegistration: function(){

			$('form#ajax-register-user').on('submit', function(e){
				
				var form = $(this);
				var form_name = 'form#ajax-register-user';
				$(form).addClass('ajax-preload');

	        	var user_name = $('#register-username').val();
	        	var user_email = $('#register-useremail').val();
	        	var user_password = $('#register-userpassword').val();
	        	var re_user_password = $('#register-re-pwd').val();
	        	$.ajax({
	        		type: 'POST',
	          	dataType: 'json',
	          	url: form_ajax_object.ajaxurl,
	          	data: {
	            	'action': "register_user_frontend",
	            	'user_name': user_name,
	            	'user_email': user_email,
	            	'user_password': user_password,
	            	're_user_password': re_user_password,
	            	'security': form_ajax_object.security_nonce
	          	},
	          	success: function(data){
						$(form).removeClass('ajax-preload');
	            	$('.form-status', form).show().html(data.message); 
	          	},
	          	error: function(data) {
						$(form).removeClass('ajax-preload');
	          	}
	        	});
	        	
				e.preventDefault();

	      });
		},

		ajaxChangeUserInfo: function(){
			$('form.lt-change-profile-form').on('submit', function(e){
            e.preventDefault();
            var form = $(this);
            $(form).addClass('loading');
            $.ajax({
              type:'POST',
              dataType: 'json',
              url: form_ajax_object.ajaxurl,
              data: {
	            	'action': "halpes_change_user_info",
	            	'form_data': form.serialize(),
	            	'security': form_ajax_object.security_nonce
	          	},
            }).done(function(data) {
              	$('.form-status', form).show().html(data.message); 
            });
        });
		},

		ajaxWishlist: function(){

			// Add Wishlist
				$(document).delegate('.ajax-wishlist-link.wishlist-add', 'click', function(e){
					$(this).addClass('ajax-preload');
					var link = $(this);
					var post_id = $(this).data('post_id');
		        	$.ajax({
		        		type: 'POST',
		          	dataType: 'json',
		          	url: form_ajax_object.ajaxurl,
		          	data: {
		            	'action': "halpes_wishlist",
		            	'post_id': post_id,
		            	'mode' : 'add',
		            	'security': form_ajax_object.security_nonce
		          	},
		          	success: function(data){
		          		link.removeClass('ajax-preload');
		          		link.removeClass('wishlist-add');
		          		link.addClass('wishlist-remove');
		          		if(!data.logged_in){
		          			$('#form-ajax-login-popup').modal('show'); 
		          		}
		          		console.log(data.add_wishlist);
		          		if(data.add_wishlist == 'added' ){
								link.addClass('wishlist-added');
		          		}
		          	},
		          	error: function(data) {
							console.log('error');
		          	}
		        	});
					e.preventDefault();
				});


			// Remove Wishlist
			$(document).delegate('.ajax-wishlist-link.wishlist-remove', 'click', function(e){
				$(this).addClass('ajax-preload');
				var link = $(this);
				var post_id = $(this).data('post_id');
	        	$.ajax({
	        		type: 'POST',
	          	dataType: 'json',
	          	url: form_ajax_object.ajaxurl,
	          	data: {
	            	'action': "halpes_wishlist",
	            	'post_id': post_id,
	            	'mode' : 'remove',
	            	'security': form_ajax_object.security_nonce
	          	},
	          	success: function(data){
	          		link.removeClass('ajax-preload');
	          		link.addClass('wishlist-add');
		          	link.removeClass('wishlist-remove');
	          		if(!data.logged_in){
	          			$('#form-ajax-login-popup').modal('show'); 
	          		}
	          		console.log(data.remove_wishlist);
	          		if(data.remove_wishlist == 'removed' ){
							link.removeClass('wishlist-added');
	          		}
	          	},
	          	error: function(data) {
						console.log('error');
	          	}
	        	});
	        	
				e.preventDefault();
	      });
		},

		ajaxLoadPackage: function(){
			$('.load-lt-package').on('click', function(e){
				$('#popup-ajax-package .ajax-package-form-content').html('');
				var listing_id = $(this).data('id');
				$.ajax({
			    	type: 'POST',
			    	dataType: 'json',
			    	url: form_ajax_object.ajaxurl,
			    	data: {
	            	'action'			: 'load_lt_package',
	            	'listing_id'	: listing_id,
	            	'security'		: form_ajax_object.security_nonce
	          	},
				    success: function(data){ 
				      $('#popup-ajax-package .ajax-package-form-content').html(data.html);
			    	}
				});
				e.preventDefault();
			});
		},

		ajaxApplyPackage: function(){
			$('.ajax-package-form-content').delegate('.btn-apply-package', 'click', function(e){
				
				var listing_id = $(this).parents('.ajax-package-form-content').find('#listing-id-val').val();
				var package_id = $(this).parents('.ajax-package-form-content').find('input[name=lt_package_choose]:checked').val();
				var button = $(this);

				$.ajax({
			    	type: 'POST',
			    	dataType: 'json',
			    	url: form_ajax_object.ajaxurl,
			    	data: {
	            	'action'			: 'lt_apply_package',
	            	'listing_id'	: listing_id,
	            	'package_id'	: package_id,
	            	'security'		: form_ajax_object.security_nonce
	          	},
				    success: function(data){ 
				      $(button).parents('.ajax-package-form-content').find('.notice-text').html(data.notice);
				      if(data._status == 'success'){
				      	location.reload();
				      }
			    	}
				});

				e.preventDefault();
			});
		},

		popup: function(){
			$('a.lost-popup').on('click', function(){
				$('#form-ajax-login-popup').modal('hide'); 
			});
			$('a.registration-popup').on('click', function(){
				$('#form-ajax-login-popup').modal('hide'); 
				$('#form-ajax-lost-password-popup').modal('hide'); 
			});
			$('a.login-popup').on('click', function(){
				$('#form-ajax-registration-popup').modal('hide'); 
				$('#form-ajax-lost-password-popup').modal('hide'); 
			});
			$('.modal').on("hidden.bs.modal", function (e) { 
			   if ($('.modal:visible').length) { 
			      $('body').addClass('modal-open');
			   }
			});
		}

	}

	$(document).ready(function(){
    addonAjaxForm.init();
  })

})(jQuery);

