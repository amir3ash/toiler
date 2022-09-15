(function ($) {
  'use strict';
  function he() {
    var check = true;
    for (var i = 0; i < input.length; i++) {
      if (validate(input[i]) == false) {
        showValidate(input[i]);
        check = false;
      }
    }
    const p = $('#pass2');
    if($('#pass1').val() !== p.val()){
      showValidate(p);
      check = false;
    }
    return check;
  }
  $('.login100-form-btn').on('click', function () {
    let he2=he();
     if(he2) {
       grecaptcha.execute();
     }
  });
  const input = $('.validate-input .input100');
  // $('.validate-form').on('click2', );
  $('.validate-form .input100').each(function () {
    $(this).focus(function () {
      hideValidate(this);
    });
  });
  function validate(input) {
    const x = $(input);
    if (/*$(input).attr('type') == 'email' ||*/ $(input).attr('name') === 'email') {
      if ($(input).val().trim().match(/^([a-zA-Z0-9_\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{1,5}|[0-9]{1,3})(\]?)$/) == null) {
        return false;
      }
    }
   /* else if(x.attr('name') === 'username'){
      if(x.val().length <= 1 || !usernameIsValid(x.val()))
        return false
    }*/
    else if(x.attr('name') === 'password1'){
      if(x.val().length <= 7)
        return false
    }
    else if(x.attr('name') === 'first_name'){
      if(x.val().length <= 1)
        return false
    }
    else if(x.attr('name') === 'last_name') {
      return true
    }
    else {
      if ($(input).val().trim() == '') {
        return false;
      }
    }
  }
  function showValidate(input) {
    var thisAlert = $(input).parent();
    $(thisAlert).addClass('alert-validate');
  }
  function hideValidate(input) {
    var thisAlert = $(input).parent();
    $(thisAlert).removeClass('alert-validate');
  }
  function usernameIsValid(username) {
 //^(?=.{4,99}$)(?![_])(?!.*[_.]{2})[a-zA-Z0-9_]+(?<![_.])$
 // └─────┬────┘└───┬─┘└─────┬─────┘└─────┬────┘ └───┬───┘
 //       │         │        │            │          no _ or . at the end
 //       │         │        │            │
 //       │         │        │            allowed characters
 //       │         │        │
 //       │         │        no __ or _. or ._ or .. inside
 //       │         │
 //       │         no _ beginning
 //       │
 //       username is 4-99 characters long

    return /^(?=.{2,25}$)(?![_])(?!.*[_.]{2})[a-zA-Z0-9_]+(?<![_.])$/.test(username);
}
}) (jQuery);
