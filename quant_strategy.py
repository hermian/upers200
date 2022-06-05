#-*- coding: utf-8 -*-
# %%
import pandas as pd
import datetime as dt
import numpy as np
import os
import re
#
pd.set_option('mode.chained_assignment',  None) # <==== 경고를 끈다
# %%

base_cols = ['회사명', '업종(대)', '업종(소)', '주가(원)', '시가총액(억)', '발표PER', '발표PBR', '시가배당률(%)']
#########################################################
# %%
def 시가총액하위20퍼센트(df):
    return df[df['시가총액(억)'] <  df['시가총액(억)'].quantile(.2)]

def 시가총액상위20퍼센트(df):
    return df[df['시가총액(억)'] >=  df['시가총액(억)'].quantile(.2)]
#%%
def 매출액YOYQOQ영업이익YOYQOQ순이익YOYQOQ_0이상(df):
    df = df[df[f'매출액{YEAR}{QUATER}YOY'] >= 0]
    df = df[df[f'매출액{YEAR}{QUATER}QOQ'] >= 0]

    df = df[df[f'영업이익{YEAR}{QUATER}YOY'] >= 0]
    df = df[df[f'영업이익{YEAR}{QUATER}QOQ'] >= 0]

    df = df[df[f'순이익{YEAR}{QUATER}YOY'] >= 0]
    df = df[df[f'순이익{YEAR}{QUATER}QOQ'] >= 0]

    return df

def 영업활동현금흐름_순이익지배_0이상(df):
    df = df[df['영업활동현금흐름(억)'] >= 0]
    df = df[df['순이익(지배)(억)'] >= 0]
    return df

def 신F스코어_3점이상(df):
    신F스코어컬럼 = ['F스코어지배주주순익>0여부', 'F스코어영업활동현금흐름>0여부', 'F스코어신주발행X여부']
    return df[df[신F스코어컬럼].sum(axis=1) >= 3]

def 랭킹합계(sr):
    새_sr = sum(sr)
    return 새_sr

def 종합_랭킹_계산(df, 역수변환=False):
    df = df[(df != 0).all(axis=1)] # 값이 0인 열은 제거한다.
    if 역수변환:
        df = df.applymap(역수)

    랭크변환_df = df.rank(ascending=False) # 값 큰게 순위가 높음 (내림차순) 숫자가 작을수록 좋음
    랭크합산_df = 랭크변환_df.apply(랭킹합계, axis=1)
    랭크합산_df = 랭크합산_df.sort_values(ascending=True) # 순위 높은 순서 정렬이 필요하기 때문에 오름차순 정렬
    return 랭크합산_df

def 역수(값):
    새값 = 1/값
    return 새값

# %%
""" 신마법공식 소형주
시가총액 하위 20%
소형주_df = df[df['시가총액(억)'] <=  df['시가총액(억)'].quantile(.2)] #원본은 '='을 빼고 계산했더라
소형주_df.loc[:, 'PBR역수']=소형주_df.loc[:,'자본(억)']/소형주_df.loc[:,'시가총액(억)']
"""
def 신마법공식_소형주(df1, n):
    """ GP/A, PBR 사용
    """
    df1 = df1[df1['차입금비율(%)'] <= 200]
    df1 = 시가총액하위20퍼센트(df1)
    df1.loc[:, 'PBR역수'] = df1.loc[:,'자본(억)']/df1.loc[:,'시가총액(억)']

    df1 = df1[(df1[['과거GP/A(%)','PBR역수']] != 0).all(axis=1)] #하나라도 0이면 제외
    df1['순위GP/A'] = df1['과거GP/A(%)'].rank(ascending=False)
    df1['순위PBR'] = df1['PBR역수'].rank(ascending=False)

    df1['종합순위'] = df1[['순위GP/A', '순위PBR']].mean(axis=1)

    신마법공식소형주 = df1.sort_values(by='종합순위').head(n)
    신마법공식소형주[base_cols].to_csv("신마법공식소형주_new.csv")
    return 신마법공식소형주['회사명']

