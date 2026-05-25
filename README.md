# 医療用医薬品 売上分析ダッシュボード

Power BIでの最終作成を想定した、架空データとStreamlitによる1ページの画面モックです。

## 起動方法

```powershell
python generate_sales_data.py
pip install -r requirements.txt
streamlit run app.py
```

`.streamlit/config.toml` でStreamlit標準のツールバーとトップバーを非表示にし、デモ画面にフレームワーク固有のUIが表示されない設定にしています。

## ダッシュボード内容

- KPI: 売上実績、計画達成率、前年同期比、販売数量
- 月次売上: 実績、計画、前年の比較
- 製品別売上ランキング
- 地域別計画達成率
- 治療領域別売上構成（中央合計表示付きドーナツチャート）
- フィルター: 年度、治療領域、製品、地域

## Power BI用データ

`data`フォルダーに生成するCSVは、集計表ではなくスター型データモデルで利用できます。文字コードはExcelでも開きやすいUTF-8 BOM付きです。

| ファイル | 内容 | 主キー / 関係 |
| --- | --- | --- |
| `dim_date.csv` | 日付、年月、年度、四半期 | `DateKey` |
| `dim_product.csv` | 製品、治療領域、薬価、区分 | `ProductKey` |
| `dim_region.csv` | 地域、並び順 | `RegionKey` |
| `fact_sales.csv` | 月次の売上・計画・数量 | 各ディメンションへのキー |

Power BIでは次のリレーションを設定します。

| ディメンション側 | ファクト側 | 関係 |
| --- | --- | --- |
| `dim_date[DateKey]` | `fact_sales[SalesDateKey]` | 1対多 |
| `dim_product[ProductKey]` | `fact_sales[ProductKey]` | 1対多 |
| `dim_region[RegionKey]` | `fact_sales[RegionKey]` | 1対多 |

`dim_date`は日次の連続日付を持つため、Power BIで日付テーブルに指定し、前年同期比などのタイムインテリジェンスを組めます。`fact_sales`は月初日に紐づく月次粒度です。

### 基本メジャー例

```DAX
売上実績 = SUM(fact_sales[SalesAmountJPY])

売上計画 = SUM(fact_sales[BudgetAmountJPY])

計画達成率 = DIVIDE([売上実績], [売上計画])

前年売上 = CALCULATE([売上実績], SAMEPERIODLASTYEAR(dim_date[Date]))

前年同期比 = DIVIDE([売上実績] - [前年売上], [前年売上])

販売数量 = SUM(fact_sales[UnitQuantity])
```

## 想定される製品ストーリー

| 製品 | 治療領域 | データ上の特徴 |
| --- | --- | --- |
| `Diabetra` | 糖尿病 | 売上規模の大きい安定した主力品 |
| `Oncora` | 腫瘍 | 2024年7月発売後に伸長する新薬 |
| `Cardivex` | 循環器 | 徐々に減少する長期収載品 |
| `Respira` | 呼吸器 | 冬期に売上が増える重点品 |
| `Immunex` | 免疫疾患 | 規模は小さいが成長する製品 |
