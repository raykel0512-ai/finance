import streamlit as st
import FinanceDataReader as fdr
import pandas_ta as ta
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="국장 실시간 스캐너", layout="wide")

st.title("📈 K-Stock 기술적 지표 스캐너")
st.write("GitHub 연동형 프로토타입 - 전 종목 실시간 분석")

# 사이드바 설정
st.sidebar.header("설정")
market = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ", "KRX(전체)"])
rsi_limit = st.sidebar.slider("RSI 기준 (이하)", 10, 50, 30)
sample_size = st.sidebar.number_input("분석 종목 수 (테스트는 100~300 추천)", value=200)

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
            
            # 지표 계산
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['MA20'] = ta.sma(df['Close'], length=20)
            
            curr_rsi = df['RSI'].iloc[-1]
            curr_price = df['Close'].iloc[-1]
            prev_vol = df['Volume'].iloc[-2]
            curr_vol = df['Volume'].iloc[-1]
            vol_ratio = curr_vol / prev_vol if prev_vol > 0 else 0
            
            # 필터링 조건 (RSI 과매도)
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
        
        # 엑셀 다운로드
        csv = res_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 결과 다운로드 (CSV)", csv, "scan_result.csv", "text/csv")
    else:
        st.warning("조건에 맞는 종목이 없습니다.")