# cols = ['과거GP/A(%)','차입금비율(%)', '자본(억)']
# 신마법공식_소형주(df.copy(), 20)
# %%
def 전종목_성장C(df1, n):  # 전종목 성장C 실적 상승 종목 중 F스코어 정렬 (매우합격)
    """매출액YOY->매출액QQQ->영업이익YOY->영업이익QOQ->순이익YOY->순이익QOQ
    --> 영업활동현금흐름(억) 0 이상 -> 순이익(지배)(억) 0 이상
    --> F스코어높은 순정렬
    --> 상위 n개
    https://data-newbie.tistory.com/523 pandas 의 filter 함수로 변수 선택하기
    FIXME: 원본과 결과가 다르다.
    """
    df1 = 매출액YOYQOQ영업이익YOYQOQ순이익YOYQOQ_0이상(df1)
    df1 = 영업활동현금흐름_순이익지배_0이상(df1)

    # FIXME: 동일 점수대에 대한 sorting 기준은.=> 전분기 대비 영업이익이 높은 것으로 정렬
    _전종목_성장C = df1.sort_values(by=['F스코어점수(9점만점)', f'영업이익{YEAR}{QUATER}QOQ'], ascending=False).head(n)
    _전종목_성장C[base_cols].to_csv('실적 성장 F우량주 전략_new.csv')
    return _전종목_성장C['회사명']

# 전종목_성장C(df.copy(), 20)

# %%
def 소형주_밸류C(df1, n):  # 소형주 밸류C 시총 하위 20%에서 과거PFCR','발표PSR','발표POR','발표PER','발표분기PER','발표PBR', 'F스코어점수 (9점만점)' 종합 점수 높은순중에서 종가 낮은순 정렬
    """ FIXME : 한종목이 다르게 나온다. (이노인스트루먼트) 이유를 모르겠다.
    """
    df1 =시가총액하위20퍼센트(df1)

    cols = ['과거PFCR', '발표PSR', '발표POR', '발표PER', '발표분기PER', '발표PBR']
    df1 = df1[(df1[cols] != 0).all(axis=1)] #하나라도 0이면 제외
    df1['종합순위'] = df1[cols].applymap(역수).rank(ascending=False).mean(axis=1)
    df1 = df1[df1['종합순위'] <= df1['종합순위'].quantile(.2)]
    _소형주_밸류C = df1.sort_values(by='주가(원)').head(n)
    _소형주_밸류C[base_cols].to_csv("시총하위 슈퍼가치저가주 전략_new.csv")
    return _소형주_밸류C['회사명']

# 소형주_밸류C(df.copy(), 20)
# %%
def 저가주_안전마진(df1, n):  # 저가주 안전마진 주가 하위 20%중 NCAV
    """FIXME: 한 종목이 다르다.
    """
    df1 = df1[df1['주가(원)'] <=  df1['주가(원)'].quantile(.2)]
    _저가주_안전마진 = df1.sort_values(by='청산가치비율(NCAV전략)(%)', ascending=False).head(n)
    _저가주_안전마진[base_cols].to_csv("저가주_안전마진 전략_new.csv")
    return _저가주_안전마진['회사명']

# cols = ['청산가치비율(NCAV전략)(%)']
# 저가주_안전마진(df.copy(), 20)
# %%
def 저가주_성장A(df1, n):  # 저가주 성장A 장기이평선 돌파 종목중 실적 상승한 종목을 추려 저가주 매수 (매우합격)
    df1 = df1[df1['주가>20이평'] >= 1]
    df1 = 매출액YOYQOQ영업이익YOYQOQ순이익YOYQOQ_0이상(df1)
    df1 = 영업활동현금흐름_순이익지배_0이상(df1)
    _저가주_성장A = df1.sort_values(by='주가(원)').head(n)
    _저가주_성장A[base_cols].to_csv("실적 성장 저가주 전략_new.csv")
    return _저가주_성장A['회사명']

# 저가주_성장A(df.copy(), 20)
# %%
def 전종목_배당성장(df1, n):  # 전종목 배당성장 실적 상승 종목 중 배당률 정렬 (매우합격)
    df1 = 매출액YOYQOQ영업이익YOYQOQ순이익YOYQOQ_0이상(df1)
    df1 = 영업활동현금흐름_순이익지배_0이상(df1)
    _전종목_배당성장 = df1.sort_values(by='시가배당률(%)', ascending=False).head(n)
    _전종목_배당성장[base_cols].to_csv("실적 성장 배당주 전략_new.csv")
    return _전종목_배당성장['회사명']

