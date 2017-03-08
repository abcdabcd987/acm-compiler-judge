'use strict';

window.updater = {
    url: undefined,
    build_id: undefined,
    latest_id: undefined,
    watch_list: undefined,
    last_stamp: 0,
    next_stamp: 0,

    busy_interval: 1000,
    bar_div: undefined,
    runs_tbody: undefined,

    init: function(url, build_id, latest_id, watch_list) {
        updater.url = url;
        updater.build_id = build_id;
        updater.latest_id = latest_id;
        updater.watch_list = watch_list;

        updater.runs_tbody = $('#table-build-runs tbody');
        updater.bar_div = $('#build-bar');
        setInterval(updater.request, updater.busy_interval);
    },

    request: function() {
        var url = updater.url;
        url += '?build_id=' + updater.build_id;
        url += '&q=' + (updater.watch_list.join(','));
        url += '&latest_id=' + updater.latest_id;
        url += '&stamp=' + updater.last_stamp;
        ++updater.next_stamp;
        $.getJSON(url, updater.onsuccess);
    },

    onsuccess: function(data) {
        if (data.stamp !== updater.last_stamp) return;
        updater.last_stamp = updater.next_stamp;
        updater.bar_div.html(data.bar);
        data.watch.forEach(updater.update_watch);
        data.runs.forEach(updater.add_new);
        updater.latest_id = data.latest_id;
        if (!data.auto_refresh) window.location.reload(true);
    },

    update_watch: function(r) {
        var old_tr = updater.runs_tbody.find('tr[data-id=' + r.id + ']');
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
        var tr = $(r.html);
        updater.runs_tbody.prepend(tr);
        tr.hide().show('slow');
        if (!r.finished) updater.watch_list.push(r.id);
        if (r.id > updater.latest_id) updater.latest_id = r.id;
    },
};
