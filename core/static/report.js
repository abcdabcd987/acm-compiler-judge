'use strict';
(function() {
    $(document).ready(function() {
        $(".text-add-one").on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const me = $(this);
            const outer = me.closest('.text-tool');
            const clone = outer.prev().clone();
            clone.find('input').val('');
            clone.find('textarea').val('');
            clone.insertBefore(outer).hide().fadeIn();
            const num_extra = parseInt(outer.data('num_extra'), 10) || 0;
            outer.data('num_extra', num_extra+1);
            outer.find('.text-del-one').prop('disabled', false);
            me.blur();
        });

        $('.text-del-one').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const me = $(this);
            const outer = me.closest('.text-tool');
            const num_extra = parseInt(outer.data('num_extra'), 10) || 0;
            if (num_extra > 0) {
                const prev = outer.prev();
                prev.fadeOut(function() {
                    $(this).remove();
                });
                outer.data('num_extra', num_extra-1);
                me.prop('disabled', num_extra < 2);
            }
            me.blur();
        });
        
        $('.text-del-one').each(function() {
            const me = $(this);
            const outer = me.closest('.text-tool');
            const num_extra = parseInt(outer.data('num_extra'), 10) || 0;
            me.prop('disabled', num_extra < 1);
        });
    });
})();