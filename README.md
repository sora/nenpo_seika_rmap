# 年報成果要覧生成スクリプト

Researchmapの登録情報を使用して、年報の成果リスト(bibitem形式)を生成します。

* **必ず** 自身でスクリプトの生成結果が正しいか確認してください。
* Researchmapの登録情報が曖昧な場合、正しく成果が出力されない可能性があります。特に日付情報が無い場合や「年」のみで「月」情報が無い場合は、正しく出力されない場合があります。
* 年報成果リストと、Researchmapの成果カテゴリが異なるため、スクリプトは独自のルールでカテゴリを変換しています。詳しくは成果カテゴリの対応表を参照して、Researchmapのカテゴリに成果を登録してください。
* 出力できなかった成果があった場合は、想定外の動作なのでお知らせください。


## 成果カテゴリの対応表

| 年報成果リストカテゴリ | Researchmapカテゴリ |
| ------------- | ------------- |
| 招待講演  | 講演・口頭発表（招待の有無: 有り） |
| 招待論文  | 論文（招待の有無: 有り） |
| 受賞関連 | 受賞 |
| 著書・編集 | 書籍等出版物 |
| 雑誌論文（査読付） | 論文（査読の有無：有り、該当する掲載種別：学術雑誌） |
| 雑誌以外の査読付論文 | 論文（査読の有無：有り、該当する掲載種別：学術雑誌以外） |
| その他の発表論文 | 論文（招待の有無：無し、査読の有無：無し）、MISC |
| 公開ソフトウェア | Works(期間指定の場合はdate_fromが今年度の成果のみ) |
| 特許申請・取得 | 産業財産権（産業財産権の種類：特許権、登録日が今年度の成果のみ） |
| 特記事項 | 講演・口頭発表等（招待の有無：無し） |
| 報道関連 | メディア報道 |

カテゴリの変換ルールは、仮に設定したものなので、改善点や不明点があればご連絡ください。


## スクリプトの使用方法

1. Researchmapアカウントを作成し、成果カテゴリに従って、成果を登録してください。
2. Researchmap IDをCSVファイルに書き出してください。

CSVファイルフォーマット:
```csv
rmap_id1, lang, date_from, date_to
rmap_id2, lang
rmap_id3
```

* 必須パラメータ
  * `rmap_id`: Researchmap ID。自身のページの https://researchmap.jp/XXXX ←XXXXの部分です
* オプションパラメータ
  * `lang`: Researchmapの登録情報に複数言語が登録されている場合に、優先して成果リストに出力する言語を選択できます。デフォルトパラメータは'en'です。
  * `date_from`, `date_to`: 出力する成果の期間を指定できます。指定しない場合は、日時指定が無い成果を含むすべての期間の成果を出力します。


また、複数ユーザIDの入力に対応しています。

CSVファイル例: 
```csv
user_id1, en, "2021/4/1", "2022/3/31"
user_id2, ja
user_id3
user_id4, en, "2021/4/1", "2022/3/31"
```

3. スクリプトを実行します。

```bash
# 画面に出力
$ python3 ./nenpo_seika_rmap.py sample_users.csv
# ファイルに出力
$ python3 ./nenpo_seika_rmap.py sample_users.csv > seika_bibitem.tex
```

# スクリプトの注意事項

* researchmapの成果は「年」だけでなく「月」と「日」も入力してください。年のみの成果は年報に反映されない可能性があります。日付の修正が面倒な場合は、CSVファイルのdate_fromとdate_toを指定せずにスクリプトを実行してすべての成果を出力し、手動で成果リストを編集してください。とりあえず今年度の成果のみ出力したい場合は、今年度の成果だけで日付を入力しておれば良いと思います。
* スクリプトは、Researchmapの「公開」設定されている成果のみ取得可能です。「研究者のみに公開」や「非公開」設定の成果は取得できない可能性があります。
* 論文タイトルなどで日本語と英語両方が登録されている場合、英語表記を優先して出力します。日本語表記を利用したい場合は、CSVファイルのlangを'ja'に設定してください。

