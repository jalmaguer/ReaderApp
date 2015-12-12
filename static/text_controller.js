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

var main = function() {
    //TODO: only allow one popover to be open at a time
    $('span').click(function() {
        var e = $(this);
        var word = e.text();
        var wordClass;
        if (e.hasClass('known')) {
            wordClass = 'known';
        } else if (e.hasClass('unknown')) {
            wordClass = 'unknown';
        } else if (e.hasClass('learning')) {
            wordClass = 'learning';
        }
        var popOverHiddenContent = $('#popoverHiddenContent');
        popOverHiddenContent.find('button').removeClass('active');
        popOverHiddenContent.find('.btn-' + wordClass).addClass('active');
        var popOverSettings = {
            html: true,
            title: word,
            placement: 'top',
            content: function() {
                return popOverHiddenContent.html();
            },
            trigger: 'click'
        };
        e.popover(popOverSettings);
    });

    $(document).on('click', '.btn-translate', function() {
        var popover = $(this).parents('.popover');
        var word = popover.children('.popover-title').text();
        var loader = popover.find('.loading-gif');
        var translationContainer = popover.find('.translation-container');
        loader.show();
        $.post('/translate', {
            text: word
        }).done(function(translated) {
            loader.hide();
            var translatedWord = translated['text'];
            translationContainer.text(translatedWord);
            translationContainer.show();
        });
    });

    $(document).on('click', '.word-class-buttons button', function() {
        var popover = $(this).parents('.popover');
        var word = popover.children('.popover-title').text().toLowerCase();
        var activeButton = popover.find('.active');
        activeButton.removeClass('active');
        var oldWordClass = activeButton.text().toLowerCase();
        var newWordClass = $(this).text().toLowerCase();
        $(this).addClass('active');
        var elementArray = $('span').filter(function() { return ($(this).text().toLowerCase() === word) });
        elementArray.removeClass(oldWordClass).addClass(newWordClass);
        var postObject = {word:word, removeFrom:oldWordClass, addTo:newWordClass};
        postToDatabase(postObject);
    });

    //close popovers by clicking outside
    $(document).on('click', function(e) {
      if (typeof $(e.target).data('original-title') == 'undefined' && !$(e.target).parents().is('.popover.in')) {
        $('[data-original-title]').popover('hide');
      }
    });
};

$(document).ready(main);