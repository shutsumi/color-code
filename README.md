# カラーコード（色番号）をクリックでコピー

`#FF4B1E` のような6桁のカラーコード（色番号）を、全色マップから1クリックでコピーできる無料のWebツールです。

https://shutsumi.github.io/color-code/

- 全色マップ（色相×明るさ）とグレーの帯。クリックでコピー
- Canva型の微調整ピッカー（ドラッグして離すとコピー）
- HEX / RGB / HSL のコピー、カラーコード入力、RGB→6桁変換
- よく使う色（CSS色名・和色）のカラーコード一覧
- コピー履歴はブラウザのlocalStorageにだけ保存

`index.html` 1枚で動きます。ビルド不要。

## 日本の色のページ

`data/wairo.json`（Wikipedia「日本の色の一覧」の色名・読み・近似値）から、`python3 build.py` で次を生成します。

- `wairo/index.html` … 日本の色の一覧
- `wairo/<読みのローマ字>/index.html` … 1色ごとのページ（238色）
- `sitemap.xml`、トップページの和色データと相談ボタン

相談ボタンは `build.py` の `FORM_URL` に URL を入れて再生成すると表示されます。
