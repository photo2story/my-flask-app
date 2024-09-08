import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:photo_view/photo_view.dart';
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
  String _message = '';
  String _reportText = '';
  List<String> _tickers = []; // 스탁 리스트 저장할 리스트
  final TextEditingController _controller = TextEditingController();

  final String apiUrl = 'http://192.168.0.5:5000/api';

  @override
  void initState() {
    super.initState();
    fetchReviewedTickers(); // 주식 목록을 불러오는 함수 호출
  }

  // 서버에서 스탁 리스트 불러오는 함수
  Future<void> fetchReviewedTickers() async {
    try {
      print('Fetching reviewed tickers from: $apiUrl/get_reviewed_tickers');
      final response = await http.get(Uri.parse('$apiUrl/get_reviewed_tickers'));
      print('Response status for tickers: ${response.statusCode}');
      if (response.statusCode == 200) {
        final List<dynamic> tickers = json.decode(response.body);
        print('Fetched tickers: $tickers');
        setState(() {
          _tickers = tickers.cast<String>();
          print('State updated with tickers: $_tickers');
        });
      } else {
        setState(() {
          _message = 'Error occurred while fetching tickers: ${response.statusCode}';
          print(_message);
        });
      }
    } catch (e) {
      setState(() {
        _message = 'Error occurred while fetching tickers: $e';
        print(_message);
      });
    }
  }

  // 서버에서 이미지 및 리포트 불러오는 함수
  Future<void> fetchImagesAndReport(String stockTicker) async {
    try {
      print('Fetching images and report for ticker: $stockTicker');
      final response = await http.get(Uri.parse('$apiUrl/get_images?ticker=$stockTicker'));
      print('Response status for images and report: ${response.statusCode}');
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        print('Fetched data: $data');

        // 절대 경로로 변환 (이미지 URL이 상대 경로로 왔을 경우)
        String comparisonImageUrl = data['comparison_image'] ?? '';
        if (comparisonImageUrl.isNotEmpty && !comparisonImageUrl.startsWith('http')) {
          comparisonImageUrl = 'http://192.168.0.5:5000$comparisonImageUrl';
        }

        String resultImageUrl = data['result_image'] ?? '';
        if (resultImageUrl.isNotEmpty && !resultImageUrl.startsWith('http')) {
          resultImageUrl = 'http://192.168.0.5:5000$resultImageUrl';
        }

        setState(() {
          _comparisonImageUrl = comparisonImageUrl;
          _resultImageUrl = resultImageUrl;
          _reportText = data['report'] ?? '';
          _message = '';
          print('State updated with images and report');
        });
      } else {
        setState(() {
          _comparisonImageUrl = '';
          _resultImageUrl = '';
          _reportText = '';
          _message = 'Failed to fetch images and report: ${response.statusCode}';
          print(_message);
        });
      }
    } catch (e) {
      setState(() {
        _comparisonImageUrl = '';
        _resultImageUrl = '';
        _reportText = '';
        _message = 'Error occurred: $e';
        print(_message);
      });
    }
  }

  // 이미지 클릭 시 확대해서 보여주는 함수
  void _openImage(BuildContext context, String imageUrl) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ImageScreen(imageUrl: imageUrl),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Stock Comparison Review'),
      ),
      body: Center(
        child: SingleChildScrollView(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              // 주식 목록을 상단에 표시하는 부분
              Container(
                padding: const EdgeInsets.all(8.0),
                child: Text(
                  'Reviewed Stocks:',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
              Wrap(
                children: _tickers.map((ticker) {
                  return Padding(
                    padding: const EdgeInsets.all(4.0),
                    child: GestureDetector(
                      onTap: () {
                        print('Ticker clicked: $ticker');
                        fetchImagesAndReport(ticker);
                      },
                      child: Text(
                        ticker,
                        style: TextStyle(fontSize: 14, color: Colors.blue),
                      ),
                    ),
                  );
                }).toList(),
              ),
              SizedBox(height: 20),

              // 기본 이미지를 화면에 표시
              Text(
                'Stock Comparison',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 20),
              GestureDetector(
                onTap: () => _openImage(context, _comparisonImageUrl),
                child: Image.network(
                  _comparisonImageUrl.isNotEmpty
                      ? _comparisonImageUrl
                      : 'http://192.168.0.5:5000/static/images/comparison_AAPL_VOO.png',
                  errorBuilder: (context, error, stackTrace) {
                    return Text('Failed to load comparison image');
                  },
                ),
              ),
              SizedBox(height: 20),

              // 리포트 및 결과 이미지를 표시하는 부분
              _resultImageUrl.isNotEmpty
                  ? GestureDetector(
                      onTap: () => _openImage(context, _resultImageUrl),
                      child: Image.network(
                        _resultImageUrl,
                        errorBuilder: (context, error, stackTrace) {
                          return Text('Failed to load result image');
                        },
                      ),
                    )
                  : Container(),
              SizedBox(height: 20),
              _reportText.isNotEmpty
                  ? Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: MarkdownBody(
                        data: _reportText,
                      ),
                    )
                  : Container(),
              _message.isNotEmpty
                  ? Text(
                      _message,
                      style: TextStyle(fontSize: 16, color: Colors.red),
                    )
                  : Container(),
            ],
          ),
        ),
      ),
    );
  }
}

// 이미지를 클릭했을 때 보여주는 확대 화면
class ImageScreen extends StatelessWidget {
  final String imageUrl;

  ImageScreen({required this.imageUrl});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Image Preview'),
      ),
      body: Center(
        child: PhotoView(
          imageProvider: NetworkImage(imageUrl),
          errorBuilder: (context, error, stackTrace) {
            return Text('Failed to load image');
          },
        ),
      ),
    );
  }
}
