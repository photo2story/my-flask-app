$(function () {
    const csvUrl = 'https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/results_relative_divergence.csv';
    let defaultTicker = 'AAPL'; 
    let isRanked = true; 
    let showOnlyFavorites = false; 
    let rankedTickers = []; 
    let favorites = JSON.parse(localStorage.getItem('favorites')) || []; 

    function fetchCSV() {
        Papa.parse(csvUrl, {
            download: true,
            header: true,
            complete: function (results) {
                rankedTickers = results.data.map(row => `${row.Rank}:${row.Ticker}`);
                sortTickers();
                fetchImagesAndReport(defaultTicker);
            },
            error: function (error) {
                console.error('Error while fetching CSV:', error);
            }
        });
    }

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
        displayTickers(); 
    }

    function displayTickers() {
        $('#tickerList').empty();
        rankedTickers.forEach(ticker => {
            const [rank, tickerName] = ticker.split(':');
            const isFavorited = favorites.includes(tickerName);
            const heartClass = isFavorited ? 'heart favorited' : 'heart';

            // 알파벳 순 정렬 시 랭킹 숫자 없이 티커명만 표시
            const displayText = isRanked ? `${rank}:${tickerName}` : `${tickerName}`;

            if (!showOnlyFavorites || (showOnlyFavorites && isFavorited)) {
                $('#tickerList').append(
                    `<div class="ticker-item" data-ticker="${tickerName}">
                        <span>${displayText}</span>
                        <span class="${heartClass}" data-ticker="${tickerName}" title="Favorite">❤</span>
                    </div>`
                );
            }
        });

        // 티커 및 하트 클릭 이벤트 처리
        $('.ticker-item').off('click').on('click', function (e) {
            if (!$(e.target).hasClass('heart')) {
                const ticker = $(this).data('ticker');
                fetchImagesAndReport(ticker);
            }
        });

        $('.ticker-item .heart').off('click').on('click', function (e) {
            e.stopPropagation();
            const ticker = $(this).data('ticker');
            if (favorites.includes(ticker)) {
                favorites = favorites.filter(fav => fav !== ticker);
                $(this).removeClass('favorited');
            } else {
                favorites.push(ticker);
                $(this).addClass('favorited');
            }
            localStorage.setItem('favorites', JSON.stringify(favorites));
            sortTickers();
        });
    }


    function fetchImagesAndReport(stockTicker) {
        $('#loading').show();
        $('#fixedGraph').empty();
        $('#scrollableGraph').empty();
        $('#reportSection').empty();

        const comparisonImageUrl = `https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/comparison_${stockTicker}_VOO.png`;
        const resultImageUrl = `https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/result_mpl_${stockTicker}.png`;
        const reportApiUrl = `https://api.github.com/repos/photo2story/my-flask-app/contents/static/images/report_${stockTicker}.txt`;

        // 고정 그래프 이미지 표시
        $('#fixedGraph').html(
            `<img src="${comparisonImageUrl}" alt="${stockTicker} vs VOO" class="clickable-image zoomable-image">`
        );

        // 스크롤 그래프 이미지 표시
        $('#scrollableGraph').html(
            `<img src="${resultImageUrl}" alt="${stockTicker} Result" class="clickable-image zoomable-image">`
        );

        // 보고서 내용 로드
        $.ajax({
            url: reportApiUrl,
            type: 'GET',
            headers: {
                'Accept': 'application/vnd.github.v3.raw'
            },
            success: function(data) {
                const htmlContent = marked.parse(data);
                $('#reportSection').html(htmlContent);
            },
            error: function(xhr, status, error) {
                console.error('Error loading report:', error);
                $('#reportSection').html('Failed to load report.');
            },
            complete: function() {
                $('#loading').hide();
            }
        });
    }

    $('#rankAlphaToggle').on('click', function () {
        isRanked = !isRanked;
        $(this).text(isRanked ? 'Rank' : 'Alpha');
        sortTickers();
    });

    $('#favFilter').on('click', function () {
        showOnlyFavorites = !showOnlyFavorites;
        $(this).toggleClass('active');
        sortTickers();
    });

    // 이미지 클릭 시 확대 표시
    $(document).on('click', '.zoomable-image', function () {
        const imageUrl = $(this).attr('src');
        const altText = $(this).attr('alt');
        const zoomWindow = window.open('', '_blank', 'width=800,height=600');
        zoomWindow.document.write(`
            <html>
                <head>
                    <title>Zoomable Image</title>
                    <style>
                        body { margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #000; }
                        img { max-width: 90%; max-height: 90%; }
                    </style>
                </head>
                <body>
                    <img src="${imageUrl}" alt="${altText}">
                </body>
            </html>
        `);
    });

    fetchCSV();
});

// (?) 아이콘 클릭 시 GitHub README 파일 로드
$('#helpIcon').on('click', function () {
    const readmeUrl = 'https://raw.githubusercontent.com/photo2story/my-flask-app/main/README.md';
    $.ajax({
        url: readmeUrl,
        type: 'GET',
        success: function(data) {
            const htmlContent = marked.parse(data); // markdown 내용을 HTML로 변환
            const newTab = window.open();
            newTab.document.write(`
                <html>
                    <head>
                        <title>README</title>
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/4.0.0/github-markdown.min.css">
                    </head>
                    <body class="markdown-body" style="padding: 20px;">
                        ${htmlContent}
                    </body>
                </html>
            `);
            newTab.document.close();
        },
        error: function() {
            alert('Failed to load README file.');
        }
    });
});
