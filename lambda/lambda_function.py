import boto3
import json
import pymysql
import os
import yfinance as yf

from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# 한국 시간 설정 (UTC+9)
KST = timezone(timedelta(hours=9))

# RDS 연결 설정
RDS_HOST     = os.environ.get('RDS_HOST')
RDS_USER     = os.environ.get('RDS_USER')
RDS_PASSWORD = os.environ.get('RDS_PASSWORD')
RDS_DB       = os.environ.get('RDS_DB')

# 미국 빅테크 20개 select
TICKERS = [
    "AAPL", "MSFT", "NVDA", "TSLA", "META",
    "GOOGL", "AMZN", "AMD", "INTC", "ORCL",
    "CRM", "NFLX", "ADBE", "QCOM", "TXN",
    "IBM", "UBER", "SHOP", "SNOW", "PLTR"
]

def lambda_handler(event, context):

    s3 = boto3.client('s3', region_name='ap-northeast-2')
    data = []

    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="21d")

            if len(hist) < 2:
                print(f"[SKIP] {ticker} 데이터 부족")
                continue

            today = hist.iloc[-1]
            avg_volume = hist["Volume"].iloc[:-1].mean()
            volume_ratio = round(today["Volume"] / avg_volume, 2)

            if volume_ratio >= 2.0:
                trade_signal = "급등"
            elif volume_ratio >= 1.5:
                trade_signal = "주의"
            else:
                trade_signal = "정상"

            row = {
                "ticker": ticker,
                "date": str(today.name.date()),
                "open": round(today["Open"], 2),
                "close": round(today["Close"], 2),
                "high": round(today["High"], 2),
                "low": round(today["Low"], 2),
                "volume": int(today["Volume"]),
                "avg_volume_20d": int(avg_volume),
                "volume_ratio": volume_ratio,
                "trade_signal": trade_signal
            }
            data.append(row)
            print(f"[OK] {ticker} | 거래량 비율: {volume_ratio}x | {trade_signal}")

        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")

    # S3 업로드
    filename = f"stock_{datetime.now(KST).strftime('%Y%m%d_%H%M%S')}.json"
    s3.put_object(
        Bucket="first-bucket-xgmlwns",
        Key=f"pipeline-output/{filename}",
        Body=json.dumps(data, indent=2, ensure_ascii=False)
    )
    print(f"[S3] 업로드 완료: {filename}")

    # RDS 저장
    conn = pymysql.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        db=RDS_DB,
        charset='utf8'
    )
    cursor = conn.cursor()

    for row in data:
        sql = """
        INSERT INTO stock_signals
        (ticker, date, open, close, high, low, volume, avg_volume_20d, volume_ratio, trade_signal)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            row["ticker"], row["date"], row["open"], row["close"],
            row["high"], row["low"], row["volume"], row["avg_volume_20d"],
            row["volume_ratio"], row["trade_signal"]
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"[RDS] 저장 완료: {len(data)}개 종목")

    return {
        'statusCode': 200,
        'body': json.dumps({'saved': len(data)}, ensure_ascii=False)
    }