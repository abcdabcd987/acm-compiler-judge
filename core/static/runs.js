'use strict';

window.updater = {
    url: undefined,
    latest_id: undefined,
    watch_list: undefined,
    last_stamp: 0,
    next_stamp: 0,

    busy_interval: 1000,
    slow_interval: 10000,
    slow_down_request: 0,
    cur_interval: undefined,
    interval: undefined,
    tbody: undefined,

    init: function(url, latest_id, watch_list) {
        updater.url = url;
        updater.latest_id = latest_id;
        updater.watch_list = watch_list;

        updater.tbody = $('#run-table tbody');
        updater.set_interval('busy');
    },

    set_interval: function(type) {
        var interval;
        if (type == 'busy') {
            interval = updater.busy_interval;
            updater.slow_down_request = 0;
        } else if (updater.cur_interval == updater.slow_interval) {
            return;
        } else {
            ++updater.slow_down_request;
            if (updater.slow_down_request === 10) interval = updater.slow_interval;
            else return;
        }
        if (interval === updater.cur_interval) return;
        if (updater.interval) clearInterval(updater.interval);
        updater.cur_interval = interval;
        updater.interval = setInterval(updater.request, updater.cur_interval);
    },

    request: function() {
        var url = updater.url;
        url += '?q=' + (updater.watch_list.join(','));
        url += '&latest_id=' + updater.latest_id;
        url += '&stamp=' + updater.last_stamp;
        ++updater.next_stamp;
        $.getJSON(url, updater.onsuccess);
    },

    onsuccess: function(data) {
        if (data.stamp !== updater.last_stamp) return;
        updater.last_stamp = updater.next_stamp;
        data.watch.forEach(updater.update_watch);
        data.new.forEach(updater.add_new);
        updater.set_interval(updater.watch_list.length > 0 ? 'busy' : 'slow');
    },

    update_watch: function(r) {
        var old_tr = updater.tbody.find('tr[data-id=' + r.id + ']');
        var new_tr = $(r.row_html);
        old_tr.find('td[data-field="status" ]').html(new_tr.find('td[data-field="status" ]').html());
        old_tr.find('td[data-field="compile"]').html(new_tr.find('td[data-field="compile"]').html());
        old_tr.find('td[data-field="runtime"]').html(new_tr.find('td[data-field="runtime"]').html());
        if (r.finished) {
            var idx = $.inArray(r.id, updater.watch_list);
            if (idx !== -1) updater.watch_list.splice(idx, 1);
        }
    },

    add_new: function(r) {
        var tr = $(r.row_html);
        updater.tbody.prepend(tr);
        tr.find('[data-toggle="tooltip"]').tooltip({html: true});
        tr.hide().show('slow');
        if (!r.finished) updater.watch_list.push(r.id);
        if (r.id > updater.latest_id) updater.latest_id = r.id;
    },
};
