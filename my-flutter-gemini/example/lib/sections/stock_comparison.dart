import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_gemini/flutter_gemini.dart';

class StockComparison extends StatefulWidget {
  @override
  _StockComparisonState createState() => _StockComparisonState();
}

class _StockComparisonState extends State<StockComparison> {
  String _comparisonImageUrl = '';
  String _resultImageUrl = '';
  bool _isLoading = false;
  String? _finishReason;
  final TextEditingController _controller = TextEditingController(); // 입력 박스를 위한 컨트롤러
  String _enteredTicker = '';  // 입력된 티커를 저장할 변수
  List<Content> _chats = [];  // Chat 형식으로 데이터를 저장할 리스트
  final gemini = Gemini.instance;

  final String apiUrl = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images';

  @override
  void initState() {
    super.initState();
    // 처음에는 데이터를 불러오지 않고 사용자가 직접 입력하게 설정.
  }

  // finishReason 변수 설정을 위한 getter/setter
  String? get finishReason => _finishReason;

  set finishReason(String? reason) {
    setState(() {
      _finishReason = reason;
    });
  }

  // 티커를 입력받아 이미지를 불러오고, 보고서를 번역
  Future<void> fetchImagesAndReport(String stockTicker) async {
    try {
      setState(() {
        _isLoading = true;
        _chats = [];  // 새로운 요청을 시작할 때 채팅 리스트 초기화
        _enteredTicker = stockTicker;  // 입력된 티커를 저장
      });

      final response = await http.get(Uri.parse(apiUrl));
      if (response.statusCode == 200) {
        final List<dynamic> files = json.decode(response.body);
        final reportFile = files.firstWhere(
            (file) => file['name'] == 'report_${stockTicker}.txt',
            orElse: () => null);

        if (reportFile != null) {
          // 영문 레포트 불러오기
          final reportResponse = await http.get(Uri.parse(reportFile['download_url']));
          if (reportResponse.statusCode == 200) {
            setState(() {
              _chats.add(Content(role: 'user', parts: [Parts(text: '한글로 번역해줘')]));
              _chats.add(Content(role: 'user', parts: [Parts(text: reportResponse.body)])); // 영문 텍스트를 chats에 추가
            });

            // Gemini 플래시(무료)를 이용해 한글로 번역
            gemini.chat(_chats).then((value) {
              setState(() {
                _chats.add(Content(role: 'model', parts: [Parts(text: value?.output)]));  // 번역된 한글 텍스트를 chats에 추가
                _isLoading = false;
              });
            });
          } else {
            setState(() {
              _chats.add(Content(role: 'error', parts: [Parts(text: '레포트를 불러오는 데 실패했습니다: ${reportResponse.statusCode}')]));
              _isLoading = false;
            });
          }
        } else {
          setState(() {
            _chats.add(Content(role: 'error', parts: [Parts(text: '레포트를 찾을 수 없습니다.')]));
            _isLoading = false;
          });
        }
      } else {
        setState(() {
          _chats.add(Content(role: 'error', parts: [Parts(text: 'GitHub API 호출 실패: ${response.statusCode}')]));
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _chats.add(Content(role: 'error', parts: [Parts(text: '오류 발생: $e')]));
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
      body: Column(
        children: [
          // 상단에 입력된 티커가 있으면 고정 텍스트로 표시
          _enteredTicker.isNotEmpty
              ? Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Text(
                    'Entered Ticker: $_enteredTicker', // 입력된 티커를 고정 텍스트로 표시
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                )
              : ChatInputBox(
                  controller: _controller,  // 사용자가 입력할 수 있도록 컨트롤러 추가
                  onSend: () {
                    if (_controller.text.isNotEmpty) {
                      final ticker = _controller.text.toUpperCase();  // 티커를 대문자로 변환
                      _chats = [];  // 새로운 요청을 할 때 이전 채팅 기록 초기화
                      _chats.add(Content(role: 'user', parts: [Parts(text: '티커: $ticker 로 분석을 요청합니다.')]));
                      fetchImagesAndReport(ticker);  // 입력된 티커로 데이터와 보고서 요청
                      _controller.clear();
                    }
                  },
                ),
          Expanded(
            child: _chats.isNotEmpty
                ? Align(
                    alignment: Alignment.bottomCenter,
                    child: SingleChildScrollView(
                      reverse: true,
                      child: ListView.builder(
                        itemBuilder: chatItem,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _chats.length,
                        reverse: false,
                      ),
                    ),
                  )
                : const Center(child: Text('레포트를 불러오세요!')),  // 초기 메시지
          ),
          if (_isLoading) const CircularProgressIndicator(),
        ],
      ),
    );
  }

  // 채팅 아이템을 표시하는 함수
  Widget chatItem(BuildContext context, int index) {
    final Content content = _chats[index];

    return Card(
      elevation: 0,
      color: content.role == 'model' ? Colors.black : Colors.transparent, // 답변창 배경을 검정색으로 변경
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(content.role ?? 'role'),
            Markdown(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              data: content.parts?.lastOrNull?.text ?? 'cannot generate data!',
            ),
          ],
        ),
      ),
    );
  }
}

// 채팅 입력 박스를 위한 위젯
class ChatInputBox extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;

  ChatInputBox({required this.controller, required this.onSend});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              decoration: InputDecoration(
                labelText: 'Enter stock ticker',
                border: OutlineInputBorder(),
              ),
              textCapitalization: TextCapitalization.characters,  // 대문자 입력 강제
            ),
          ),
          IconButton(
            icon: Icon(Icons.send),
            onPressed: onSend,
          ),
        ],
      ),
    );
  }
}
