angular.module('gah.services', []).
service('ff', ['$q', function ($q) {
  function ff() {
    this.isSecure = false;
    if (0) {
      this.host = "gah.local.codef.in";
    } else {
      this.host = "10.55.3.174";
    }
    this.port = 5000;
    this.init();
    this.listeners = {};
    this.queue = [];
  }
  ff.prototype.init = function () {
    this.sock = new WebSocket(this.getPath());
    this.sock.onopen = this.onOpen.bind(this);
    this.sock.onmessage = this.onMessage.bind(this);
    this.sock.onclose = this.onClose.bind(this);
    this.sock.onerror = this.onError.bind(this);
  };
  ff.prototype.onOpen = function () {
    console.log('socket opened');
    this.consumeQueue();
  };
  ff.prototype.onMessage = function (message) {
    message = JSON.parse(message.data);
    var listeners = this.getListenersForAction(message.action);
    var len = listeners.length;
    while (len--) {
      listeners[len].notify(message);
    }
  };
  ff.prototype.onClose = function () {
    console.log('socket closed');
  };
  ff.prototype.onError = function () {
    console.log('socket errored out');
    setTimeout(function () {
      console.log('Attempting re-connect of socket');
      ff.init();
    }, 500);
  };
  ff.prototype.send = function (payload) {
    this.queue.push(payload);
    this.consumeQueue();
  };
  ff.prototype.consumeQueue = function () {
    if (this.sock.readyState !== 1) return;
    while (this.queue.length) {
      var message = this.queue.pop();
      message = message instanceof Object ? JSON.stringify(message) : message;
      this.sock.send(message);
    }
  };
  ff.prototype.getProtocol = function () {
    return this.isSecure ? 'wss://' : 'ws://';
  };
  ff.prototype.getPath = function () {
    return this.getProtocol() + this.host + ':' + this.port;
  };
  ff.prototype.getListeners = function () {
    return this.listeners;
  };
  ff.prototype.getListenersForAction = function (action) {
    var listeners = this.getListeners();
    if (!listeners[action]) listeners[action] = [];
    return listeners[action];
  };
  ff.prototype.on = function (action) {
    var q = $q.defer();
    var listeners = this.getListenersForAction(action);
    listeners.push(q);
    return q.promise;
  };
  ff.prototype.setPort = function (port) {
    this.sock.close();
    this.port = port;
    this.init();
  };
  return new ff();
}]).
service('Stalin', ['ff', function (ff) {
  function Stalin() {
    this.name = '';
    this.lobbyOwner = '';
    this.players = [];
    this.hand = [];
    this.turn = 0;
    this.keyword = '';

    this.addHook('joined', this.onJoined);
    this.addHook('player_joined', this.onPlayerJoined);
    this.addHook('create', this.onCreate);
    this.addHook('receive_card', this.onReceiveCard);
    this.addHook('round_won', this.onRoundWon);
    this.addHook('game_over', this.onGameOver);
    this.addHook('lobby_update', this.onLobbyUpdate);
  }
  Stalin.prototype.hasName = function () {
    return !!this.getName();
  };
  Stalin.prototype.getName = function () {
    return this.name;
  };
  Stalin.prototype.setName = function (name) {
    this.name = name;
    localStorage.setItem('name', this.name);
  };
  Stalin.prototype.createGame = function (keyword) {
    ff.send({
      action: 'create',
      keyword: keyword,
      name: this.getName()
    });
  };
  Stalin.prototype.joinGame = function (keyword) {
    this.keyword = keyword;
    ff.send({
      action: 'join',
      name: this.getName(),
      keyword: this.keyword
    });
  };
  Stalin.prototype.hasGame = function () {
    return !!this.keyword;
  };
  Stalin.prototype.addHook = function (action, method) {
    ff.on(action).then(null, null, method.bind(this)); 
  };
  Stalin.prototype.onCreate = function (payload) {
    this.keyword = payload.keyword;
  };
  Stalin.prototype.onJoined = function (payload) {
    console.log('onJoined');
    console.log(payload);
  };
  Stalin.prototype.onPlayerJoined = function (payload) {
    var player = payload.player;
    this.players.push(player);
  };
  Stalin.prototype.onLobbyUpdate = function (lobby) {
    this.lobbyOwner = lobby.owner;
    this.players = lobby.lobby.players;
    this.keyword = lobby.keyword;
  };
  Stalin.prototype.onReceiveCard = function (payload) {
    var card = payload.card;
    this.hand.push(card);
  };
  Stalin.prototype.onCardPlayed = function (payload) {
    var card = payload.card;
    // add to visible set of cards for judge
  };
  Stalin.prototype.onRoundWon = function (payload) {
    var card = payload.card;
    var winner = payload.winner;
    var scores = payload.scores;
    // display the card once, with the winner
    // update points
    /*
    action: 'round_won',
    card: 'http://i.imgur.com/asdf.gif',
    winner: 'Natasha',
    scores: {
      'Natasha': 1,
      'John': 0
    }*/
  };
  Stalin.prototype.onGameOver = function (payload) {
    var winner = payload.winner;
    /* action: 'game_over',
       winner: 'Natasha' */
  };
  return new Stalin();
}]);
