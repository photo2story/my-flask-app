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
            const displayText = isRanked ? `${rank}:${tickerName}` : `${tickerName}`;

            $('#tickerList').append(
                `<div class="ticker-item" data-ticker="${tickerName}">
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

        // 이미지 클릭 시 새 창에서 보기 기능 추가
        enableImageZoom();

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

    // 이미지 확대 기능 추가
    function enableImageZoom() {
        $('.zoomable-image').off('click').on('click', function () {
            const imageUrl = $(this).attr('src');
            window.open(imageUrl, '_blank', 'width=800,height=600'); // 새 창에서 이미지 보기
        });
    }

    $('#rankAlphaToggle').on('click', function () {
        isRanked = !isRanked;
        $(this).text(isRanked ? 'Rank' : 'Alpha');
        sortTickers();
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

    fetchCSV();
});
