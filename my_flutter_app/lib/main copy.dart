import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_gemini/flutter_gemini.dart';


void main() async {
  // API 키와 디버그 모드 초기화
  Gemini.init(
    apiKey: const String.fromEnvironment('apiKey'),
    enableDebugging: true,
  );

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

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
  const MyHomePage({super.key});

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  String _comparisonImageUrl = '';
  String _resultImageUrl = '';
  String _reportText = '';
  String _message = '';
  List<String> _tickers = [];
  final List<Map<String, String>> _messages = [];
  final TextEditingController _controller = TextEditingController();

  final String apiUrl = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images';

  @override
  void initState() {
    super.initState();
    fetchReviewedTickers();
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
          _message = 'Error occurred while fetching tickers: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _message = 'Error occurred while fetching tickers: $e';
      });
    }
  }

  Future<void> fetchImagesAndReport(String stockTicker) async {
    try {
      final response = await http.get(Uri.parse(apiUrl));
      if (response.statusCode == 200) {
        final List<dynamic> files = json.decode(response.body);
        final comparisonFile = files.firstWhere(
            (file) => file['name'] == 'comparison_${stockTicker}_VOO.png',
            orElse: () => null);
        final resultFile = files.firstWhere(
            (file) => file['name'] == 'result_mpl_${stockTicker}.png',
            orElse: () => null);
        final reportFile = files.firstWhere(
            (file) => file['name'] == 'report_${stockTicker}.txt',
            orElse: () => null);

        if (comparisonFile != null && resultFile != null) {
          setState(() {
            _comparisonImageUrl = comparisonFile['download_url'];
            _resultImageUrl = resultFile['download_url'];
            _message = '';
          });
          if (reportFile != null) {
            final reportResponse = await http.get(Uri.parse(reportFile['download_url']));
            if (reportResponse.statusCode == 200) {
              setState(() {
                _reportText = reportResponse.body;
                _messages.add({'bot': 'Report Loaded: \n' + _reportText});
              });
              // ReportView를 모달로 보여줍니다 (기존 화면 유지)
              showDialog(
                context: context,
                builder: (BuildContext context) => Dialog(
                  child: ReportView(reportText: _reportText),
                ),
              );
            } else {
              setState(() {
                _reportText = 'Failed to load report text';
                _messages.add({'bot': _reportText});
              });
            }
          } else {
            setState(() {
              _reportText = ''; // Clear the report text if no report is found
            });
          }
        } else {
          setState(() {
            _comparisonImageUrl = '';
            _resultImageUrl = '';
            _reportText = ''; // Clear the report text if no images or report are found
            _message = 'Unable to find images or report for the stock ticker $stockTicker';
            _messages.add({'bot': _message});
          });
        }
      } else {
        setState(() {
          _comparisonImageUrl = '';
          _resultImageUrl = '';
          _reportText = ''; // Clear the report text on API call failure
          _message = 'GitHub API call failed: ${response.statusCode}';
          _messages.add({'bot': _message});
        });
      }
    } catch (e) {
      setState(() {
        _comparisonImageUrl = '';
        _resultImageUrl = '';
        _reportText = ''; // Clear the report text on exception
        _message = 'Error occurred: $e';
        _messages.add({'bot': _message});
      });
    }
  }

  Future<void> _sendMessageToGemini(String message) async {
    try {
      final response = await Gemini.sendMessage(
        prompt: message,
        model: 'gemini-1.5-flash',  // 사용하는 모델 지정
      );

      if (response.statusCode == 200) {
        final reply = response.data['choices'][0]['text'];
        setState(() {
          _messages.add({'bot': reply});
        });
      } else {
        setState(() {
          _messages.add({'bot': 'Error: Unable to communicate with Gemini API.'});
        });
      }
    } catch (e) {
      setState(() {
        _messages.add({'bot': 'Error: $e'});
      });
    }
  }

  void _handleSubmitted(String text) {
    setState(() {
      _messages.add({'user': text});
    });

    // 주식 티커를 기반으로 한 요청인지, 일반 질문인지 구분
    if (_tickers.contains(text.toUpperCase())) {
      fetchImagesAndReport(text.toUpperCase());
    } else {
      _sendMessageToGemini(text);
    }

    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Stock Comparison Review'),
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            ListView.builder(
              shrinkWrap: true,
              physics: NeverScrollableScrollPhysics(),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return ListTile(
                  title: Text(message.keys.first == 'user' ? 'You: ' : 'Bot: '),
                  subtitle: Text(message.values.first),
                );
              },
            ),
            if (_comparisonImageUrl.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(8.0),
                height: 400, // 고정된 높이 설정
                child: Image.network(
                  _comparisonImageUrl,
                  fit: BoxFit.contain,
                  errorBuilder: (context, error, stackTrace) {
                    return Text('Failed to load comparison image');
                  },
                ),
              ),
            if (_resultImageUrl.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(8.0),
                height: 400, // 고정된 높이 설정
                child: Image.network(
                  _resultImageUrl,
                  fit: BoxFit.contain,
                  errorBuilder: (context, error, stackTrace) {
                    return Text('Failed to load result image');
                  },
                ),
              ),
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      onSubmitted: _handleSubmitted,
                      decoration: InputDecoration(
                        labelText: 'Ask Gemini or Enter Stock Ticker...',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  IconButton(
                    icon: Icon(Icons.send),
                    onPressed: () => _handleSubmitted(_controller.text),
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

class ReportView extends StatelessWidget {
  final String reportText;

  ReportView({required this.reportText});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Stock Report'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Markdown(
          data: reportText,
          styleSheet: MarkdownStyleSheet(
            h1: TextStyle(color: Colors.blue, fontSize: 24, fontWeight: FontWeight.bold),
            h2: TextStyle(color: Colors.blueAccent, fontSize: 22, fontWeight: FontWeight.bold),
            p: TextStyle(fontSize: 18, height: 1.5),
            strong: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            blockSpacing: 8.0,
            listBullet: TextStyle(color: Colors.blueAccent),
            tableHead: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 18,
              color: Colors.white,
              backgroundColor: Colors.blueAccent,
            ),
            tableBody: TextStyle(fontSize: 18, color: Colors.black),
          ),
          selectable: true, // 선택 가능한 텍스트를 위해 추가
        ),
      ),
    );
  }
}


// flutter clean

// flutter pub add flutter_gemini
// flutter pub get

// flutter devices

// flutter run -d R3CX404VPHE

// flutter run -d chrome