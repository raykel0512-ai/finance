import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# RSI 계산 함수 (pandas-ta 없이 직접 계산)
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

st.set_page_config(page_title="국장 실시간 스캐너", layout="wide")

st.title("📈 K-Stock 기술적 지표 스캐너")
st.write("버전: V1.1 (호환성 최적화 완료)")

# 사이드바 설정
st.sidebar.header("설정")
market = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ", "KRX"])
rsi_limit = st.sidebar.slider("RSI 기준 (이하)", 10, 50, 30)
sample_size = st.sidebar.number_input("분석 종목 수", value=100)

@st.cache_data(ttl=3600)
def get_list(m):
    return fdr.StockListing(m)

if st.button("🚀 스캔 시작"):
    stocks = get_list(market)
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 분석 루프
    for i, (idx, row) in enumerate(stocks[:sample_size].iterrows()):
        ticker = row['Code']
        name = row['Name']
        
        progress_bar.progress((i + 1) / sample_size)
        status_text.text(f"분석 중: {name}")
        
        try:
            # 데이터 수집 (최근 60일)
            df = fdr.DataReader(ticker, start=(datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
            if len(df) < 20: continue
            
            # 지표 계산 (직접 계산)
            df['RSI'] = calculate_rsi(df)
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            curr_rsi = df['RSI'].iloc[-1]
            curr_price = df['Close'].iloc[-1]
            prev_vol = df['Volume'].iloc[-2]
            curr_vol = df['Volume'].iloc[-1]
            vol_ratio = curr_vol / prev_vol if prev_vol > 0 else 0
            
            # 필터링 조건
            if curr_rsi <= rsi_limit:
                results.append({
                    "종목명": name,
                    "코드": ticker,
                    "현재가": int(curr_price),
                    "RSI": round(curr_rsi, 2),
                    "거래량비율": round(vol_ratio, 2),
                    "20일선이격": round((curr_price / df['MA20'].iloc[-1] - 1) * 100, 2)
                })
        except:
            continue

    status_text.text("✅ 분석 완료!")
    
    if results:
        res_df = pd.DataFrame(results)
        st.dataframe(res_df.sort_values(by="RSI"), use_container_width=True)
        csv = res_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 결과 다운로드 (CSV)", csv, "scan_result.csv", "text/csv")
    else:
        st.warning("조건에 맞는 종목이 없습니다.")