# 전종목_배당성장(df.copy(), 20)

# %%
def 소형주_해자밸류(df1, n):  # 소형주 해자밸류 실적 상승 종목 중 슈퍼가치주 (매우합격)
    df1 = 시가총액하위20퍼센트(df1)
    df1= 영업활동현금흐름_순이익지배_0이상(df1)

    매출영업순이익성장 = df1[[f'매출액{YEAR}{QUATER}YOY', f'매출액{YEAR}{QUATER}QOQ',
                          f'영업이익{YEAR}{QUATER}YOY', f'영업이익{YEAR}{QUATER}QOQ',
                          f'순이익{YEAR}{QUATER}YOY', f'순이익{YEAR}{QUATER}QOQ']]
    매출영업순이익성장종합랭킹 = 종합_랭킹_계산(매출영업순이익성장, True)
    df1 = df1.loc[매출영업순이익성장종합랭킹.index]

    슈퍼가치_컬럼추출 = df1[['과거PFCR', '발표PSR', '발표POR', '발표PER', '발표분기PER', '발표PBR']]
    슈퍼가치 = df1.loc[종합_랭킹_계산(슈퍼가치_컬럼추출, True).index]
    슈퍼가치[base_cols].head(n).to_csv("실적 성장 슈퍼가치 전략_new.csv")
    return 슈퍼가치.head(n)['회사명']

# 소형주_해자밸류(df.copy(), 20)

#%%
def 소형주_해자성장A(df1, n):  # 소형주 해자성장A 시총하위 종목중 이익률지표 성장률
    df1 = 시가총액하위20퍼센트(df1)

    df1 = 신F스코어_3점이상(df1)

    이익율성장율 = df1[['발표OPM증가율(최근분기)','발표NPM증가율(최근분기)','발표ROE증가율(최근분기)','발표자본증가율(최근분기)']]
    시총하위이익률성장율 = df1.loc[종합_랭킹_계산(이익율성장율).index]
    시총하위이익률성장율[base_cols].head(n).to_csv("시총하위 이익율 성장률 전략_new.csv")
    return 시총하위이익률성장율.head(n)['회사명']

# 소형주_해자성장A(df.copy(), 20)
# %%
def 소형주_해자성장B(df1, n):  # 소형주 해자성장B 실적 상승 종목 중 영업이익률 정렬 전종목 > 소형주
    df1 = 시가총액하위20퍼센트(df1)

    df1 = 매출액YOYQOQ영업이익YOYQOQ순이익YOYQOQ_0이상(df1)
    df1= 영업활동현금흐름_순이익지배_0이상(df1)

    이익_컬럼추출 = df1[["5년평균OPM", "발표OPM(%)", "발표분기OPM(%)"]]
    실적성장이익률우량주 = df1.loc[종합_랭킹_계산(이익_컬럼추출).index]
    실적성장이익률우량주[base_cols].head(n).to_csv("실적 성장 이익률우량 소형주 전략_new.csv")
    return 실적성장이익률우량주.head(n)['회사명']

# 소형주_해자성장B(df.copy(), 20)
# %%
def 전종목_해자성장B(df1, n):  # 전종목 해자성장B 실적 상승 종목 중 영업이익률 정렬 (매우합격)
    df1 = 매출액YOYQOQ영업이익YOYQOQ순이익YOYQOQ_0이상(df1)
    df1= 영업활동현금흐름_순이익지배_0이상(df1)

    이익_컬럼추출 = df1[["5년평균OPM", "발표OPM(%)", "발표분기OPM(%)"]]
    실적성장이익률우량주 = df1.loc[종합_랭킹_계산(이익_컬럼추출).index]
    실적성장이익률우량주[base_cols].head(n).to_csv("실적 성장 이익률우량주 전략_new.csv")
    return 실적성장이익률우량주.head(n)['회사명']

# 전종목_해자성장B(df.copy(), 20)

