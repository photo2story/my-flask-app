# config_assets.py

# Updated config_assets.py from Universe JSON
# Generated from universe_260118.json on 2026-01-18 13:36:32
# 사람이 직접 확인/수정하는 최종 기준 파일

def extract_all_tickers(stock_dict):
    """
    중복 제거 버전: 같은 티커가 여러 섹터에 있어도 1번만 추가 (순서 유지)
    """
    seen = set()
    result = []

    def _add(t):
        if t not in seen:
            seen.add(t)
            result.append(t)

    for sector_or_group in stock_dict.values():
        if isinstance(sector_or_group, dict):  # 중첩 구조일 경우
            for group_list in sector_or_group.values():
                # group_list가 dict일 수도 있으니 한 번 더 방어
                if isinstance(group_list, dict):
                    for lst in group_list.values():
                        for t in lst:
                            _add(t)
                elif isinstance(group_list, list):
                    for t in group_list:
                        _add(t)
        elif isinstance(sector_or_group, list):
            for t in sector_or_group:
                _add(t)

    return result


STOCKS = {
    'Coin': {
        'Leaders': [
            'BTC-USD',  #1 Bitcoin - 대표 디지털 자산
            'ETH-USD',  #2 Ethereum - 스마트 계약 및 디앱 플랫폼
            'XRP-USD',  #3 Ripple - 빠른 송금 네트워크
            'SOL-USD',  #4 Solana - 고속 블록체인 프로토콜
            'LINK-USD',  #5 Chainlink - 블록체인 데이터 통합 플랫폼
            'DOGE-USD',  #6 Dogecoin - 밈 기반 디지털 자산
            'SUI-USD',  #7 Sui - 고속 블록체인 프로토콜
            'TRX-USD',  #8 Tron - 고속 블록체인 프로토콜
            'BNB-USD',  #9 Binance Coin - 비트코인 체인 기반 디지털 자산
            'ADA-USD',  #10 Cardano - 환경 친화적인 블록체인
            'ONDO-USD',  #11 Ondo Finance - RWA(실물자산) 토큰화 DeFi 플랫폼
        ]
    },
    'Technology': {
        'Leaders': [
            'AAPL',  #12 Apple - 아이폰 기반 글로벌 기술 플랫폼 및 서비스
            'ACN',  #13 Accenture - 글로벌 IT 컨설팅 및 전략 서비스 리더
            'AMAT',  #14 Applied Materials - 반도체 제조 장비 분야 글로벌 선도
            'AMD',  #15 AMD - CPU 및 GPU 설계 분야 혁신 리더
            'APH',  #16 Amphenol - 글로벌 전자 및 광섬유 커넥터 제조 전문
            'AVGO',  #17 Broadcom - 유무선 통신 및 인프라 반도체 선도 기업
            'CRM',  #18 Salesforce - 글로벌 1위 고객 관계 관리(CRM) 플랫폼
            'CSCO',  #19 Cisco - 글로벌 네트워크 장비 및 보안 솔루션 리더
            'IBM',  #20 IBM - 하이브리드 클라우드 및 AI 비즈니스 서비스
            'INTC',  #21 Intel - PC 및 데이터센터 CPU 제조 선도 기업
            'KLAC',  #22 KLA Corporation - 반도체 제조 공정 및 제어 장비 전문
            'LRCX',  #23 Lam Research - 식각 등 반도체 제조 장비 리더
            'MSFT',  #24 Microsoft - 클라우드 및 생산성 소프트웨어 글로벌 1위
            'MU',  #25 Micron - 메모리 반도체(DRAM, NAND) 제조 전문
            'NOW',  #26 ServiceNow - 기업용 워크플로우 자동화 플랫폼 전문
            'NVDA',  #27 Nvidia - 글로벌 AI 및 GPU 컴퓨팅 하드웨어 리더
            'ORCL',  #28 Oracle - 글로벌 엔터프라이즈 데이터베이스 및 클라우드
            'PLTR',  #29 Palantir - 빅데이터 분석 및 AI 의사결정 플랫폼
            'TER',  #30 Teradyne - 반도체 테스트·산업용 로봇(UR 등)
            'TXN',  #31 Texas Instruments - 아날로그 반도체 제조 분야 글로벌 리더
            'WDC',  #32 Western Digital - 메모리 반도체 제조 분야 글로벌 리더
        ]
    },
    'Healthcare': {
        'Leaders': [
            'ABBV',  #33 AbbVie - 바이오 의약품 및 면역학 전문 제약사
            'ABT',  #34 Abbott Labs - 의료 기기 및 진단 장비 글로벌 리더
            'ALGN',  #35 Align Technology - 의료 기기 및 진단 장비 글로벌 리더
            'AMGN',  #36 Amgen - 글로벌 바이오 테크놀로지 선도 제약사
            'ISRG',  #37 Intuitive Surgical - 다빈치 로봇 수술 시스템 제조사
            'JNJ',  #38 Johnson & Johnson - 글로벌 헬스케어 및 제약 종합 그룹
            'LLY',  #39 Eli Lilly - 당뇨, 비만 치료제 등 혁신 신약 제약사
            'MRK',  #40 Merck - 면역 항암제 등 글로벌 혁신 제약사
            'REGN',  #41 REGN - 바이오 의료 기기 및 진단 장비 글로벌 리더
            'TMO',  #42 Thermo Fisher - 생명과학 분석 장비 및 서비스 1위
            'UNH',  #43 UnitedHealth Group - 미국 최대 의료 보험 및 서비스 기업
        ]
    },
    'Financials': {
        'Leaders': [
            'AXP',  #44 American Express - 프리미엄 카드 및 결제 서비스사
            'BAC',  #45 Bank of America - 미국 대형 상업 은행 리더
            'BLK',  #46 BlackRock - 세계 최대 자산운용사
            'BRK-B',  #47 Berkshire Hathaway B - 워렌 버핏의 투자 지주사 (B주)
            'C',  #48 Citigroup - 글로벌 금융 서비스 및 투자 은행
            'GS',  #49 Goldman Sachs - 글로벌 투자 은행 및 자산 관리 리더
            'IVZ',  #50 Invesco - 글로벌 자산운용사 (AUM 2.1조 달러)
            'JKHY',  #51 JPMorgan Chase & Co - 글로벌 금융 서비스 및 투자 은행
            'JPM',  #52 JPMorgan Chase - 미국 자산 규모 1위 상업 은행
            'MA',  #53 Mastercard - 글로벌 디지털 결제 네트워크 리더
            'MS',  #54 Morgan Stanley - 글로벌 투자 은행 및 자산 관리 전문
            'SCHW',  #55 Charles Schwab - 미국 최대 증권 중개 및 금융 서비스사
            'V',  #56 Visa - 세계 최대 디지털 결제 네트워크 플랫폼
            'WFC',  #57 Wells Fargo - 미국 대표 대형 상업 은행
        ]
    },
    'Consumer Cyclical': {
        'Leaders': [
            'AMZN',  #58 Amazon - 글로벌 최대 전자상거래 및 클라우드(AWS)
            'EXPE',  #59 Expedia Group - 글로벌 여행 예약 플랫폼 리더
            'GM',  #60 General Motors - 글로벌 자동차 제조 및 판매 기업
            'HD',  #61 Home Depot - 세계 최대 주택 개량 용품 소매점
            'MCD',  #62 McDonald's - 글로벌 패스트푸드 프랜차이즈 리더
            'ROST',  #63 Ross Stores - 글로벌 의류 및 홈패션 할인 유통사
            'TJX',  #64 TJX Companies - 미국 최대 의류 및 홈패션 할인 유통사
            'TSLA',  #65 Tesla - 전기차 및 자율주행 기술 선도 기업
        ]
    },
    'Consumer Defensive': {
        'Leaders': [
            'COST',  #66 Costco - 멤버십 기반 창고형 할인매장 리더
            'DG',  #67 Dollar General - 글로벌 할인 유통 기업
            'DLTR',  #68 Dollar Tree - 글로벌 할인 유통 기업
            'EL',  #69 Estée Lauder - 프리미엄 화장품 및 뷰티 제품 제조사
            'KO',  #70 Coca-Cola - 글로벌 비알코올 음료 제조사 1위
            'PEP',  #71 PepsiCo - 글로벌 음료 및 스낵 제조사
            'PG',  #72 Procter & Gamble - 글로벌 생활용품 제조사 리더
            'PM',  #73 Philip Morris - 글로벌 담배 및 가열식 담배 제조사
            'WMT',  #74 Walmart - 세계 최대 오프라인 유통 및 할인점
        ]
    },
    'Communication Services': {
        'Leaders': [
            'DIS',  #75 Disney - 글로벌 미디어 및 엔터테인먼트 그룹
            'FOX',  #76 Fox Corporation - 글로벌 미디어 및 엔터테인먼트 그룹
            'GOOG',  #77 Alphabet C - 구글 지주사 (의결권 없는 클래스 C)
            'GOOGL',  #78 Alphabet A - 구글 지주사 (의결권 있는 클래스 A)
            'META',  #79 Meta - 페이스북, 인스타그램 기반 소셜 미디어 플랫폼
            'NFLX',  #80 Netflix - 세계 최대 유료 동영상 스트리밍 서비스
            'TMUS',  #81 T-Mobile US - 미국 혁신 통신 서비스 선도 기업
            'WBD',  #82 Warner Bros Discovery - 글로벌 미디어 및 엔터테인먼트 그룹
        ]
    },
    'Industrials': {
        'Leaders': [
            'BA',  #83 Boeing - 글로벌 항공우주 및 방위산업 리더
            'CAT',  #84 Caterpillar - 세계 최대 건설 및 광산 장비 제조사
            'CHRW',  #85 C.H. Robinson - 글로벌 물류 및 운송 서비스 플랫폼
            'EXPD',  #86 Expeditors - 글로벌 물류 및 운송 서비스 플랫폼
            'GE',  #87 GE Aerospace - 글로벌 항공기 엔진 및 항공 시스템 리더
            'GEV',  #88 GE Vernova - 글로벌 에너지 전환 및 전력 장비 기업
            'HII',  #89 Huntington Ingalls - 미국 최대 군함/항모 조선
            'RTX',  #90 RTX Corporation - 미국 대형 항공우주 및 방위산업체
            'UBER',  #91 Uber - 모빌리티 및 배달 플랫폼 혁신 리더
        ]
    },
    'Energy': {
        'Leaders': [
            'CVX',  #92 Chevron - 미국 2위 종합 에너지 기업
            'HAL',  #93 Halliburton - 글로벌 1위 유전 서비스 및 기술 기업
            'SLB',  #94 Schlumberger - 글로벌 1위 유전 서비스 및 기술 기업
            'TPL',  #95 Toll Brothers - 미국 최대 홈빌더 및 개발사
            'XOM',  #96 Exxon Mobil - 미국 최대 종합 에너지 기업
        ]
    },
    'Basic Materials': {
        'Leaders': [
            'ALB',  #97 Albemarle - 리튬 생산 및 EV 소재 기업
            'DD',  #98 DuPont de Nemours - 글로벌 1위 화학 기업
            'FCX',  #99 Freeport-McMoRan - 세계 최대 상장 구리 생산 기업
            'LIN',  #100 Linde - 글로벌 최대 산업용 가스 전문 기업
            'NEM',  #101 Newmont - 세계 최대 금 광산 채굴 기업
        ]
    },
    'Real Estate': {
        'Leaders': [
            'CBRE',  #102 CBRE Group - 글로벌 부동산 서비스 및 투자 관리 리더
            'HST',  #103 Host Hotels & Resorts - 미국 최대 호텔 및 리츠 운영 기업
            'PLD',  #104 Prologis - 글로벌 산업용 물류 센터 리츠 리더
            'VTR',  #105 Ventas - 글로벌 헬스케어 및 시니어 리빙 부동산 리츠
            'WELL',  #106 Welltower - 헬스케어 및 시니어 리빙 부동산 리츠
        ]
    },
    'Utilities': {
        'Leaders': [
            'AEP',  #107 American Electric Power - 미국 대형 전력 공급 전문 기업
            'CEG',  #108 Constellation Energy - 미국 최대 원자력 발전 운영사
            'ED',  #109 Edison International - 미국 대형 전력 공급 전문 기업
            'EIX',  #110 Edison International - 미국 대형 전력 공급 전문 기업
            'NEE',  #111 NextEra Energy - 세계 최대 재생 에너지 발전 유틸리티
        ]
    },
    'Korea ETF (My Portfolio)': {
        'Leaders': [
            '457480.KS',  #112 ACE 테슬라밸류체인 액티브 - 테슬라 밸류체인/관련 산업 테마(국내 ETF)
            '315960.KS',  #113 RISE 대형고배당 - 국내 대형주 고배당 테마(국내 ETF)
            '160580.KS',  #114 구리 실물(ETC/원자재) - 구리 가격 추종(국내 상장)
            '0138Y0.KS',  #115 PLUS 금채권혼합 ETF - 금(금현물/선물) + 채권 혼합형(국내 ETF)
            '381180.KS',  #116 TIGER 미국필라델피아반도체나스닥 - SOX(필라델피아 반도체 지수) 추종(국내 ETF)
            '456680.KS',  #117 KODEX 미국AI전력핵심인프라 - 데이터센터·전력·송배전·원전·유틸리티(국내 ETF)
            '491010.KS',  #118 TIGER 글로벌AI전력인프라액티브 - AI 산업 발전의 핵심인 전력 인프라 관련 기업 투자(액티브 ETF, 환노출형, 2024.09.10 상장)
        ],
    },
    'Theme (User Picks)': {
        'Defense': [
            'LMT',  #119 Lockheed Martin - 미국 최대 방산(전투기/미사일/우주)
            'NOC',  #120 Northrop Grumman - 방산/우주/무인기/미사일
            'GD',  #121 General Dynamics - 방산(잠수함/지상/항공)·IT
            'HII',  #122 Huntington Ingalls - 미국 최대 군함/항모 조선
            'BAESY',  #123 BAE Systems ADR - 영국계 방산 대기업(항공/전자)
            'LDOS',  #124 Leidos - 국방/정부 IT·사이버·시스템통합
            'KTOS',  #125 Kratos Defense - 무인기/전자전·국방기술
        ],
        'Space': [
            'RKLB',  #126 Rocket Lab - 소형 발사체·위성 시스템
            'ASTS',  #127 AST SpaceMobile - 위성통신(셀룰러 커버리지)
            'PL',  #128 Planet Labs - 지구관측 위성 데이터/분석
            'SPCE',  #129 Virgin Galactic - 우주관광(고위험/고변동)
            'IRDM',  #130 Iridium - 위성통신(저궤도)·IoT
            'MAXR',  #131 Maxar - 위성/지리공간 데이터 (상폐/인수 이슈 가능)
        ],
        'Robotics': [
            'TER',  #132 Teradyne - 반도체 테스트·산업용 로봇(UR 등)
            'ROK',  #133 Rockwell Automation - 산업자동화·제어 시스템
            'SYM',  #134 Symbotic - 물류/창고 자동화 로봇·AI
        ],
        'UAM': [
            'JOBY',  #135 Joby Aviation - eVTOL(도심항공모빌리티)
            'ACHR',  #136 Archer Aviation - eVTOL(도심항공모빌리티)
            'EH',  #137 EHang - eVTOL/드론(중국) (고위험/고변동)
        ],
        'Health (Trendy)': [
            'NVO',  #138 Novo Nordisk - 비만/당뇨 치료제(글로벌 리더)
        ],
        'Quantum': [
            'IONQ',  #139 IonQ - 양자컴퓨팅(이온트랩) 플랫폼
            'RGTI',  #140 Rigetti - 양자컴퓨팅(초전도) 플랫폼
            'QUBT',  #141 Quantum Computing Inc - 양자 관련(고위험/테마)
            'QBTS',  #142 D-Wave Quantum - 어닐링 기반 양자컴퓨팅
        ],
        'AI / Semis': [
            'ARM',  #143 Arm - 모바일/AI SoC 설계 IP(아키텍처)
            'TSM',  #144 TSMC - 파운드리 1위(첨단공정)
            'ASML',  #145 ASML - EUV 노광장비(반도체 핵심)
            'SMCI',  #146 Super Micro - AI 서버/랙 인프라(고변동)
        ],
    },
}


ALL_TICKERS = extract_all_tickers(STOCKS)
print(f"Total tickers: {len(ALL_TICKERS)}")
