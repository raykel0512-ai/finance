import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 지표 계산 함수들 ---
def calculate_indicators(df):
    # 1. RSI
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 2. 볼린저 밴드 (20일)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['std'] = df['Close'].rolling(window=20).std()
    df['BB_upper'] = df['MA20'] + (df['std'] * 2)
    df['BB_lower'] = df['MA20'] - (df['std'] * 2)
    
    # 3. 이동평균선
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    return df

st.set_page_config(page_title="K-Stock Full Scanner", layout="wide")

st.title("🔍 국장 전 종목 멀티 지표 스캐너")
st.sidebar.header("⚙️ 스캔 설정")

# 시장 선택 및 종목 수 제한
market_choice = st.sidebar.selectbox("대상 시장", ["KOSPI", "KOSDAQ"])
scan_limit = st.sidebar.slider("스캔 종목 수 (시총 순)", 100, 2000, 500)

# 필터 조건 설정
rsi_low = st.sidebar.number_input("RSI 하한선 (과매도)", 0, 100, 30)
vol_mult = st.sidebar.number_input("거래량 급증 (전일대비 n배)", 1.0, 10.0, 2.0)

@st.cache_data
def load_all_tickers():
    # 실제로는 FDR이 차단되므로, 시총 상위 리스트를 CSV로 관리하는 게 좋으나 
    # 프로토타입용으로 주요 코드를 자동 생성합니다.
    # (실제 운영시에는 상장 종목 CSV를 GitHub에 올리는 걸 추천)
    if market_choice == "KOSPI":
        return [f"{str(i).zfill(6)}.KS" for i in range(100, 10000)] # 간이 생성
    else:
        return [f"{str(i).zfill(6)}.KQ" for i in range(100, 10000)]

if st.button("🚀 전 종목 스캔 시작 (약 1~3분 소요)"):
    # 1. 종목 리스트 준비 (여기서는 시뮬레이션 코드지만 실제 리스트를 넣으면 됨)
    # 실제로는 krx 리스트를 파일에서 읽어오는 것이 가장 빠름
    # 우선 테스트를 위해 주요 종목 리스트만 활용하고, 코드를 보강함
    st.info("데이터를 배치로 불러오는 중입니다... 잠시만 기다려주세요.")
    
    # 예시: 시총 상위권을 대변하는 주요 코드들 (실제로는 수천 개 가능)
    # 실제 구현시에는 모든 코드를 리스트로 만듭니다.
    all_codes = [f"{str(i).zfill(6)}.KS" for i in ["005930", "000660", "035420", "005380", "035720", "068270", "005490", "051910", "000270", "105560"]]
    # ... 여기에 2000개를 넣어도 배치는 작동합니다.
    
    results = []
    
    # 배치를 위한 진행바
    batch_size = 20
    for i in range(0, len(all_codes), batch_size):
        batch = all_codes[i:i+batch_size]
        tickers_str = " ".join(batch)
        
        try:
            # 묶어서 한 번에 다운로드 (속도 핵심!)
            data = yf.download(tickers_str, period="100d", group_by='ticker', progress=False)
            
            for ticker in batch:
                if ticker not in data or data[ticker].empty: continue
                
                df = data[ticker].copy().dropna()
                if len(df) < 60: continue
                
                df = calculate_indicators(df)
                
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # --- 조건 필터링 ---
                # 조건 A: RSI 30 이하
                # 조건 B: 현재가가 볼린저 밴드 하단보다 낮음
                # 조건 C: 거래량이 전일보다 n배 높음
                
                cond_rsi = last['RSI'] <= rsi_low
                cond_bb = last['Close'] <= last['BB_lower']
                cond_vol = last['Volume'] >= prev['Volume'] * vol_mult
                
                if cond_rsi or cond_bb: # 조건 중 하나라도 만족하면 추가
                    results.append({
                        "종목": ticker,
                        "현재가": int(last['Close']),
                        "RSI": round(last['RSI'], 1),
                        "BB상태": "하단이탈" if last['Close'] < last['BB_lower'] else "정상",
                        "거래량증폭": round(last['Volume']/prev['Volume'], 1),
                        "이동평균": "정배열" if last['MA5'] > last['MA20'] > last['MA60'] else "역배열"
                    })
        except:
            continue
            
    if results:
        res_df = pd.DataFrame(results)
        st.subheader("🎯 필터링 결과")
        st.dataframe(res_df, use_container_width=True)
        
        # 상세 분석용
        st.write("💡 **팁:** RSI가 낮으면서 볼린저 하단에 걸린 종목은 반등 가능성이 높습니다.")
    else:
        st.warning("조건에 맞는 종목이 없습니다. 필터 수치를 조절해보세요.")
