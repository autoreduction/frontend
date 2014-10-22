(function(){
    var formUrl = $('#run_variables').attr('action');

    var isNumber = function isNumber(n){
        return !isNaN(parseFloat(n)) && isFinite(n);
    };

    String.prototype.endsWith = function(suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };

    var previewScript  = function previewScript(){
        var url = $('#preview_url').val();
        var $form = $('#run_variables');
        if($form.length===0) $form = $('#instrument_variables');
        $form.attr('action', url);
        $form.submit();
    };

    var validateForm = function validateForm(event){
        var isValid = true;
        var $form = $('#run_variables');
        if($form.length===0) $form = $('#instrument_variables');

        var validateNotEmpty = function validateNotEmpty(){
            if($(this).val().trim() === ''){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateText = function validateText(){
            validateNotEmpty.call(this);
        };
        var validateNumber = function validateNumber(){
            validateNotEmpty.call(this);
            if(!isNumber($(this).val())){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateBoolean = function validateBoolean(){
            validateNotEmpty.call(this);
            if($(this).val().toLowerCase() !== 'true' && $(this).val().toLowerCase() !== 'false'){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateListNumber = function validateListNumber(){
            var items;
            validateNotEmpty.call(this);
            if($(this).val().trim().endsWith(',')){
                $(this).parent().addClass('has-error');
                isValid = false;
            }else{
                items = $(this).val().split(',');
                for(item in items){
                    if(!isNumber(item)){
                        $(this).parent().addClass('has-error');
                        isValid = false;
                        break;
                    }
                }
            }
        };
        var validateListText = function validateListText(){
            validateNotEmpty.call(this);
            if($(this).val().trim().endsWith(',')){
                $(this).parent().addClass('has-error');
                isValid = false;
            }else{
                items = $(this).val().split(',');
                for(item in items){
                    if(item.trim() === ''){
                        $(this).parent().addClass('has-error');
                        isValid = false;
                        break;
                    }
                }
            }
        };

        // Populate all boolean values with their checked state
        $('[type="boolean"]').each(function(){
            if($(this).attr('checked')){
                $(this).val('True');
            }else{
                $(this).val('False');
            }
        });

        $('[type="text"]').each(validateText);
        $('[type="number"]').each(validateNumber);
        $('[type="boolean"]').each(validateBoolean);
        $('[type="list_number"]').each(validateListNumber);
        $('[type="list_text"]').each(validateListText);

        event.preventDefault();
        if(isValid){
            $form.attr('action', formUrl);
            $form.submit();
        }else{
            return false;
        }
    };

    var init = function init(){
        $('#previewScript').on('click', previewScript);
        $('#variableSubmit').on('click', validateForm);
    };

    init();
}())