#%%
def 시가총액중형주(df):
    """ 0.2~0.8 를 중형주라 하자
    """
    cond1 = df['시가총액(억)'] < df['시가총액(억)'].quantile(.8)
    cond2 = df['시가총액(억)'] >= df['시가총액(억)'].quantile(.2)
    cond = (cond1) & (cond2)
    return df[cond]
#%%
def 중형주_성장B(df1, n):  # 중형주 성장B 시총중위 종목중 신F스코어 통과 종목중 실적 성장률
    """ FIXME: 결과 완전히 다름, 시가총액중형주() 함수부터 검토 필요
    """
    df1 = 시가총액중형주(df1)
    df1 = 신F스코어_3점이상(df1)

    이익성장률_컬럼추출 = df1[[f'매출액{YEAR}{QUATER}YOY', f'매출액{YEAR}{QUATER}QOQ',
                            f'영업이익{YEAR}{QUATER}YOY', f'영업이익{YEAR}{QUATER}QOQ',
                            f'순이익{YEAR}{QUATER}YOY', f'순이익{YEAR}{QUATER}QOQ']]
    실적성장이익률우량주 = df1.loc[종합_랭킹_계산(이익성장률_컬럼추출).index]
    실적성장이익률우량주[base_cols].head(n).to_csv("시총중위 이익성장률 전략_new.csv")
    return 실적성장이익률우량주.head(n)['회사명']

# 중형주_성장B(df.copy(), 20)
# %%
def 중형주_밸류C(df1, n):  # 중형주 밸류C 시총 중위종목에서 과거PFCR','발표PSR','발표POR','발표PER','발표분기PER','발표PBR', 'F스코어점수 (9점만점)' 종합 점수 높은순중에서 종가 낮은순 정렬
    """FIXME : 한종목이 다르다. 이노인스트루먼트
    """
    df1 = 시가총액중형주(df1)

    슈퍼가치_컬럼추출 = df1[['과거PFCR', '발표PSR', '발표POR', '발표PER', '발표분기PER', '발표PBR']].copy()
    df1.loc[:, '슈퍼가치등수'] = 종합_랭킹_계산(슈퍼가치_컬럼추출, 역수변환=True).copy()
    df1 = df1[df1['슈퍼가치등수'] <  df1['슈퍼가치등수'].quantile(.2)] #슈퍼가치 등수 20%(작은값)
    _중형주_밸류C = df1.sort_values(by='주가(원)').head(n)
    _중형주_밸류C[base_cols].to_csv("시총중위 슈퍼가치저가주 전략_new.csv")
    return _중형주_밸류C['회사명']

# 중형주_밸류C(df.copy(), 20)
# %%
def 소형주_컨트래리안A(df1, n): # 소형주 컨트래리안A 12개월 등락률 0%이상 소형 저가주 종목중 주가 시총 1개월 등락률 낮은순
    """컨트래리안 전략: 중장기 상승추세에 있는 펀더멘탈이 우수한 우량기업 중에서 단기적으로 주가가 급락한 종목에 투자
    """
    df1 = df1[df1['1년등락률(%)'] > 0]

    주가시총1개월등락률 = df1[['주가(원)', '시가총액(억)', '1개월등락률(%)']]
    컨트래리안 = df1.loc[종합_랭킹_계산(주가시총1개월등락률, 역수변환=True).index]
    컨트래리안[base_cols].head(n).to_csv("소형주 컨트래리안 전략_new.csv")
    return 컨트래리안.head(n)['회사명']

