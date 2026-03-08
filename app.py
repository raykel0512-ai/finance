import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# RSI 직접 계산 함수
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

st.set_page_config(page_title="K-Stock Scanner (Stable)", layout="wide")

st.title("🚀 국장 종목 스캐너 (안정화 버전)")
st.info("KRX 서버 차단을 피하기 위해 Yahoo Finance 데이터를 사용합니다.")

# 1. 분석할 종목 선택 방식
st.sidebar.header("🔍 분석 대상 설정")
mode = st.sidebar.radio("종목 선택 방법", ["주요 종목 (샘플)", "직접 코드 입력"])

if mode == "주요 종목 (샘플)":
    # 샘플 종목 (삼성전자, SK하이닉스, 현대차, NAVER 등 주요 20개)
    default_tickers = {
        "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "LG에너지솔루션": "373220.KS",
        "삼성바이오로직스": "207940.KS", "현대차": "005380.KS", "기아": "000270.KS",
        "셀트리온": "068270.KS", "POSCO홀딩스": "005490.KS", "NAVER": "035420.KS",
        "LG화학": "051910.KS", "삼성SDI": "006400.KS", "카카오": "035720.KS",
        "한미반도체": "042700.KS", "에코프로비엠": "247540.KQ", "에코프로": "086520.KQ"
    }
    target_stocks = default_tickers
else:
    user_input = st.sidebar.text_area("종목코드를 입력하세요 (예: 005930, 000660)", "005930, 000660")
    codes = [x.strip() for x in user_input.split(",")]
    target_stocks = {code: f"{code}.KS" if not code.endswith(("KQ", "KS")) else code for code in codes}

rsi_limit = st.sidebar.slider("RSI 기준 (이하)", 10, 50, 30)

# 실행 버튼
if st.button("🚀 분석 시작"):
    results = []
    progress_bar = st.progress(0)
    
    total = len(target_stocks)
    for i, (name, symbol) in enumerate(target_stocks.items()):
        # 만약 직접 입력 모드라면 symbol 보정 (코스피 .KS / 코스닥 .KQ)
        # 프로토타입에서는 .KS를 기본으로 하되 실패 시 .KQ 시도
        
        progress_bar.progress((i + 1) / total)
        
        try:
            # yfinance로 데이터 가져오기
            data = yf.download(symbol, period="60d", progress=False)
            
            if data.empty or len(data) < 20:
                # .KS로 안되면 .KQ로 재시도
                symbol_kq = symbol.replace(".KS", ".KQ")
                data = yf.download(symbol_kq, period="60d", progress=False)
                if data.empty: continue

            # 지표 계산
            data['RSI'] = calculate_rsi(data)
            data['MA20'] = data['Close'].rolling(window=20).mean()
            
            curr_rsi = float(data['RSI'].iloc[-1])
            curr_price = float(data['Close'].iloc[-1])
            ma20 = float(data['MA20'].iloc[-1])
            
            # 필터 조건: RSI 기준 이하
            if curr_rsi <= rsi_limit:
                results.append({
                    "종목": name,
                    "코드": symbol,
                    "현재가": f"{int(curr_price):,}원",
                    "RSI": round(curr_rsi, 2),
                    "20일선이격": f"{round((curr_price/ma20 - 1)*100, 2)}%"
                })
        except Exception as e:
            continue

    if results:
        st.success(f"{len(results)}개의 종목이 검색되었습니다.")
        st.table(pd.DataFrame(results))
    else:
        st.warning("조건에 맞는 종목이 없습니다.")
