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
                    return row.Ticker && typeof row.Ticker === 'string' && 
                           row.Ticker !== 'undefined' && row.Rank && 
                           !isNaN(parseFloat(row.Delta_Previous_Relative_Divergence));
                }).map(row => ({
                    rank: parseInt(row.Rank),
                    ticker: row.Ticker,
                    delta_previous_relative_divergence: parseFloat(row.Delta_Previous_Relative_Divergence),
                    totalReturn: parseFloat(row.Total_Return),
                    divergence: parseFloat(row.Divergence),
                    relativeDivergence: parseFloat(row.Relative_Divergence),
                    maxDivergence: parseFloat(row.Max_Divergence),
                    minDivergence: parseFloat(row.Min_Divergence),
                    expectedReturn: parseFloat(row.Expected_Return),
                    dynamicExpectedReturn: parseFloat(row.Dynamic_Expected_Return)
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
        $('#fixedGraph').empty().html('<canvas id="mainChart" style="background-color: white;"></canvas>');
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
    
            // 차트 데이터 정규화
            const normalizedData = normalizeChartData(parsedData, stockTicker);
            
            // 현재 티커의 데이터 찾기
            const tickerData = rankedTickers.find(t => t.ticker === stockTicker);
            if (!tickerData) {
                throw new Error('티커 데이터를 찾을 수 없습니다.');
            }
            
            // 차트 데이터 준비
            const chartData = {
                ...normalizedData,
                tickerData: tickerData  // tickerData를 chartData에 포함
            };
    
            // 차트 생성 시 tickerData 전달
            createChart(stockTicker, chartData);
    
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

    function updateHeader(ticker, data) {
        $('#header').html(`
            <h1>${ticker} vs VOO</h1>
            <p>Total Rate: ${data.totalReturn}% (VOO: ${data.vooTotalReturn}%), Relative Divergence: ${data.relativeDivergence}%</p>
            <p>Current Divergence: ${data.delta}% (max: ${data.maxDivergence}, min: ${data.minDivergence})</p>
            <p>Expected Return: ${data.expectedReturn}%</p>
        `);
    }

    
    function createChart(stockTicker, chartData) {
        const mainCtx = document.getElementById('mainChart').getContext('2d');
        const tickerData = chartData.tickerData;
        
        new Chart(mainCtx, {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: stockTicker,
                        data: chartData.stockData,
                        borderColor: '#00BCD4',
                        backgroundColor: 'rgba(0, 188, 212, 0.2)',
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
                        borderColor: '#FF4081',
                        backgroundColor: 'rgba(255, 64, 129, 0.2)',
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
                plugins: {
                    title: {
                        display: true,
                        text: [
                            `${stockTicker} vs VOO`
                        ],
                        font: {
                            size: 15,
                            weight: 'bold'
                        },
                        color: '#000',
                        padding: {
                            top: 10,
                            bottom: 5
                        }
                    },
                    subtitle: {
                        display: true,
                        text: [
                            `Total Rate: ${tickerData.totalReturn.toFixed(2)}%, Relative Divergence: ${tickerData.relativeDivergence.toFixed(2)}%`,
                            `Current Divergence: ${tickerData.divergence.toFixed(2)}% (max: ${tickerData.maxDivergence.toFixed(2)}, min: ${tickerData.minDivergence.toFixed(2)})`,
                            `Expected Return: ${tickerData.expectedReturn.toFixed(2)}% (dynamic: ${tickerData.dynamicExpectedReturn.toFixed(2)}%), Recent Signal (Delta_Divergence): ${tickerData.delta_previous_relative_divergence.toFixed(2)}%`
                        ],
                        font: {
                            size: 10,
                            weight: 'bold'
                        },
                        color: '#000',
                        padding: {
                            top: 0,
                            bottom: 5
                        }
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(20, 64, 64, 0.9)',  // 진한 회색으로 변경
                        titleColor: '#fff',  // 흰색으로 변경
                        bodyColor: '#fff',   // 흰색으로 변경
                        borderWidth: 0,
                        padding: 8,
                        titleFont: {
                            size: 10
                        },
                        bodyFont: {
                            size: 10
                        },
                        displayColors: true,
                        boxWidth: 8,
                        boxHeight: 8,
                        usePointStyle: true,
                        position: 'nearest',
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].label;
                            },
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(2) + '%';
                                }
                                return label;
                            }
                        }
                    },
                    filler: {
                        propagate: true
                    }
                },
                hover: {
                    mode: 'index',
                    intersect: false
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#000',
                            maxTicksLimit: 8,
                            maxRotation: 0,
                            minRotation: 0,
                            font: {
                                size: 10
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#000',
                            font: {
                                size: 8
                            }
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
