angular.module('gah.controllers', []).
controller('HeaderController', ['$scope', function ($scope) {
  $scope.showNav = false;
  $scope.toggleNavigation = function () {
    $scope.showNav = !$scope.showNav;
  };
}]).
controller('IndexController', ['$scope', function ($scope) {}]).
controller('WhoAreYouController', ['$scope', 'Stalin', '$routeParams', '$location', function ($scope, Stalin, $routeParams, $location) {
  $scope.saveName = function () {
    Stalin.setName($scope.name);
    $location.path('/lobby/' + $routeParams.then);
  };
}]).
controller('CastroController', ['$scope', 'ff', function ($scope, ff) {
  $scope.messages = [];
  ff.on('lobby_update').then(null, null, function (payload) {
    console.dir(payload);
  });
}]).
controller('LobbyJoinController', ['$scope', '$location', 'Stalin', function ($scope, $location, Stalin) {
  if (!Stalin.hasName()) $location.path('/lobby/join/whoareyou');
  $scope.Stalin = Stalin;
  console.log(Stalin.getName());
  $scope.joinGame = function () {
    Stalin.joinGame($scope.keyword);
    $location.path('/lobby');
  };
}]).
controller('LobbyController', ['$scope', '$location', '$routeParams', 'Stalin', function ($scope, $location, $routeParams, Stalin) {
  if (!Stalin.hasName()) $location.path('/lobby/index/whoareyou');
  if (!Stalin.hasGame()) Stalin.createGame($routeParams.keyword);
  $scope.Stalin = Stalin;
  $scope.sendPayload = function () {
    Stalin.send($scope.payload);
    $scope.payload = '';
  };
}]);
