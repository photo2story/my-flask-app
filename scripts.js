$(function () {
    const csvUrl = 'https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/results_relative_divergence.csv';
    let defaultTicker = 'AAPL'; 
    let isRanked = true; 
    let rankedTickers = []; 

    function fetchCSV() {
        Papa.parse(csvUrl, {
            download: true,
            header: true,
            complete: function (results) {
                rankedTickers = results.data.map(row => ({
                    rank: row.Rank,
                    ticker: row.Ticker,
                    delta_previous_relative_divergence: parseFloat(row.Delta_Previous_Relative_Divergence) // Delta_Previous_Relative_Divergence 값 추가
                }));
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
            rankedTickers.sort((a, b) => a.rank - b.rank);
        } else {
            rankedTickers.sort((a, b) => a.ticker.localeCompare(b.ticker));
        }
        displayTickers(); 
    }

    function displayTickers() {
        $('#tickerList').empty();
        rankedTickers.forEach(tickerData => {
            const { rank, ticker, delta_previous_relative_divergence } = tickerData;

            // 글씨 색깔을 Delta_Previous_Relative_Divergence 값에 따라 설정
            let textColor = 'white'; // 기본값: 흰색
            if (delta_previous_relative_divergence > 0) {
                textColor = 'green'; // 양수일 경우 녹색
            } else if (delta_previous_relative_divergence < 0) {
                textColor = '#FF6F61'; // 음수일 경우 빨간색
            }

            // 알파벳 순 정렬 시 랭킹 숫자 없이 티커명만 표시
            const displayText = isRanked ? `${rank}:${ticker}` : `${ticker}`;

            $('#tickerList').append(
                `<div class="ticker-item" data-ticker="${ticker}" style="color:${textColor};">
                    <span>${displayText}</span>
                </div>`
            );
        });

        // 티커 클릭 이벤트 처리
        $('.ticker-item').off('click').on('click', function (e) {
            const ticker = $(this).data('ticker');
            fetchImagesAndReport(ticker);
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
