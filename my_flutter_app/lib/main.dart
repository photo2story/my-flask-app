import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:photo_view/photo_view.dart';  // 추가
import 'package:photo_view/photo_view_gallery.dart'; // 여러 이미지일 경우
import 'package:csv/csv.dart'; // CSV 패키지 추가

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  // 앱의 기본 테마와 라우팅을 설정합니다.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Stock Comparison Review',
      theme: ThemeData(
        brightness: Brightness.dark, // 다크 테마 적용
        primarySwatch: Colors.blueGrey,
        scaffoldBackgroundColor: Colors.black, // 배경색을 검은색으로 설정
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.grey[900], // AppBar 배경색 설정
        ),
      ),
      home: MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  // 메인 페이지의 상태를 관리하는 위젯입니다.
  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  // 상태 변수들을 선언합니다.
  String _comparisonImageUrl = '';
  String _resultImageUrl = '';
  String _reportText = '';
  List<String> _tickers = [];
  List<Map<String, dynamic>> _tickersWithReturns = []; // CSV에서 가져온 티커 목록과 Rank 값
  bool _isLoading = false;
  late String _selectedTicker; // null safety를 위해 late 키워드 사용

  bool _isRanked = true; // true면 랭킹 순서, false면 알파벳 순서

  final String apiUrl = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images';

  @override
  void initState() {
    super.initState();
    fetchReviewedTickers();
  }

  Future<void> fetchReviewedTickers() async {
    try {
      // API URL 호출
      final response = await http.get(Uri.parse(apiUrl));
      if (response.statusCode == 200) {
        final List<dynamic> files = json.decode(response.body);

        // 비교 이미지를 포함한 파일에서 티커를 추출 (대문자로 변환)
        final tickersFromFiles = files
            .where((file) => file['name'].startsWith('comparison_') && file['name'].endsWith('_VOO.png'))
            .map<String>((file) => file['name'].replaceAll('comparison_', '').replaceAll('_VOO.png', '').toUpperCase())
            .toList();

        // CSV 파일 다운로드 및 수동 파싱
        final csvResponse = await http.get(Uri.parse('https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images/results_relative_divergence.csv'));
        if (csvResponse.statusCode == 200) {
          final csvString = csvResponse.body;

          // CSV 파일을 줄 단위로 분리하여 수동 파싱
          List<String> rows = csvString.split('\n');

          List<Map<String, dynamic>> tickersWithReturns = [];
          for (int i = 1; i < rows.length; i++) {
            // 각 행을 ','로 구분하여 배열로 만듦
            List<String> columns = rows[i].split(',');

            if (columns.length > 1) {
              String rank = columns[0].trim();  // Rank 값을 문자열로 처리
              String ticker = columns[1].trim();  // Ticker 값을 문자열로 처리

              // 데이터를 리스트에 추가
              tickersWithReturns.add({'rank': rank, 'ticker': ticker.toUpperCase()});
            } else {
              print('Skipping empty or malformed row: ${rows[i]}');
            }
          }

          print('Tickers from CSV: $tickersWithReturns');

          // 상태 업데이트 (리스트 및 정렬)
          setState(() {
            _tickers = tickersFromFiles;  // 파일에서 추출한 티커 목록
            _tickersWithReturns = tickersWithReturns;  // CSV에서 추출한 티커와 Rank 목록
            _sortTickers();  // 정렬 함수 호출
            if (_tickers.isNotEmpty) {
              _selectedTicker = _tickers.first.split(':').last.toUpperCase();
              fetchImagesAndReport(_selectedTicker);
            }
          });
        } else {
          // CSV 파일을 가져오지 못한 경우 파일에서 추출한 티커 목록만 사용
          setState(() {
            _tickers = tickersFromFiles;
            _sortTickers();  // 정렬 함수 호출
            if (_tickers.isNotEmpty) {
              _selectedTicker = _tickers.first.split(':').last.toUpperCase();
              fetchImagesAndReport(_selectedTicker);
            }
          });
        }
      } else {
        // API 호출 실패 시 에러 메시지 설정
        setState(() {
          _comparisonImageUrl = '';
          _resultImageUrl = '';
          _reportText = 'Error occurred while fetching tickers: ${response.statusCode}';
        });
      }
    } catch (e) {
      // 예외 발생 시 에러 메시지 설정
      setState(() {
        _comparisonImageUrl = '';
        _resultImageUrl = '';
        _reportText = 'Error occurred while fetching tickers: $e';
      });
    }
  }



