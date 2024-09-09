import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_gemini/flutter_gemini.dart';
import 'package:photo_view/photo_view.dart';  // PhotoView 추가

class StockComparison extends StatefulWidget {
  @override
  _StockComparisonState createState() => _StockComparisonState();
}

class _StockComparisonState extends State<StockComparison> {
  String _comparisonImageUrl = '';  // 비교 그래프 이미지 URL을 저장할 변수
  String _enteredTicker = '';  // 입력된 티커를 저장할 변수
  bool _isLoading = false;
  final TextEditingController _controller = TextEditingController();
  final List<Content> _chats = [];  // Chat 형식으로 데이터를 저장할 리스트
  final gemini = Gemini.instance;

  final String apiUrl = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images';

  @override
  void initState() {
    super.initState();
  }

  // 티커를 입력받아 이미지를 불러오고, 보고서를 번역
  Future<void> fetchImagesAndReport(String stockTicker) async {
    try {
      setState(() {
        _isLoading = true;
        _chats.clear();  // 새로운 요청을 시작할 때 채팅 리스트 초기화
        _enteredTicker = stockTicker;  // 입력된 티커를 저장
      });

      final response = await http.get(Uri.parse(apiUrl));
      if (response.statusCode == 200) {
        final List<dynamic> files = json.decode(response.body);

        // 비교 그래프 파일 찾기
        final comparisonFile = files.firstWhere(
          (file) => file['name'].startsWith('comparison_${stockTicker}') && file['name'].endsWith('_VOO.png'),
          orElse: () => null,
        );

        final reportFile = files.firstWhere(
            (file) => file['name'] == 'report_${stockTicker}.txt',
            orElse: () => null);

        if (comparisonFile != null) {
          setState(() {
            _comparisonImageUrl = comparisonFile['download_url'];  // 비교 그래프 URL 저장
          });
        } else {
          setState(() {
            _comparisonImageUrl = '';  // 그래프를 찾지 못하면 비움
          });
        }

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
          // 티커 입력 필드
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              controller: _controller,
              onSubmitted: (value) {
                if (value.isNotEmpty) {
                  fetchImagesAndReport(value.toUpperCase());  // 티커 입력 후 데이터를 불러옴
                  _controller.clear();  // 입력 후 텍스트 필드 비움
                }
              },
              decoration: InputDecoration(
                hintText: 'Enter stock ticker',
                border: OutlineInputBorder(),
              ),
            ),
          ),

          // 비교 그래프 이미지 표시
          if (_comparisonImageUrl.isNotEmpty)
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(8.0),
                child: PhotoView(
                  imageProvider: NetworkImage(_comparisonImageUrl),  // 불러온 이미지 URL 사용
                ),
              ),
            ),

          // 보고서 출력
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
                : const Center(child: Text('레포트를 불러오세요!')),
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
      color: content.role == 'model' ? Colors.black : Colors.transparent,
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
