// socket_server/events/eat_food.js
module.exports = function(io, socket) {
  socket.on('join_room', ({ username, room }) => {
    socket.join(room);
    socket.data.username = username;
    socket.data.room = room;

    console.log(`👥 ${username} joined room ${room}`);
    socket.to(room).emit('player_joined', { username });
  });

  socket.on('score_update', ({ username, room, score }) => {
    socket.to(room).emit('score_update', { username, score });
  });

  socket.on('game_over', ({ username, room, finalScore }) => {
    socket.to(room).emit('game_over', { username, finalScore });
  });
};
