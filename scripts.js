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
                rankedTickers = results.data.filter(row => {
                    return row.Ticker && typeof row.Ticker === 'string' && row.Ticker !== 'undefined' && row.Rank && !isNaN(parseFloat(row.Delta_Previous_Relative_Divergence));
                }).map(row => ({
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
            $('.left-panel').addClass('collapsed'); // 왼쪽 패널 숨기기
            $('.right-panel').addClass('expanded'); // 오른쪽 패널 확장
        });
    }

    async function fetchImagesAndReport(stockTicker) {
        if (!stockTicker) {
            console.error('유효하지 않은 티커:', stockTicker);
            return;
        }
    
        $('#loading').show();
        $('#fixedGraph').empty().html('<canvas id="mainChart"></canvas>');
        $('#reportSection').empty();
    
        try {
            // 데이터 Fetch
            const csvUrl = `https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/result_${stockTicker}.csv`;
            const response = await fetch(csvUrl);
            const csvText = await response.text();
    
            const parsedData = Papa.parse(csvText, {
                header: true,
                dynamicTyping: true,
            }).data;
    
            const normalizedData = normalizeChartData(parsedData, stockTicker);
    
            // 차트 생성
            createChart(stockTicker, normalizedData);
    
            // 리포트 Fetch
            const reportUrl = `https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/report_${stockTicker}.txt`;
            const reportResponse = await fetch(reportUrl);
            if (!reportResponse.ok) {
                throw new Error('리포트를 불러올 수 없습니다.');
            }
            const reportText = await reportResponse.text();
    
            // Markdown 형식의 리포트를 HTML로 변환 후 표시
            $('#reportSection').html(marked.parse(reportText));

        } catch (error) {
            console.error('데이터 로딩 실패:', error);
            $('#reportSection').html('<div class="error-message">데이터를 불러올 수 없습니다.</div>');
        } finally {
            $('#loading').hide();
        }
    }

    // 차트 데이터를 정규화하는 함수
    function normalizeChartData(data, ticker) {
        if (!data.length) return { dates: [], stockData: [], vooData: [] };

        // Use reasonable base values to avoid over-amplification
        const baseValue = data[0][`rate_${ticker}_5D`] || 1; // Avoid small base
        const baseVooValue = data[0]['rate_VOO_20D'] || 1;

        return {
            dates: data.map(row => row.Date),
            stockData: data.map(row => (row[`rate_${ticker}_5D`] - baseValue)), // Absolute change
            vooData: data.map(row => (row['rate_VOO_20D'] - baseVooValue)), // Absolute change
        };
    }
        
    function createChart(stockTicker, chartData) {
        const mainCtx = document.getElementById('mainChart').getContext('2d');
        
        // Y축의 최대/최소값을 자동으로 계산
        const allValues = [...chartData.stockData, ...chartData.vooData];
        const minY = Math.min(...allValues);
        const maxY = Math.max(...allValues);
        const padding = (maxY - minY) * 0.1;
    
        new Chart(mainCtx, {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: stockTicker,
                        data: chartData.stockData,
                        borderColor: 'rgb(0, 255, 255)',  // cyan color
                        backgroundColor: 'rgba(0, 255, 255, 0.1)',
                        borderWidth: 1.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        order: 1
                    },
                    {
                        label: 'VOO',
                        data: chartData.vooData,
                        borderColor: 'rgb(255, 99, 132)',  // pink/red color
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 1.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        order: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    y: {
                        min: minY - padding,
                        max: maxY + padding,
                        position: 'left',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: true
                        },
                        ticks: {
                            color: '#fff',
                            font: {
                                size: 10
                            },
                            callback: function(value) {
                                return value.toFixed(0);
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#fff',
                            font: {
                                size: 10
                            },
                            maxTicksLimit: 6,
                            maxRotation: 0
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#fff',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    const value = context.parsed.y;
                                    label += value.toFixed(2) + '%';
                                }
                                return label;
                            }
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'start',
                        labels: {
                            color: '#fff',
                            font: {
                                size: 12
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    }
                }
            }
        });
    }
    
    
    // 적절한 눈금 간격을 계산하는 헬퍼 함수
    function getNiceNumber(range) {
        const exponent = Math.floor(Math.log10(range));
        const fraction = range / Math.pow(10, exponent);
        let niceFraction;

        if (fraction <= 1.0) niceFraction = 1;
        else if (fraction <= 2) niceFraction = 2;
        else if (fraction <= 5) niceFraction = 5;
        else niceFraction = 10;

        return niceFraction * Math.pow(10, exponent);
    }

    $('#rankAlphaToggle').on('click', function () {
        isRanked = !isRanked;
        sortTickers();
    });

    $('#toggleLeftPanel').on('click', function () {
        $('.left-panel').toggleClass('collapsed');
        $('.right-panel').toggleClass('expanded');
    });

    $('<style>').text(`
        .error-message {
            color: #FF7F7F;
            padding: 1rem;
            text-align: center;
        }
    `).appendTo('head');

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