# 소형주_컨트래리안A(df.copy(), 20)
# %%
def 소형주_성장밸류(df1, n, ):  # 소형주 성장B + 슈퍼가치 시총하위 종목중 신F스코어 통과 종목중 실적 성장률 + 슈퍼가치
    df1 = 시가총액하위20퍼센트(df1)
    df1 = 신F스코어_3점이상(df1)

    슈퍼가치_컬럼추출 = df1[['과거PFCR', '발표PSR', '발표POR', '발표PER', '발표분기PER', '발표PBR']]
    df1['슈퍼가치등수'] = 종합_랭킹_계산(슈퍼가치_컬럼추출, 역수변환=True)

    이익성장률_컬럼추출 = df1[[f'매출액{YEAR}{QUATER}YOY', f'매출액{YEAR}{QUATER}QOQ',
                            f'영업이익{YEAR}{QUATER}YOY', f'영업이익{YEAR}{QUATER}QOQ',
                            f'순이익{YEAR}{QUATER}YOY', f'순이익{YEAR}{QUATER}QOQ',]]
    df1['이익성장등수'] = 종합_랭킹_계산(이익성장률_컬럼추출)
    df1.dropna(inplace=True)

    df1['종합등수'] = df1['슈퍼가치등수'] + df1['이익성장등수']
    _소형주_성장밸류 = df1.sort_values(by='종합등수').head(n)
    _소형주_성장밸류[base_cols].to_csv("시총하위 이익성장+슈퍼가치_new.csv")
    return _소형주_성장밸류['회사명']

def extract_header(real_name):
    ''' real_name으로 부터 년도와 분기를 추출한다. real_name에는 실적발표반영, 실적데이터반영, 재무데이터반영등이 있다.

        real_name : 퀀트킹 사이트에 올라와 있는 게시판의 제목 ex)퀀트데이터2022.05.25(22년1Q실적발표반영)

        return:
            year : real_name의 '(..)'에서 년도를 추출 ex) ...(22년1Q...) -> 22년을 추출
            quater : real_name의 '(..)'에서 분기를 추출 ex) ...(22년1Q...) --> 1Q를 추출 다만 실적이라는 단어가 들어 있으면 '(E)'를 추가한다.
    '''
    regexp = re.compile(r'.*\(((\d+년)(\dQ).*)\)')
    matchobj = regexp.search(real_name)
    print(matchobj.group(1), matchobj.group(2), matchobj.group(3))
    year = matchobj.group(2)
    quater = matchobj.group(3)
    if '실적' in real_name:
        quater += '(E)'
    return year, quater

