var initDatePicker = function () {
    var rentalFee = {{ listing.accomodationFee }};
    var cleaningFee = {{ listing.cleaningFee }};
    var securityDeposit = {{ listing.securityDeposit }};
    var nowTemp = new Date();
    var now = new Date(nowTemp.getFullYear(), nowTemp.getMonth(), nowTemp.getDate(), 0, 0, 0, 0);
    var checkin = $('#datetimepicker6').datetimepicker({
        defaultDate: now,
        disabledDates: [
            now,
            new Date(2013, 11 - 1, 21),
        ],
        format: "MM/DD/YYYY"
    });
    var checkout = $('#datetimepicker7').datetimepicker({
        useCurrent: false, //Important! See issue #1075
        //defaultDate: new Date(nowTemp.getDate()),
        format: "MM/DD/YYYY"
    });
    checkin.on("dp.change", function (e) {
        checkin.data("DateTimePicker").hide();
        checkout.data("DateTimePicker").minDate(e.date);
        checkout.data("DateTimePicker").date(e.date.add(1, 'd'));
    });
    checkout.on("dp.change", function (e) {
        checkout.data("DateTimePicker").hide();
        checkin.data("DateTimePicker").maxDate(e.date);
        var diff = moment.duration(checkout.data("DateTimePicker").date().diff(checkin.data("DateTimePicker").date())).asDays();
        var total = (rentalFee * diff) + securityDeposit + cleaningFee;
        $('#total-pricing').text("$" + total);
        $('#num-nights').text(diff);
        $('#num-nights-times-price').text('$' + (diff * rentalFee));
        $(function() {
            $.getJSON($SCRIPT_ROOT + '/_is_available', {
                start_date: $('#checkin-picker').val(),
                end_date: $('#checkout-picker').val(),
                listing_id: '{{ listing.objectId }}'
            }, function(data) {
                if (!data.available) {
                    $('#availability-output').show();
                } else {
                    $('#availability-output').hide();
                    $('#book-button').prop('disabled', false);
                }
            });
            return false;
            });
    });

    $('#datetimepicker6').click(function() {
        checkin.data("DateTimePicker").show();
    });

    $('#datetimepicker7').click(function() {
        checkout.data("DateTimePicker").show();
    });
});



