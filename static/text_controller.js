var postToDatabase = function(postObject) {
    $.ajax({
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(postObject),
        url: '/update_word',
        success: function(e) {
            console.log(e);
        }
    });
};

var translate = function(word) {
    $.post('/translate', {
        text: word
    }).done(function(translated) {
        return translated['text'];
    });
};

var main = function() {
    $(document).on('click', '.unknown', function() {
        var word = $(this).text().toLowerCase();
        var elementArray = $('span').filter(function() { return ($(this).text().toLowerCase() === word) });
        elementArray.removeClass('unknown').addClass('learning');
        var postObject = {word:word, removeFrom:'unknown', addTo:'learning'}
        postToDatabase(postObject);
    });

    $(document).on('click', '.learning', function() {
        var word = $(this).text().toLowerCase();
        var elementArray = $('span').filter(function() { return ($(this).text().toLowerCase() === word) });
        elementArray.removeClass('learning').addClass('known');
        var postObject = {word:word, removeFrom:'learning', addTo:'known'}
        postToDatabase(postObject);
    });

    $(document).on('click', '.known', function() {
        var word = $(this).text().toLowerCase();
        var elementArray = $('span').filter(function() { return ($(this).text().toLowerCase() === word) });
        elementArray.removeClass('known').addClass('unknown');
        var postObject = {word:word, removeFrom:'known', addTo:'unknown'}
        postToDatabase(postObject);
    });

    $('span').click(function() {
        var word = $(this).text();
        $.post('/translate', {
            text: word
        }).done(function(translated) {
            $('#translation').text(translated['text']);
        });
    });
};

$(document).ready(main);