jQuery(document).ready(function ($) {

    // Get cookie duration.
    function getDurationBySettings() {
        switch (ps_ajax.cookie_duration_unit) {
            case 'days':
                return parseInt(ps_ajax.cookie_duration);
                break;
            case 'hours':
                return new Date(new Date().getTime() + (ps_ajax.cookie_duration * 10) * 60 * 1000);
                break;
            case 'minutes':
                return new Date(new Date().getTime() + ps_ajax.cookie_duration * 60 * 1000);
                break;
            default:
                return parseInt(ps_ajax.cookie_duration);
        }
    }

    // Get cache busting URL.
    function getCacheFriendlyURL() {
        if (location.search) {
            return (location.origin).concat(location.pathname).concat(location.hash) + location.search + '&pts=' + Math.floor(Date.now() / 1000);
        } else {
            return (location.origin).concat(location.pathname).concat(location.hash) + '?pts=' + Math.floor(Date.now() / 1000);
        }
    }

    // Get hashed cookie via Ajax.
    function setHashedCookie(password) {
        $.ajax({
            type: "post", dataType: "json", url: ps_ajax.ajax_url, data: {
                'action': 'hash_password', 'hash_nonce': ps_ajax.hash_nonce, 'password': password,
            }, success: function (response) {
                Cookies.set('passster', response.password, {
                    expires: getDurationBySettings(), sameSite: 'strict'
                });
            }, async: false,
        });
    }

    // Check if we have an unlock link.
    if (ps_ajax.link_pass) {
        if (!ps_ajax.disable_cookie) {
            if (ps_ajax.link_pass.length < 25) {
                // It's an old base64 encryption.
                setHashedCookie(atob(ps_ajax.link_pass));
            } else {
                Cookies.set('passster', ps_ajax.link_pass, {
                    expires: getDurationBySettings(), sameSite: 'strict'
                });
            }

            // Handle the redirect with cache busting.
            window.location.replace(ps_ajax.permalink + '?pts=' + Math.floor(Date.now() / 1000));
        }
    }

    // Passwords
    $('.passster-submit').on('click', function (e) {
        e.preventDefault();

        // Validate form before submitting ajax.
        var form = $(this).parent().parent();

        if (!$(form)[0].checkValidity()) {
            $(form)[0].reportValidity();
        }

        ps_id = $(this).attr('data-psid');
        form = $("#" + ps_id);
        password = $("#" + ps_id + ' .passster-password').attr('data-password');
        type = $("#" + ps_id + ' .passster-password').attr('data-protection-type');
        list = $("#" + ps_id + ' .passster-password').attr('data-list');
        lists = $("#" + ps_id + ' .passster-password').attr('data-lists');
        area = $("#" + ps_id + ' .passster-password').attr('data-area');
        protection = $("#" + ps_id + ' .passster-password').attr('data-protection');
        redirect = $(this).attr('data-redirect');
        input = $("#" + ps_id + ' .passster-password').val();
        acf = $(this).attr('data-acf');

        $.ajax({
            type: "post", dataType: "json", url: ps_ajax.ajax_url, data: {
                'action': 'validate_input',
                'nonce': ps_ajax.nonce,
                'input': input,
                'password': password,
                'post_id': ps_ajax.post_id,
                'type': type,
                'list': list,
                'lists': lists,
                'area': area,
                'protection': protection,
                'acf': acf,
                'redirect': redirect
            }, beforeSend: function () {
                form.find(".ps-loader").css('display', 'block');
            }, success: function (response) {
                form.find(".ps-loader").css('display', 'none');
                if (true === response.success) {
                    // if no ajax.
                    if (!ps_ajax.unlock_mode) {
                        setHashedCookie(input);

                        if (response.redirect) {
                            window.location.replace(redirect);
                        } else {
                            window.location.href = getCacheFriendlyURL();
                        }
                    } else {

                        // set cookie if activated.
                        if (!ps_ajax.disable_cookie) {
                            setHashedCookie(input);
                        }
                        form.find('.passster-error').hide();

                        // replace shortcodes.
                        let content = response.content;

                        if (content) {
                            $.each(ps_ajax.shortcodes, function (key, value) {
                                content = content.replace(key, value);
                            });

                            $("#" + ps_id).replaceWith(content);
                        }

                        // Redirect?
                        if (response.redirect) {
                            window.location.replace(redirect);
                        }

                    }
                } else {
                    form.find('.passster-error').text(response.error);
                    form.find('.passster-error').show().fadeOut(3500);
                    $("#" + ps_id + ' .passster-password').val('');
                }
            }
        });
    });

    // Recaptcha v2
    if ($('.recaptcha-form-v2').length > 0) {
        grecaptcha.ready(function () {
            grecaptcha.render('ps-recaptcha-v2', {
                'sitekey': ps_ajax.recaptcha_key, 'callback': function (token) {
                    ps_id = $('.recaptcha-v2-submit').attr('data-psid');
                    form = $("#" + ps_id);
                    protection = $('.recaptcha-v2-submit').attr('data-protection');
                    acf = $('.recaptcha-v2-submit').attr('data-acf');
                    area = $("#" + ps_id).find('.recaptcha-v2-submit').attr('data-area');
                    redirect = $("#" + ps_id).find('.recaptcha-v2-submit').attr('data-redirect');

                    $.ajax({
                        type: "post", dataType: "json", url: ps_ajax.ajax_url, data: {
                            'action': 'validate_input',
                            'nonce': ps_ajax.nonce,
                            'token': token,
                            'post_id': ps_ajax.post_id,
                            'type': 'recaptcha',
                            'protection': protection,
                            'captcha_id': ps_id,
                            'acf': acf,
                            'area': area,
                            'redirect': redirect
                        }, success: function (response) {
                            if (true === response.success) {

                                // if no ajax.
                                if (!ps_ajax.unlock_mode) {
                                    Cookies.set('passster', 'recaptcha', {
                                        expires: getDurationBySettings(), sameSite: 'strict'
                                    });

                                    if (response.redirect) {
                                        window.location.replace(redirect);
                                    } else {
                                        window.location.href = getCacheFriendlyURL();
                                    }
                                } else {
                                    // set cookie if activated.
                                    if (!ps_ajax.disable_cookie) {
                                        Cookies.set('passster', 'recaptcha', {
                                            expires: getDurationBySettings(), sameSite: 'strict'
                                        });
                                    }
                                    form.find('.passster-error').hide();

                                    // replace shortcodes.
                                    let content = response.content;

                                    if (content) {

                                        $.each(ps_ajax.shortcodes, function (key, value) {
                                            content = content.replace(key, value);
                                        });

                                        $("#" + ps_id).replaceWith(content);
                                    }

                                    // Redirect?
                                    if (response.redirect) {
                                        window.location.replace(redirect);
                                    }
                                }
                            } else {
                                form.find('.passster-error').text(response.error);
                                form.find('.passster-error').show().fadeOut(3500);
                            }
                        }
                    });
                }
            });
        });
    }

    // ReCaptcha v3
    $('.recaptcha-form').on('submit', function (event) {
        event.preventDefault();

        ps_id = $(this).find('.passster-submit-recaptcha').attr('data-psid');
        form = $("#" + ps_id);
        protection = $(this).find('.passster-submit-recaptcha').attr('data-protection');
        acf = $(this).find('.passster-submit-recaptcha').attr('data-acf');
        area = $(this).find('.passster-submit-recaptcha').attr('data-area');
        redirect = $(this).find('.passster-submit-recaptcha').attr('data-redirect');

        grecaptcha.ready(function () {
            grecaptcha.execute(ps_ajax.recaptcha_key, {action: 'validate_input'}).then(function (token) {

                form.prepend('<input type="hidden" name="token" value="' + token + '">');
                form.prepend('<input type="hidden" name="action" value="validate_input">');

                $.ajax({
                    type: "post", dataType: "json", url: ps_ajax.ajax_url, data: {
                        'action': 'validate_input',
                        'nonce': ps_ajax.nonce,
                        'token': token,
                        'post_id': ps_ajax.post_id,
                        'type': 'recaptcha',
                        'protection': protection,
                        'captcha_id': ps_id,
                        'acf': acf,
                        'area': area,
                        'redirect': redirect
                    }, success: function (response) {
                        if (true === response.success) {

                            // if no ajax.
                            if (!ps_ajax.unlock_mode) {
                                Cookies.set('passster', 'recaptcha', {
                                    expires: getDurationBySettings(), sameSite: 'strict'
                                });

                                if (response.redirect) {
                                    window.location.replace(redirect);
                                } else {
                                    window.location.href = getCacheFriendlyURL();
                                }
                            } else {
                                // set cookie if activated.
                                if (!ps_ajax.disable_cookie) {
                                    Cookies.set('passster', 'recaptcha', {
                                        expires: getDurationBySettings(), sameSite: 'strict'
                                    });
                                }
                                form.find('.passster-error').hide();
                                // replace shortcodes.
                                let content = response.content;

                                if (content) {
                                    $.each(ps_ajax.shortcodes, function (key, value) {
                                        content = content.replace(key, value);
                                    });

                                    form.replaceWith(content);
                                }

                                // Redirect?
                                if (response.redirect) {
                                    window.location.replace(redirect);
                                }
                            }
                        } else {
                            form.find('.passster-error').text(response.error);
                            form.find('.passster-error').show().fadeOut(3500);
                        }
                    }
                });
            });
        });
    });

    // hcaptcha
    $('.hcaptcha-form').on('submit', function (event) {
        event.preventDefault();

        ps_id = $(this).find('.passster-submit-recaptcha').attr('data-psid');
        form = $("#" + ps_id);
        protection = $(this).find('.passster-submit-recaptcha').attr('data-protection');
        acf = $(this).find('.passster-submit-recaptcha').attr('data-acf');
        area = $(this).find('.passster-submit-recaptcha').attr('data-area');
        redirect = $(this).find('.passster-submit-recaptcha').attr('data-redirect');

        hcaptcha.execute({async: true})
            .then(({response, key}) => {
                $.ajax({
                    type: "post", dataType: "json", url: ps_ajax.ajax_url, data: {
                        'action': 'validate_input',
                        'nonce': ps_ajax.nonce,
                        'token': response,
                        'post_id': ps_ajax.post_id,
                        'type': 'recaptcha',
                        'protection': protection,
                        'captcha_id': ps_id,
                        'acf': acf,
                        'area': area,
                        'redirect': redirect
                    }, success: function (response) {
                        if (true === response.success) {

                            // if no ajax.
                            if (!ps_ajax.unlock_mode) {
                                Cookies.set('passster', 'recaptcha', {
                                    expires: getDurationBySettings(), sameSite: 'strict'
                                });

                                if (response.redirect) {
                                    window.location.replace(redirect);
                                } else {
                                    window.location.href = getCacheFriendlyURL();
                                }
                            } else {
                                // set cookie if activated.
                                if (!ps_ajax.disable_cookie) {
                                    Cookies.set('passster', 'recaptcha', {
                                        expires: getDurationBySettings(), sameSite: 'strict'
                                    });
                                }
                                form.find('.passster-error').hide();
                                // replace shortcodes.
                                let content = response.content;

                                if (content) {
                                    $.each(ps_ajax.shortcodes, function (key, value) {
                                        content = content.replace(key, value);
                                    });

                                    form.replaceWith(content);
                                }

                                // Redirect?
                                if (response.redirect) {
                                    window.location.replace(redirect);
                                }
                            }
                        } else {
                            form.find('.passster-error').text(response.error);
                            form.find('.passster-error').show().fadeOut(3500);
                        }
                    }
                });
            })
            .catch(err => {
                form.find('.passster-error').text(err);
                form.find('.passster-error').show().fadeOut(3500);
            });

    });

    // Concurrent logout.
    $(document).on('click', '#ps-logout', function () {
        $.ajax({
            type: 'post',
            dataType: 'json',
            url: ps_ajax.ajax_url,
            data: {'action': 'handle_logout', 'logout_nonce': ps_ajax.logout_nonce},
            success: function (response) {
                if (true === response.success) {
                    Cookies.set('passster', '', {expires: 0, sameSite: 'strict'});
                    window.location.href = getCacheFriendlyURL();
                }
            }
        });
    });
});