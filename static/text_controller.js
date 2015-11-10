var addToDatabase = function(word) {
    $.ajax({
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(word),
        url: '/add_word',
        success: function(e) {
            console.log(e);
        }
    });
};

var removeFromDatabase = function(word) {
    $.ajax({
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(word),
        url: '/delete_word',
        success: function(e) {
            console.log(e);
        }
    });
};

var main = function() {
    $(document).on('click', '.known', function() {
        var word = $(this).text().toLowerCase();
        var elementArray = $("span").filter(function() { return ($(this).text().toLowerCase() === word) });
        elementArray.removeClass('known').addClass('unknown');
        removeFromDatabase(word);
    });

    $(document).on('click', '.unknown', function() {
        var word = $(this).text().toLowerCase();
        var elementArray = $("span").filter(function() { return ($(this).text().toLowerCase() === word) });
        elementArray.removeClass('unknown').addClass('known');
        addToDatabase(word);
    })
};

$(document).ready(main);