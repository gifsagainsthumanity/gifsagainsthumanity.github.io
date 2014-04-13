'use strict';

angular.module('gah', [
  'ngRoute',
  'gah.controllers',
  'gah.services',
  'gah.directives'
]).
config(['$routeProvider', '$locationProvider', function ($routeProvider, $locationProvider) {
  $routeProvider.
  when('/', {
    templateUrl: 'partials/index.html',
    controller: 'IndexController'
  }).
  when('/castro', {
    templateUrl: 'partials/castro.html',
    controller: 'CastroController'
  }).
  when('/lobby/:then/whoareyou', {
    templateUrl: 'partials/lobby/whoareyou.html',
    controller: 'WhoAreYouController'
  }).
  when('/lobby/join', {
    templateUrl: 'partials/lobby/join.html',
    controller: 'LobbyJoinController'
  }).
  when('/lobby/index', {
    redirectTo: '/lobby'
  }).
  when('/lobby', {
    templateUrl: 'partials/lobby/index.html',
    controller: 'LobbyController'
  }).
  when('/game', {
    templateUrl: 'partials/game.html',
    controller: 'GameController'
  });
}]);

angular.module('gah.directives', []);

var a;
function fakeMsg(msg) {
  a.onMessage(JSON.stringify(msg));
}
function fakeUser(name) {
  fakeMsg({
    action: 'player_joined',
    player: {
      name: name
    }
  });
}
