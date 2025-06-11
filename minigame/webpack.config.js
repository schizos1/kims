// 파일 경로: /home/schizos/study_site/minigame/webpack.config.js (또는 프로젝트 루트)

const path = require('path');

module.exports = {
  // 각 속성은 콤마(,)로 구분되어야 합니다.
  entry: {
    monopoly: './static/minigame/js/games/monopoly/main.js',
    typing_game: './static/minigame/js/games/typing_game/main.js'
  }, // <-- entry 객체와 output 객체를 구분하는 콤마

  output: {
    path: path.resolve(__dirname, 'static/minigame/js/bundles'), // <-- path와 filename을 구분하는 콤마
    filename: '[name].bundle.js'
  }, // <-- output 객체와 mode를 구분하는 콤마

  mode: 'production',

  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      }
    ]
  }, // <-- module 객체와 performance를 구분하는 콤마

  performance: {
    hints: 'warning',
    maxAssetSize: 2000000, // 2 MiB
    maxEntrypointSize: 2000000 // 2 MiB
  }
};