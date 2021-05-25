(function ($) {
    $(document).ready(function ($) {
        if (location.pathname.indexOf('change') <= -1) {
            // List form
            $(".object-tools").append('<li><a href="./is_order_confirm_send/' + location.search + '">&nbsp;&nbsp;' + gettext('✓🔐') + '&nbsp;&nbsp;</a></li>');
        } else {
            // Change form
            // See : https://django-autocomplete-light.readthedocs.io/en/master/tutorial.html#clearing-autocomplete-on-forward-field-change
            $(document).ready(function () {
                // Bind on continent field change
                $(':input[name$=customer]').on('change', function () {
                    // Get the field prefix, ie. if this comes from a formset form
                    var prefix = $(this).getFormPrefix();

                    // Clear the autocomplete with the same prefix
                    $(':input[name=' + prefix + 'delivery]').val(null).trigger('change');
                    $(':input[name=' + prefix + 'offer_item]').val(null).trigger('change');
                });
            });
            $(document).ready(function () {
                // Bind on continent field change
                $(':input[name$=offer_item]').on('change', function () {
                    // Get the field prefix, ie. if this comes from a formset form
                    var prefix = $(this).getFormPrefix();

                    // Clear the autocomplete with the same prefix
                    $(':input[name=' + prefix + 'quantity]').val(null).trigger('change');
                    $(':input[name=' + prefix + 'comment]').val(null).trigger('change');
                });
            });
        }
    });
})(django.jQuery);