void _sortTickers() {
  setState(() {
    if (_isRanked) {
      // 랭킹 순서로 정렬
      List<Map<String, dynamic>> sortedTickersWithReturns = _tickersWithReturns
          .where((item) => _tickers.contains(item['ticker']))
          .toList();

      sortedTickersWithReturns.sort((a, b) {
        final aTicker = a['ticker'];
        final bTicker = b['ticker'];

        final isANumeric = RegExp(r'^\d+$').hasMatch(aTicker);
        final isBNumeric = RegExp(r'^\d+$').hasMatch(bTicker);

        if (isANumeric && isBNumeric) {
          return int.parse(aTicker).compareTo(int.parse(bTicker));
        } else if (isANumeric) {
          return -1;
        } else if (isBNumeric) {
          return 1;
        } else {
          return aTicker.compareTo(bTicker);
        }
      });

      List<String> sortedTickers = sortedTickersWithReturns.map<String>((item) => '${item['rank']}:${item['ticker']}').toList();
      List<String> remainingTickers = _tickers.where((ticker) => !_tickersWithReturns.any((item) => item['ticker'] == ticker)).toList();
      remainingTickers.sort();

      _tickers = [...sortedTickers, ...remainingTickers];
    } else {
      // Alpha 순서로 정렬: 티커에서 랭킹 번호를 제거하고 알파벳 순으로 정렬
      _tickers = _tickers.map((ticker) {
        if (ticker.contains(':')) {
          return ticker.split(':').last;  // 'rank:ticker' 형식에서 ticker만 추출
        }
        return ticker;
      }).toList();

      // 알파벳 순서로 정렬
      _tickers.sort((a, b) => a.compareTo(b));
    }

    print('Tickers sorted: $_tickers');

    // 상태 업데이트로 UI 갱신
    setState(() {
      // 티커 리스트가 갱신되어 UI에 반영됨
    });
  });
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
            (file) => file['name'].toUpperCase() == 'RESULT_MPL_${stockTicker}.PNG',
            orElse: () => null);
        final reportFile = files.firstWhere(
            (file) => file['name'].toUpperCase() == 'REPORT_${stockTicker}.TXT',
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
            _reportText = ''; // 리포트가 없는 경우
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

  // 이미지를 클릭하면 별도 페이지에서 확대/축소 가능하게 보여주는 함수
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
              backgroundDecoration: BoxDecoration(color: Colors.black), // 배경색을 검은색으로
            ),
          ),
        ),
      ),
    );
  }

  // UI를 구성하는 위젯을 빌드합니다.
@override
Widget build(BuildContext context) {
  return Scaffold(
    appBar: AppBar(
      title: Text('Stock Comparison Review'),
    ),
    body: InteractiveViewer(
      boundaryMargin: EdgeInsets.all(8),
      minScale: 0.5,
      maxScale: 3.0,
      child: Row(
        children: <Widget>[
          // 왼쪽 패널: 티커 리스트 및 정렬 옵션
          Container(
            width: MediaQuery.of(context).size.width * 0.15,
            padding: const EdgeInsets.all(8.0),
            color: Colors.grey[900],
            child: Column(
              children: [
                // 정렬 옵션 버튼
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    GestureDetector(
                      onTap: () {
                        setState(() {
                          _isRanked = true;
                          _sortTickers();
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
                          _sortTickers();
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
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2.0),
                        child: GestureDetector(
                          onTap: () {
                            setState(() {
                              _selectedTicker = ticker;
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
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      children: [
                        _resultImageUrl.isNotEmpty
                            ? GestureDetector(
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
                              )
                            : Container(),
                        _reportText.isNotEmpty
                            ? Padding(
                                padding: const EdgeInsets.all(8.0),
                                child: MarkdownBody(
                                  data: _reportText,
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
    ),
  );
}  // <-- 여기서 빌드 함수 끝나고
}  // <-- 여기서 _MyHomePageState 클래스 끝나는 중괄호 추가

// flutter devices

// flutter run -d R3CX404VPHE

// flutter run -d chrome