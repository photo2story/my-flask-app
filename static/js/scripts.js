$(function() {
    const stockInput = $('#stockName');
    const searchReviewButton = $('#searchReviewButton');
    const reviewList = $('#reviewList');
    const tickerListContainer = $('#ticker-list');
    const searchedTickersContainer = $('#searched-tickers');

    // Markdown 변환 함수 추가
    function convertMarkdown(text) {
        return marked.parse(text);
    }

    function fetchImagesAndReport(stockTicker) {
        const apiUrl = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images';

        $.ajax({
            url: apiUrl,
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                const comparisonFile = data.find(file => file.name === `comparison_${stockTicker}_VOO.png`);
                const resultFile = data.find(file => file.name === `result_mpl_${stockTicker}.png`);
                const reportFile = data.find(file => file.name === `report_${stockTicker}.txt`);

                reviewList.empty();

                if (comparisonFile && resultFile) {
                    reviewList.append(`
                        <div class="review">
                            <h3>${stockTicker} vs VOO</h3>
                            <img src="${comparisonFile.download_url}" alt="${stockTicker} vs VOO" style="width: 100%;">
                            <img src="${resultFile.download_url}" alt="${stockTicker} Result" style="width: 100%; margin-top: 20px;">
                        </div>
                    `);

                    if (reportFile) {
                        $.get(reportFile.download_url, function(data) {
                            // Markdown을 HTML로 변환
                            const htmlContent = convertMarkdown(data);
                            reviewList.append(`<div class="report-content">${htmlContent}</div>`);
                        });
                    }
                    alert(`Successfully fetched review for ${stockTicker}.`);
                } else {
                    alert(`Unable to find images for the stock ticker ${stockTicker}.`);
                    saveSearchedTicker(stockTicker);
                    displaySearchedTickers();
                }
            },
            error: function() {
                alert('Error occurred while fetching images.');
            }
        });
    }

    function saveSearchedTicker(ticker) {
        let searchedTickers = JSON.parse(localStorage.getItem('searchedTickers')) || {};
        if (searchedTickers[ticker]) {
            searchedTickers[ticker]++;
        } else {
            searchedTickers[ticker] = 1;
        }
        localStorage.setItem('searchedTickers', JSON.stringify(searchedTickers));
    }

    function displaySearchedTickers() {
        let searchedTickers = JSON.parse(localStorage.getItem('searchedTickers')) || {};
        searchedTickersContainer.empty();
        searchedTickersContainer.append('<h2>Searched Stocks</h2>');
        for (let ticker in searchedTickers) {
            searchedTickersContainer.append(`<span class="ticker-item">${ticker} (${searchedTickers[ticker]})</span>`);
        }
    }

    function loadTickerList() {
        const apiUrl = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images';

        $.ajax({
            url: apiUrl,
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                const tickers = data
                    .filter(file => file.name.startsWith('comparison_') && file.name.endsWith('_VOO.png'))
                    .map(file => file.name.replace('comparison_', '').replace('_VOO.png', ''))
                    .sort();

                tickerListContainer.empty();

                tickers.forEach(ticker => {
                    tickerListContainer.append(`<span class="ticker-item">${ticker}</span>`);
                });

                $('.ticker-item').on('click', function() {
                    const stockTicker = $(this).text();
                    stockInput.val(stockTicker);
                    fetchImagesAndReport(stockTicker);
                });
            },
            error: function() {
                alert('Error occurred while loading ticker list.');
            }
        });
    }

    searchReviewButton.click(function() {
        const stockTicker = stockInput.val().toUpperCase();
        if (stockTicker) {
            fetchImagesAndReport(stockTicker);
        }
    });

    stockInput.on('keypress', function(e) {
        if (e.which === 13) { // Enter key
            searchReviewButton.click();
            return false;
        }
    });

    loadTickerList();
    displaySearchedTickers();
});