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
  String _selectedTicker = "AAPL";  // 기본 선택된 티커
  final TextEditingController _controller = TextEditingController();  // 티커 입력 필드 컨트롤러
  final List<Content> _chats = [];  // 번역된 텍스트를 저장할 리스트
  final gemini = Gemini.instance;   // Gemini 객체
  
  final String apiUrl = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images';

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
        final tickers = files
            .where((file) => file['name'].startsWith('comparison_') && file['name'].endsWith('_VOO.png'))
            .map<String>((file) => file['name'].replaceAll('comparison_', '').replaceAll('_VOO.png', ''))
            .toList();

        setState(() {
          _tickers = tickers;
        });
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

  // 티커를 입력 받아 이미지 및 리포트 데이터를 가져오는 함수
  Future<void> fetchImagesAndReport(String stockTicker) async {
    setState(() {
      _isLoading = true;
      _comparisonImageUrl = 'https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images/comparison_${stockTicker}_VOO.png';
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

        // 결과 이미지 URL 설정
        if (resultFile != null) {
          setState(() {
            _resultImageUrl = resultFile['download_url'];
          });
        }

        // 영어 리포트 번역 기능 추가
        if (reportFile != null) {
          final reportResponse = await http.get(Uri.parse(reportFile['download_url']));
          if (reportResponse.statusCode == 200) {
            setState(() {
              _chats.clear();
              _chats.add(Content(role: 'user', parts: [Parts(text: '한글로 번역해줘')]));  // 번역 요청
              _chats.add(Content(role: 'user', parts: [Parts(text: reportResponse.body)]));  // 리포트 원본 텍스트
            });

            // Gemini API를 통해 번역 요청
            gemini.chat(_chats).then((value) {
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
      // appBar: AppBar(
      //   title: Text('Stock Comparison Review'),
      // ),
      body: Row(
        children: <Widget>[
          // 왼쪽 패널: 티커 리스트
          Container(
            width: MediaQuery.of(context).size.width * 0.15,
            padding: const EdgeInsets.all(8.0),
            color: Colors.grey[900],
            child: ListView(
              children: _tickers.map((ticker) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2.0),
                  child: GestureDetector(
                    onTap: () {
                      setState(() {
                        _selectedTicker = ticker;
                      });
                      fetchImagesAndReport(ticker);  // 선택된 티커로 데이터 불러오기
                    },
                    child: Text(
                      ticker,
                      style: TextStyle(fontSize: 11, color: Colors.cyanAccent, height: 1.2),
                    ),
                  ),
                );
              }).toList(),
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
