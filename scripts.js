$(function () {
    const csvUrl = 'https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/results_relative_divergence.csv';
    let defaultTicker = 'AAPL'; // 기본 티커 설정
    let isRanked = true; // 기본적으로 Rank로 정렬
    let showOnlyFavorites = false; // 즐겨찾기만 보기 상태
    let rankedTickers = []; // 티커를 저장할 배열
    let favorites = JSON.parse(localStorage.getItem('favorites')) || []; // 티커 즐겨찾기 상태
    let imageFavorites = JSON.parse(localStorage.getItem('imageFavorites')) || []; // 이미지 즐겨찾기 상태

    // 세로 점 메뉴 클릭 이벤트
    $('.menu-icon').on('click', function() {
        $('#dropdownMenu').toggle(); // 메뉴 토글
    });

    // 메뉴 외부 클릭 시 메뉴 닫기
    $(document).on('click', function(event) {
        if (!$(event.target).closest('.menu-container').length) {
            $('#dropdownMenu').hide();
        }
    });

    // CSV 파일을 가져와 파싱하는 함수
    function fetchCSV() {
        Papa.parse(csvUrl, {
            download: true,
            header: true,
            complete: function (results) {
                rankedTickers = results.data.map(row => `${row.Rank}:${row.Ticker}`);
                sortTickers(); // 기본 정렬 방식에 따라 정렬
                fetchImagesAndReport(defaultTicker); // 초기 기본 티커로 AAPL 로드
            },
            error: function (error) {
                console.error('Error while fetching CSV:', error);
            }
        });
    }

    // 티커 목록을 Rank 또는 알파벳 순서로 정렬하는 함수
    function sortTickers() {
        if (isRanked) {
            rankedTickers.sort((a, b) => {
                const rankA = parseInt(a.split(':')[0], 10);
                const rankB = parseInt(b.split(':')[0], 10);
                return rankA - rankB;
            });
        } else {
            rankedTickers.sort((a, b) => a.split(':')[1].localeCompare(b.split(':')[1]));
        }
        displayTickers(); // 정렬 후 티커 목록을 다시 출력
    }

    // 티커 목록을 화면에 출력하는 함수
    function displayTickers() {
        $('#tickerList').empty();
        rankedTickers.forEach(ticker => {
            const [rank, tickerName] = ticker.split(':');
            const isFavorited = favorites.includes(tickerName);
            const heartClass = isFavorited ? 'heart favorited' : 'heart';

            if (!showOnlyFavorites || (showOnlyFavorites && isFavorited)) {
                if (isRanked) {
                    $('#tickerList').append(`
                        <span class="ticker-item" data-ticker="${tickerName}">
                            <span>${rank}:${tickerName}</span>
                            <span class="${heartClass}" data-ticker="${tickerName}" title="Favorite">❤</span>
                        </span>
                    `);
                } else {
                    $('#tickerList').append(`
                        <span class="ticker-item" data-ticker="${tickerName}">
                            <span>${tickerName}:${rank}</span>
                            <span class="${heartClass}" data-ticker="${tickerName}" title="Favorite">❤</span>
                        </span>
                    `);
                }
            }
        });

        // 티커 클릭 이벤트 및 즐겨찾기 하트 클릭 이벤트 처리
        $('.ticker-item').off('click').on('click', function (e) {
            if (!$(e.target).hasClass('heart')) {
                const ticker = $(this).data('ticker'); // data-ticker 속성에서 티커 이름 추출
                fetchImagesAndReport(ticker);
            }
        });

        // 티커 하트 클릭 이벤트 처리
        $('.ticker-item .heart').off('click').on('click', function (e) {
            e.stopPropagation(); // 티커 클릭 이벤트 막기
            const ticker = $(this).data('ticker');
            if (favorites.includes(ticker)) {
                favorites = favorites.filter(fav => fav !== ticker); // 즐겨찾기 해제
                $(this).removeClass('favorited');
            } else {
                favorites.push(ticker); // 즐겨찾기 추가
                $(this).addClass('favorited');
            }
            localStorage.setItem('favorites', JSON.stringify(favorites));
            sortTickers(); // 정렬된 티커 목록 갱신
        });
    }

    // 주식 데이터를 불러오는 함수
    function fetchImagesAndReport(stockTicker) {
        $('#loading').show();
        $('#comparisonSection').empty();
        $('#resultSection').empty();
        $('#report').empty();

        const comparisonImageUrl = `https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/comparison_${stockTicker}_VOO.png`;
        const resultImageUrl = `https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/result_mpl_${stockTicker}.png`;
        const reportApiUrl = `https://api.github.com/repos/photo2story/my-flask-app/contents/static/images/report_${stockTicker}.txt`;

        // 비교 이미지와 결과 이미지 추가
        $('#comparisonSection').html(`
            <div>
                <img src="${comparisonImageUrl}" alt="${stockTicker} vs VOO" class="clickable-image" onerror="this.onerror=null;this.src='https://via.placeholder.com/150';">
            </div>
        `);
        $('#resultSection').html(`
            <div>
                <img src="${resultImageUrl}" alt="${stockTicker} Result" class="clickable-image" onerror="this.onerror=null;this.src='https://via.placeholder.com/150';">
            </div>
        `);

        // 리포트 파일을 GitHub API로 로드 및 마크다운 변환
        $.ajax({
            url: reportApiUrl,
            type: 'GET',
            headers: {
                'Accept': 'application/vnd.github.v3.raw'
            },
            success: function(data) {
                const htmlContent = marked.parse(data);
                $('#report').html(htmlContent);
            },
            error: function(xhr, status, error) {
                console.error('Error loading report:', error);
                $('#report').html('Failed to load report. Please try again later. Error: ' + error);
            },
            complete: function() {
                $('#loading').hide();
                enableImageWindow();
            }
        });
    }

    // 이미지를 클릭했을 때 새 창으로 띄우는 함수
    function enableImageWindow() {
        $('.clickable-image').off('click').on('click', function () {
            const imageUrl = $(this).attr('src');
            window.open(imageUrl, '_blank');
        });
    }

    // 즐겨찾기 필터 클릭 이벤트 처리
    $('#favFilter').on('click', function () {
        showOnlyFavorites = !showOnlyFavorites;
        $(this).toggleClass('active');
        sortTickers();
    });

    // 정렬 옵션 클릭 이벤트 처리
    $('#rankSort').on('click', function () {
        isRanked = true;
        $(this).addClass('active');
        $('#alphaSort').removeClass('active');
        sortTickers();
    });

    $('#alphaSort').on('click', function () {
        isRanked = false;
        $(this).addClass('active');
        $('#rankSort').removeClass('active');
        sortTickers();
    });

    // 페이지 로드 시 CSV 데이터를 불러오기
    fetchCSV();
<<<<<<< HEAD
});
=======
});
>>>>>>> e0881f9b67b98fe97d121a3d3131858ff3833d30
