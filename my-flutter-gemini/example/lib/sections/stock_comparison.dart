import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_gemini/flutter_gemini.dart';  // 번역을 위한 Gemini 사용
import 'package:photo_view/photo_view.dart';  // 이미지 확대/축소 기능

class StockComparison extends StatefulWidget {
  @override
  _StockComparisonState createState() => _StockComparisonState();
}

class _StockComparisonState extends State<StockComparison> {
  String _comparisonImageUrl = '';  // 비교 그래프 이미지 URL
  String _resultImageUrl = '';      // 분석 결과 이미지 URL
  String _reportText = '';          // 리포트 원본 텍스트
  bool _isLoading = false;          // 로딩 상태를 나타내는 변수
  List<String> _tickers = [];       // 티커 리스트
  List<Map<String, dynamic>> _tickersWithReturns = []; // CSV에서 가져온 티커 목록과 Rank 값
  bool _isRanked = true;            // true면 랭킹 순서, false면 알파벳 순서
  String _selectedTicker = "AAPL";  // 기본 선택된 티커
  final TextEditingController _controller = TextEditingController();  // 티커 입력 필드 컨트롤러
  final List<Content> _chats = [];  // 번역된 텍스트를 저장할 리스트
  final gemini = Gemini.instance;   // Gemini 객체

  final String apiUrl = 'https://api.github.com/repos/photo2story/my-flask-app/contents/static/images';

  @override
  void initState() {
    super.initState();
    fetchReviewedTickers();
    fetchImagesAndReport(_selectedTicker);  // 앱 실행 시 AAPL 주식 데이터를 기본으로 불러옴
  }