# 소형주_성장밸류(df.copy(), 20)
# %%
if __name__ == '__main__':
    import csv
    import glob
    import os
    import mail
    import download

    path = "./"
    [os.remove(f) for f in glob.glob("./*.csv")]

    #====================================
    # 퀀트킹사이트의 최상단 파일을 다운로드한다
    #====================================
    real_name = download.download_quantking()

    ##########################################################
    # 필요하면 아래 3라인을 수정하세요
    FILENAME = 'quantking.xlsx' #'퀀트데이터2022.05.25(22년1Q실적발표반영)'
    # YEAR="22년" # 해당파일의 마지막재무데이터 반영년도 (엑셀의 FN열 헤더 참조) <== 자동 추출가능?
    # # 해당파일의 마지막재무데이터 반영분기 (FN열 헤더 : (E)가 들어 갔다 빠졌다 한다.)
    # # 제목에 "실적데이터반영" 또는 "실적발표반영"이 들어가면 1Q(E)와 같이 E가 들어가고
    # # 파일이름에 "재무데이터반영"이 들어가면 E가 없어진다.
    # QUATER="1Q"
    YEAR, QUATER = extract_header(real_name)
    print(f'YEAR : {YEAR}, QUATER: {QUATER}')
    #########################################################
    HEAD = ['발표POR',
    f'순이익{YEAR}{QUATER}QOQ',
    '1년등락률(%)',
    '발표OPM(%)',
    '발표분기PER',
    'F스코어지배주주순익>0여부',
    f'순이익{YEAR}{QUATER}YOY',
    '과거GP/A(%)',
    '청산가치비율(NCAV전략)(%)',
    '5년평균OPM',
    '발표PBR',
    f'매출액{YEAR}{QUATER}YOY',
    '업종(대)',
    '과거PFCR',
    'F스코어영업활동현금흐름>0여부',
    '회사명',
    f'영업이익{YEAR}{QUATER}QOQ',
    '발표NPM증가율(최근분기)',
    '차입금비율(%)',
    f'영업이익{YEAR}{QUATER}YOY',
    '주가(원)',
    '발표자본증가율(최근분기)',
    '업종(소)',
    f'매출액{YEAR}{QUATER}QOQ',
    '1개월등락률(%)',
    '발표PER',
    '발표ROE증가율(최근분기)',
    '시가총액(억)',
    '영업활동현금흐름(억)',
    '주가>20이평',
    '시가배당률(%)',
    '자본(억)',
    'F스코어점수(9점만점)',
    '발표PSR',
    '발표분기OPM(%)',
    '발표OPM증가율(최근분기)',
    '순이익(지배)(억)',
    'F스코어신주발행X여부',
    '거래대금(5일평균억)',
    '스팩=1',
    '본사국내=1',
    '지주사=1']

    read_df = pd.read_excel(FILENAME, sheet_name='퀀트데이터', skiprows=2, engine='openpyxl')\
                .drop('Unnamed: 0', axis=1)
    columns = read_df.columns.str.replace('\n', '').str.replace(' ', '')
    read_df.columns = columns
    read_df.set_index('코드번호', inplace=True)

    df = read_df[HEAD].copy()
    고주가제외 = df['주가(원)'] < 250000
    거래대금_5일평균억_1천만원이상 = df['거래대금(5일평균억)'] > 0.1
    영원짜리_쓰레기_제거 = df['주가(원)'] != 0
    스펙제외 = df['스팩=1'] == 0
    중국주제외 = df['본사국내=1'] == 1
    지주사제외 = df['지주사=1'] == 0
    리츠제외 = df['업종(소)'] != '부동산'
    기타금융제외 = df['업종(소)'] != '기타 금융'
    cond = 고주가제외 & 거래대금_5일평균억_1천만원이상 & 영원짜리_쓰레기_제거 & 스펙제외 & \
        중국주제외 & 지주사제외 & 리츠제외 & 기타금융제외
    df = df[cond]
    #===============================
    # 관리종목 제외
    #===============================
    URL = "http://kind.krx.co.kr/investwarn/adminissue.do?method=searchAdminIssueSub&currentPageSize=5000&pageIndex=1&orderMode=1&orderStat=D&searchMode=&searchCodeType=&searchCorpName=&repIsuSrtCd=&forward=adminissue_down&paxreq=&outsvcno=&marketType=&searchCorpNameTmp="
    관리종목 = pd.read_html(URL)[0]
    관리종목['종목코드'] = 관리종목['종목코드'].map('{:06d}'.format)

    관리종목제외 = ~df.index.str[1:].isin(관리종목['종목코드'])
    df = df[관리종목제외]

    #===============================
    # 종목 추출
    #===============================
    신마법공식_소형주(df.copy(), 20)
    전종목_성장C(df.copy(), 20)
    소형주_밸류C(df.copy(), 20)
    저가주_안전마진(df.copy(), 20)
    저가주_성장A(df.copy(), 20)
    전종목_배당성장(df.copy(), 20)
    소형주_해자밸류(df.copy(), 20)
    소형주_해자성장A(df.copy(), 20)
    소형주_해자성장B(df.copy(), 20)
    전종목_해자성장B(df.copy(), 20)
    중형주_성장B(df.copy(), 20)
    중형주_밸류C(df.copy(), 20)
    소형주_컨트래리안A(df.copy(), 20)
    소형주_성장밸류(df.copy(), 20)
    #===============================
    output_file = "result.csv"
    file_list = os.listdir(path)
    file_list_csv = [file for file in file_list if file.endswith(".csv")]

    is_first_file = True
    for file in file_list_csv:
        print(os.path.basename(file))
        with open(file, 'r') as csv_in_file:
            with open(output_file, 'a') as csv_out_file:
                freader = csv.reader(csv_in_file)
                fwriter = csv.writer(csv_out_file)
                if is_first_file:
                    for row in freader:
                        fwriter.writerow(row)
                    is_first_file = False
                else:
                    header = next(freader) # 헤더를 건너뛰는 옵션
                    for row in freader:
                        fwriter.writerow(row)
    df = pd.read_csv(output_file).drop_duplicates(['회사명'], keep="first")
    summary_df = df[['코드번호', '회사명']].copy()
    summary_df.sort_values(by='회사명', inplace=True)
    summary_df.columns = ['','종목명']
    summary_df.to_csv("매매종목.csv", encoding="cp949", index=False)

    mail.send_mail(real_name, '매매종목.csv')