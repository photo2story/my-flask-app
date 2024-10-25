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
                // 유효한 데이터만 필터링
                rankedTickers = results.data
                    .filter(row => {
                        // Ticker가 존재하고 유효한 문자열인지 확인
                        return row.Ticker && 
                               typeof row.Ticker === 'string' && 
                               row.Ticker !== 'undefined' &&
                               row.Rank && 
                               !isNaN(parseFloat(row.Delta_Previous_Relative_Divergence));
                    })
                    .map(row => ({
                        rank: parseInt(row.Rank),
                        ticker: row.Ticker,
                        delta_previous_relative_divergence: parseFloat(row.Delta_Previous_Relative_Divergence)
                    }));
                
                sortTickers();
                fetchImagesAndReport(defaultTicker);
            },
            error: function (error) {
                console.error('CSV 파일 로딩 중 오류 발생:', error);
                $('#tickerList').html('<div class="error-message">데이터 로딩 실패</div>');
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
        if (rankedTickers.length === 0) {
            $('#tickerList').html('<div class="error-message">표시할 티커가 없습니다</div>');
            return;
        }

        rankedTickers.forEach(tickerData => {
            const { rank, ticker, delta_previous_relative_divergence } = tickerData;

            let textColor = 'white';
            if (delta_previous_relative_divergence > 0) {
                textColor = '#90EE90';
            } else if (delta_previous_relative_divergence < 0) {
                textColor = '#FF7F7F';
            }

            const displayText = isRanked ? `${rank}:${ticker}` : ticker;

            $('#tickerList').append(
                `<div class="ticker-item" data-ticker="${ticker}" style="color:${textColor};">
                    <span>${displayText}</span>
                </div>`
            );
        });

        $('.ticker-item').off('click').on('click', function (e) {
            const ticker = $(this).data('ticker');
            fetchImagesAndReport(ticker);
        });
    }

    function fetchImagesAndReport(stockTicker) {
        if (!stockTicker) {
            console.error('유효하지 않은 티커:', stockTicker);
            return;
        }

        $('#loading').show();
        $('#fixedGraph').empty();
        $('#scrollableGraph').empty();
        $('#reportSection').empty();

        const comparisonImageUrl = `https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/comparison_${stockTicker}_VOO.png`;
        const resultImageUrl = `https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/result_mpl_${stockTicker}.png`;
        const reportApiUrl = `https://api.github.com/repos/photo2story/my-flask-app/contents/static/images/report_${stockTicker}.txt`;

        $('#fixedGraph').html(
            `<img src="${comparisonImageUrl}" alt="${stockTicker} vs VOO" class="clickable-image zoomable-image" onerror="this.onerror=null; this.src='error-placeholder.png';">`
        );

        $('#scrollableGraph').html(
            `<img src="${resultImageUrl}" alt="${stockTicker} Result" class="clickable-image zoomable-image" onerror="this.onerror=null; this.src='error-placeholder.png';">`
        );

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
                console.error('리포트 로딩 실패:', error);
                $('#reportSection').html('<div class="error-message">리포트를 불러올 수 없습니다.</div>');
            },
            complete: function() {
                $('#loading').hide();
            }
        });
    }

    $('#rankAlphaToggle').on('click', function () {
        isRanked = !isRanked;
        //$(this).text(isRanked ? 'Rank' : 'Alpha');
        sortTickers();
    });

    // 에러 이미지 처리를 위한 CSS 추가
    $('<style>')
        .text(`
            .error-message {
                color: #FF7F7F;
                padding: 1rem;
                text-align: center;
            }
        `)
        .appendTo('head');

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
