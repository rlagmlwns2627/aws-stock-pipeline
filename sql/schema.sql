CREATE DATABASE IF NOT EXISTS stock_db;
USE stock_db;

-- 주식 신호 테이블
CREATE TABLE IF NOT EXISTS stock_signals (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ticker        VARCHAR(10)    NOT NULL COMMENT '종목 코드',
    date          DATE           NOT NULL COMMENT '거래일',
    open          DECIMAL(10, 2) NOT NULL COMMENT '시가',
    close         DECIMAL(10, 2) NOT NULL COMMENT '종가',
    high          DECIMAL(10, 2) NOT NULL COMMENT '고가',
    low           DECIMAL(10, 2) NOT NULL COMMENT '저가',
    volume        BIGINT         NOT NULL COMMENT '거래량',
    avg_volume_20d BIGINT        NOT NULL COMMENT '20일 평균 거래량',
    volume_ratio  DECIMAL(5, 2)  NOT NULL COMMENT '거래량 비율 (당일/20일평균)',
    trade_signal  VARCHAR(10)    NOT NULL COMMENT '거래 신호 (급등/주의/정상)',
    created_at    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP COMMENT '적재 시간'
);

-- 인덱스 추가
CREATE INDEX idx_ticker_date ON stock_signals (ticker, date);