# 🚦 GreenGo

信号が青になるまでの残り時間をリアルタイムで表示するマップアプリのサンプル実装です。

## 概要

歩行者が次の交差点を渡れるかどうかを、手前で判断できるようにすることを目的としています。  
信号サイクルの基準時刻とサイクル定義から現在の残り秒数を推定し、地図上に色と秒数で表示します。

## ファイル構成

```
GreenGo/
├── app.py          # Streamlit アプリ本体
├── signal.json     # 信号サイクル定義（交差点ごとに編集）
└── README.md       # このファイル
```

## セットアップ

```bash
# 仮想環境を作成してパッケージをインストール
python3 -m venv .venv
.venv/bin/pip install streamlit
```

## 起動方法

```bash
.venv/bin/streamlit run app.py
```

ブラウザで http://localhost:8501 を開きます。

## signal.json の編集方法

```json
{
  "intersection": "交差点名",
  "lat": 緯度,
  "lon": 経度,
  "phases": {
    "NS": { "base_time": "HHMMSS", "green_sec": 青の秒数, "red_sec": 赤の秒数 },
    "EW": { "base_time": "HHMMSS", "green_sec": 青の秒数, "red_sec": 赤の秒数 }
  }
}
```

| フィールド | 説明 |
|---|---|
| `base_time` | その方向の**青が始まった基準時刻**（HHMMSS形式） |
| `green_sec` | 青信号の秒数 |
| `red_sec` | 赤信号の秒数 |

`base_time` を実際に目視で確認した「青が始まった時刻」に合わせると、実際の信号と同期した推定ができます。  
NS（南北横断）と EW（東西横断）は逆位相のため、`base_time` の差が `green_sec` 分になるように設定してください。

## 仕組み

```
現在の位相 = (現在時刻 - base_time) % (green_sec + red_sec)

位相 < green_sec  → 青信号、残り秒数 = green_sec - 位相
位相 >= green_sec → 赤信号、残り秒数 = (green_sec + red_sec) - 位相
```
