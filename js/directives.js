angular.module('gah.directives', []).
directive('playercircle', function () {
  return {
    restrict: 'E',
    template: '<span></span>',
    replace: true,
    link: function (scope, elem, attrs) {
      elem.addClass('player-circle');
      attrs.$observe('for', function (value) {
        if (!value) return;
        elem.text(value.substring(0, 1));
      });
    }
  }
});