  // GitHub에서 사용 가능한 티커 리스트를 가져오는 함수
  Future<void> fetchReviewedTickers() async {
    try {
      final response = await http.get(Uri.parse(apiUrl));
      if (response.statusCode == 200) {
        final List<dynamic> files = json.decode(response.body);
        final tickersFromFiles = files
            .where((file) => file['name'].startsWith('comparison_') && file['name'].endsWith('_VOO.png'))
            .map<String>((file) => file['name'].replaceAll('comparison_', '').replaceAll('_VOO.png', ''))
            .toList();

        // CSV 파일 다운로드 및 수동 파싱
        final csvResponse = await http.get(Uri.parse('https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/results_relative_divergence.csv'));
        if (csvResponse.statusCode == 200) {
          final csvString = csvResponse.body;
          List<String> rows = csvString.split('\n');

          List<Map<String, dynamic>> tickersWithReturns = [];
          for (int i = 1; i < rows.length; i++) {
            List<String> columns = rows[i].split(',');
            if (columns.length > 1) {
              String rank = columns[0].trim();
              String ticker = columns[1].trim();
              tickersWithReturns.add({'rank': rank, 'ticker': ticker});
            }
          }

          setState(() {
            _tickers = tickersFromFiles;
            _tickersWithReturns = tickersWithReturns;
            _sortTickers();  // 정렬 함수 호출
          });
        }
      } else {
        setState(() {
          _reportText = 'Error occurred while fetching tickers: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _reportText = 'Error occurred while fetching tickers: $e';
      });
    }
  }

  // 랭킹 또는 알파벳 순으로 티커 정렬
  void _sortTickers() {
    setState(() {
      if (_isRanked) {
        // 랭킹 순서로 정렬
        List<Map<String, dynamic>> sortedTickersWithReturns = _tickersWithReturns
            .where((item) => _tickers.contains(item['ticker'].toString()))  // String으로 변환
            .toList();
        
        sortedTickersWithReturns.sort((a, b) {
          int rankA = int.tryParse(a['rank']) ?? 0;
          int rankB = int.tryParse(b['rank']) ?? 0;
          return rankA.compareTo(rankB);  // 랭크 순서대로 정렬
        });

        _tickers = sortedTickersWithReturns.map<String>((item) => '${item['rank']}:${item['ticker'].toString()}').toList();  // String으로 변환
      } else {
        // 알파벳 순으로 정렬, rank 정보 제거
        _tickers = _tickersWithReturns.map((item) => item['ticker'].toString()).toList();  // String으로 변환
        _tickers.sort((a, b) => a.compareTo(b));  // 알파벳 순으로 정렬
      }

      // 상태 업데이트
      print('Tickers sorted: $_tickers');
    });
  }



  // 티커를 입력 받아 이미지 및 리포트 데이터를 가져오는 함수
  Future<void> fetchImagesAndReport(String stockTicker) async {
    // 이전 요청이 처리 중일 때 취소하거나 새 요청으로 대체
    if (_isLoading) {
      print('Previous request is still loading, cancelling it.');
      return;  // 이전 요청을 취소하고 새 요청이 처리되도록 함
    }

    setState(() {
      _isLoading = true;
      _comparisonImageUrl = 'https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/comparison_${stockTicker}_VOO.png';
      _resultImageUrl = '';
      _reportText = '';
    });

    try {
      final response = await http.get(Uri.parse(apiUrl));
      if (response.statusCode == 200) {
        final List<dynamic> files = json.decode(response.body);
        final resultFile = files.firstWhere(
            (file) => file['name'] == 'result_mpl_${stockTicker}.png',
            orElse: () => null);
        final reportFile = files.firstWhere(
            (file) => file['name'] == 'report_${stockTicker}.txt',
            orElse: () => null);

        if (resultFile != null) {
          setState(() {
            _resultImageUrl = resultFile['download_url'];
          });
        }

        if (reportFile != null) {
          final reportResponse = await http.get(Uri.parse(reportFile['download_url']));
          if (reportResponse.statusCode == 200) {
            setState(() {
              _chats.clear();
              _chats.add(Content(role: 'user', parts: [Parts(text: '한글로 번역해줘')]));  // 번역 요청
              _chats.add(Content(role: 'user', parts: [Parts(text: reportResponse.body)]));  // 리포트 원본 텍스트
            });

            await gemini.chat(_chats).then((value) {
              setState(() {
                _chats.add(Content(role: 'model', parts: [Parts(text: value?.output)]));  // 번역된 텍스트
                _isLoading = false;
              });
            });
          }
        } else {
          setState(() {
            _reportText = 'No report found for $stockTicker.';
            _isLoading = false;
          });
        }
      } else {
        setState(() {
          _reportText = 'GitHub API call failed: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _reportText = 'Error occurred: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }


  // 이미지를 클릭하면 별도의 페이지에서 확대해서 보여주는 함수
  void _openImageInNewScreen(String imageUrl) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => Scaffold(
          appBar: AppBar(
            title: Text('Zoomable Image'),
          ),
          body: Center(
            child: PhotoView(
              imageProvider: NetworkImage(imageUrl),
              backgroundDecoration: BoxDecoration(color: Colors.black),
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: <Widget>[
          // 왼쪽 패널: 티커 리스트 및 정렬 옵션
          Container(
            width: MediaQuery.of(context).size.width * 0.20,  // 크기 조정
            padding: const EdgeInsets.all(8.0),
            color: Colors.grey[900],
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    GestureDetector(
                      onTap: () {
                        setState(() {
                          _isRanked = true;
                          _sortTickers();  // 랭킹 정렬
                        });
                      },
                      child: Text(
                        'Rank',
                        style: TextStyle(
                          fontSize: 11,
                          color: _isRanked ? Colors.white : Colors.grey,
                        ),
                      ),
                    ),
                    GestureDetector(
                      onTap: () {
                        setState(() {
                          _isRanked = false;
                          _sortTickers();  // 알파벳 정렬
                        });
                      },
                      child: Text(
                        'Alpha',
                        style: TextStyle(
                          fontSize: 11,
                          color: !_isRanked ? Colors.white : Colors.grey,
                        ),
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 8),
                Expanded(
                  child: ListView(
                    children: _tickers.map((ticker) {
                      String actualTicker = ticker.contains(':') ? ticker.split(':').last : ticker;
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2.0),
                        child: GestureDetector(
                          onTap: () {
                            setState(() {
                              _selectedTicker = actualTicker;
                            });
                            fetchImagesAndReport(_selectedTicker);
                          },
                          child: Text(
                            ticker,
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.cyanAccent,
                              height: 1.2,
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),
          ),

          // 오른쪽 패널: 상단 - 고정 이미지, 하단 - 리포트 및 번역된 텍스트
          Expanded(
            child: Column(
              children: [
                if (_isLoading)
                  Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: CircularProgressIndicator(),
                  ),
                _comparisonImageUrl.isNotEmpty
                    ? GestureDetector(
                        onTap: () {
                          _openImageInNewScreen(_comparisonImageUrl);
                        },
                        child: Container(
                          padding: const EdgeInsets.all(8.0),
                          height: 250,
                          child: Image.network(
                            _comparisonImageUrl,
                            errorBuilder: (context, error, stackTrace) {
                              return Text('Failed to load comparison image');
                            },
                          ),
                        ),
                      )
                    : Container(),

                // 분석 결과 이미지 및 리포트
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      children: [
                        if (_resultImageUrl.isNotEmpty)
                          GestureDetector(
                            onTap: () {
                              _openImageInNewScreen(_resultImageUrl);
                            },
                            child: Container(
                              padding: const EdgeInsets.all(8.0),
                              height: 250,
                              child: Image.network(
                                _resultImageUrl,
                                fit: BoxFit.contain,
                                errorBuilder: (context, error, stackTrace) {
                                  return Text('Failed to load result image');
                                },
                              ),
                            ),
                          ),

                        // 번역된 텍스트 출력
                        _chats.isNotEmpty
                            ? Padding(
                                padding: const EdgeInsets.all(8.0),
                                child: MarkdownBody(
                                  data: _chats.last.parts?.lastOrNull?.text ?? 'Cannot generate data!',
                                  styleSheet: MarkdownStyleSheet(
                                    p: TextStyle(color: Colors.white70),
                                  ),
                                ),
                              )
                            : Container(),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

