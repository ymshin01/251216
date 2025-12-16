import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="국가별 MBTI 상세 분석", layout="wide")

st.title("🌏 국가별 MBTI 상세 분석 (32개 유형)")
st.write("원본 데이터(-A / -T 구분)를 그대로 사용하여 분석합니다.")

# -----------------------------------------------------------------------------
# 2. 데이터 로드
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    try:
        # 같은 폴더에 있는 countries.csv 파일 로드
        df = pd.read_csv('countries.csv')
        return df
    except FileNotFoundError:
        st.error("CSV 파일을 찾을 수 없습니다. 'countries.csv' 파일을 확인해주세요.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # 'Country' 컬럼을 제외한 모든 컬럼을 수치 데이터(MBTI 유형)로 간주
    mbti_cols = [col for col in df.columns if col != 'Country']

    # -----------------------------------------------------------------------------
    # 3. 사이드바: 국가 선택
    # -----------------------------------------------------------------------------
    st.sidebar.header("옵션")
    country_list = df['Country'].unique().tolist()
    
    # 한국이 있으면 기본 선택, 없으면 첫 번째 국가 선택
    default_idx = country_list.index("South Korea") if "South Korea" in country_list else 0
    selected_country = st.sidebar.selectbox("국가를 선택하세요:", country_list, index=default_idx)

    # -----------------------------------------------------------------------------
    # 4. 기능 1: 국가별 MBTI 분포 (32개 유형 그대로 시각화)
    # -----------------------------------------------------------------------------
    st.header(f"📊 {selected_country}의 세부 MBTI 분포")
    
    # 선택된 국가의 데이터 행 추출
    country_data = df[df['Country'] == selected_country].iloc[0]
    
    # 차트용 데이터프레임 생성
    # 전처리 없이 32개 컬럼을 모두 보여줍니다.
    chart_df = country_data[mbti_cols].to_frame(name='Ratio')
    chart_df.index.name = 'MBTI Type'
    
    # 값이 높은 순서대로 정렬하여 보기 좋게 표시
    chart_df_sorted = chart_df.sort_values(by='Ratio', ascending=False)
    
    st.bar_chart(chart_df_sorted)
    
    # 최다 비율 유형 표시
    top_type = chart_df_sorted.index[0]
    top_val = chart_df_sorted.iloc[0]['Ratio']
    st.info(f"👉 **{selected_country}**에서 가장 비율이 높은 세부 유형은 **{top_type}** ({top_val:.1%}) 입니다.")
    
    st.markdown("---")

    # -----------------------------------------------------------------------------
    # 5. 기능 2: 전 세계 평균 비율
    # -----------------------------------------------------------------------------
    st.header("🌍 전 세계 세부 유형 평균")
    
    # 전체 국가의 각 컬럼별 평균 계산
    global_avg = df[mbti_cols].mean().to_frame(name='Global Average')
    global_avg_sorted = global_avg.sort_values(by='Global Average', ascending=False)
    
    st.bar_chart(global_avg_sorted)
    st.caption("전체 국가 데이터의 단순 평균값입니다.")
    
    st.markdown("---")

    # -----------------------------------------------------------------------------
    # 6. 기능 3: ISTP 비율 높은 국가 TOP & 한국 비교
    # -----------------------------------------------------------------------------
    st.header("🛠️ ISTP(A+T) 비율 TOP 국가 & 한국 비교")
    
    # 분석을 위해 임시로 ISTP 합계 컬럼 생성 (원본 데이터프레임 구조는 유지)
    # 데이터에 ISTP-A와 ISTP-T가 있는지 확인
    if 'ISTP-A' in df.columns and 'ISTP-T' in df.columns:
        # 비교 분석용 임시 데이터프레임
        df_analysis = df[['Country']].copy()
        df_analysis['ISTP_Total'] = df['ISTP-A'] + df['ISTP-T']
        
        # 내림차순 정렬
        df_analysis = df_analysis.sort_values(by='ISTP_Total', ascending=False).reset_index(drop=True)
        
        # 상위 10개국
        top_n = 10
        top_countries = df_analysis.head(top_n).copy()
        top_countries['Label'] = 'Top Rank' # 색상/구분용 라벨
        
        # 한국 데이터 찾기
        korea_row = df_analysis[df_analysis['Country'] == 'South Korea']
        
        if not korea_row.empty:
            korea_rank = korea_row.index[0] + 1
            korea_val = korea_row['ISTP_Total'].values[0]
            
            # 한국 데이터 준비 (라벨 변경)
            korea_data = korea_row.copy()
            korea_data['Label'] = 'South Korea'
            
            st.write(f"한국의 **ISTP(A+T 합산)** 비율은 **{korea_val:.1%}**로, 전체 **{len(df)}개국 중 {korea_rank}위** 입니다.")
            
            # 시각화용 데이터 합치기
            # 한국이 이미 Top 10에 있다면 라벨만 변경
            if 'South Korea' in top_countries['Country'].values:
                top_countries.loc[top_countries['Country'] == 'South Korea', 'Label'] = 'South Korea'
                final_chart_data = top_countries
            else:
                # Top 10에 없으면 아래에 추가
                final_chart_data = pd.concat([top_countries, korea_data])
        else:
            st.warning("'South Korea' 데이터를 찾을 수 없습니다.")
            final_chart_data = top_countries

        # 차트 그리기
        # x축: 국가명, y축: ISTP 비율
        st.subheader("국가별 ISTP 비율 순위 (Top 10 + Korea)")
        
        # 인덱스를 국가명으로 설정하여 차트에 이름 표시
        chart_viz = final_chart_data.set_index('Country')[['ISTP_Total']]
        st.bar_chart(chart_viz)
        
        with st.expander("상세 순위 데이터 보기"):
            st.dataframe(final_chart_data[['Country', 'ISTP_Total', 'Label']].style.format({'ISTP_Total': '{:.2%}'}))
            
    else:
        st.error("데이터에 'ISTP-A' 또는 'ISTP-T' 컬럼이 없어 ISTP 분석을 진행할 수 없습니다.")

else:
    st.write("데이터를 불러올 수 없습니다.")
