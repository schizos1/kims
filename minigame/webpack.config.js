const path = require('path');

// Webpack 설정
module.exports = {
  // 진입점: 모노폴리 게임의 메인 JS 파일
  entry: './static/minigame/js/games/monopoly/main.js',
  // 출력: 번들링된 결과 파일
  output: {
    path: path.resolve(__dirname, 'static/minigame/js'),
    filename: 'monopoly.bundle.js'
  },
  // 프로덕션 모드로 최적화
  mode: 'production',
  // 모듈 규칙
  module: {
    rules: [
      {
        // .js 파일을 Babel로 변환
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
  },
  // 성능 경고 설정
  performance: {
    hints: 'warning',
    maxAssetSize: 2000000, // 2 MiB
    maxEntrypointSize: 2000000 // 2 MiB
  }
};