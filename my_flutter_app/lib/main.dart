import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_markdown/flutter_markdown.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Stock Comparison Review',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  String _comparisonImageUrl = '';
  String _resultImageUrl = '';
  String _reportText = '';
  List<String> _tickers = [];
  bool _isLoading = false;
  String _selectedTicker = "AAPL"; // 기본 값으로 Apple 주식 티커 설정
  final TextEditingController _controller = TextEditingController();

  final String apiUrl = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images';

  @override
  void initState() {
    super.initState();
    fetchReviewedTickers();
    fetchImagesAndReport(_selectedTicker); // 앱이 시작될 때 AAPL 주식 데이터를 불러옴
  }

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
          _comparisonImageUrl = '';
          _resultImageUrl = '';
          _reportText = 'Error occurred while fetching tickers: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _comparisonImageUrl = '';
        _resultImageUrl = '';
        _reportText = 'Error occurred while fetching tickers: $e';
      });
    }
  }

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

        if (resultFile != null) {
          setState(() {
            _resultImageUrl = resultFile['download_url'];
          });
        }

        if (reportFile != null) {
          final reportResponse = await http.get(Uri.parse(reportFile['download_url']));
          if (reportResponse.statusCode == 200) {
            setState(() {
              _reportText = reportResponse.body;
            });
          } else {
            setState(() {
              _reportText = 'Failed to load report text';
            });
          }
        } else {
          setState(() {
            _reportText = ''; // Clear the report text if no report is found
          });
        }
      } else {
        setState(() {
          _resultImageUrl = '';
          _reportText = 'GitHub API call failed: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _resultImageUrl = '';
        _reportText = 'Error occurred: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Stock Comparison Review'),
      ),
      body: InteractiveViewer( // 전체 화면에 적용
        boundaryMargin: EdgeInsets.all(8),
        minScale: 0.5,
        maxScale: 3.0,
        child: Row(
          children: <Widget>[
            // 왼쪽 패널: 티커 리스트
            Container(
              width: MediaQuery.of(context).size.width * 0.15,
              padding: const EdgeInsets.all(8.0),
              color: Colors.grey[200],
              child: ListView(
                children: _tickers.map((ticker) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2.0),
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          _selectedTicker = ticker;
                        });
                        fetchImagesAndReport(ticker);
                      },
                      child: Text(
                        ticker,
                        style: TextStyle(fontSize: 11, color: Colors.blue, height: 1.2),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),

            // 오른쪽 패널: 상단 - 고정 이미지, 하단 - 결과 이미지 및 리포트
            Expanded(
              child: Column(
                children: [
                  // 로딩 중 표시
                  if (_isLoading)
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: CircularProgressIndicator(),
                    ),

                  // 고정된 comparison_${stockTicker}_VOO.png 이미지
                  _comparisonImageUrl.isNotEmpty
                      ? Container(
                          padding: const EdgeInsets.all(8.0),
                          height: 230, // 고정 크기 설정
                          child: Image.network(
                            _comparisonImageUrl,
                            errorBuilder: (context, error, stackTrace) {
                              return Text('Failed to load comparison image');
                            },
                          ),
                        )
                      : Container(),

                  Expanded(
                    child: SingleChildScrollView(
                      child: Column(
                        children: [
                          // 스크롤 가능한 result_mpl_${stockTicker}.png 이미지
                          _resultImageUrl.isNotEmpty
                              ? Container(
                                  padding: const EdgeInsets.all(8.0),
                                  child: Image.network(
                                    _resultImageUrl,
                                    errorBuilder: (context, error, stackTrace) {
                                      return Text('Failed to load result image');
                                    },
                                  ),
                                )
                              : Container(),

                          // 리포트 텍스트
                          _reportText.isNotEmpty
                              ? Padding(
                                  padding: const EdgeInsets.all(8.0),
                                  child: MarkdownBody(
                                    data: _reportText,
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
      ),
    );
  }
}


// flutter devices

// flutter run -d R3CX404VPHE

// flutter run -d chrome