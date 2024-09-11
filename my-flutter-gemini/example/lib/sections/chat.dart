import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:syncfusion_flutter_pdf/pdf.dart';
import 'package:flutter_gemini/flutter_gemini.dart';

class ChatMessage {
  final String sender;
  final String message;
  ChatMessage({required this.sender, required this.message});
}

class SectionChat extends StatefulWidget {
  const SectionChat({Key? key}) : super(key: key);

  @override
  State<SectionChat> createState() => _SectionChatState();
}

class _SectionChatState extends State<SectionChat> {
  final controller = TextEditingController();
  bool _loading = false;
  List<ChatMessage> chats = [];
  final gemini = Gemini.instance;
  String pdfContent = '';

  final String githubPdfUrl =
      "https://raw.githubusercontent.com/photo2story/flutter_gemini_chat/master/example/data/20231226_Guide_1000.pdf";

  @override
  void initState() {
    super.initState();
    _initializePdfContent();
  }

  Future<void> _initializePdfContent() async {
    pdfContent = await fetchPdfFromGithub(githubPdfUrl);
  }

  Future<String> fetchPdfFromGithub(String url, {int? startPage, int? endPage}) async {
    try {
      final response = await http.get(Uri.parse(url));

      if (response.statusCode == 200) {
        final directory = await getTemporaryDirectory();
        final filePath = '${directory.path}/temp_guide.pdf';
        final file = File(filePath);
        await file.writeAsBytes(response.bodyBytes);

        final List<int> bytes = file.readAsBytesSync();
        final PdfDocument document = PdfDocument(inputBytes: bytes);

        int start = startPage ?? 0;
        int end = endPage ?? document.pages.count - 1;
        String text = PdfTextExtractor(document).extractText(startPageIndex: start, endPageIndex: end);
        document.dispose();

        return text;
      } else {
        throw Exception('Failed to load PDF. Status Code: ${response.statusCode}');
      }
    } catch (e) {
      print("Error fetching PDF: $e");
      return 'Error fetching PDF: $e';
    }
  }

  Future<void> handlePdfChat(String input) async {
    setState(() => _loading = true);

    if (input.startsWith('/pdf')) {
      List<String> inputParts = input.split(" ");
      if (inputParts.length > 1) {
        int? pageNumber = int.tryParse(inputParts[1]);
        if (pageNumber != null) {
          String extractedText = await fetchPdfFromGithub(githubPdfUrl,
              startPage: pageNumber - 1, endPage: pageNumber - 1);
          setState(() {
            chats.add(ChatMessage(sender: 'system', message: "PDF 페이지 $pageNumber 내용: $extractedText"));
          });
        }
      } else {
        setState(() {
          chats.add(ChatMessage(sender: 'system', message: "전체 PDF 내용: $pdfContent"));
        });
      }
    } else if (input.startsWith('/summary')) {
      String prompt = "다음 PDF 내용을 간략하게 요약해주세요: $pdfContent";
      final response = await gemini.text(prompt);
      setState(() {
        chats.add(ChatMessage(sender: 'system', message: "PDF 요약: ${response?.content?.toString() ?? "요약을 생성할 수 없습니다."}"));
      });
    } else {
      chats.add(ChatMessage(sender: 'user', message: input));
      String context = "다음은 PDF의 내용입니다: $pdfContent\n\n사용자의 질문: $input";
      final response = await gemini.text(context);
      setState(() {
        chats.add(ChatMessage(sender: 'system', message: response?.content?.toString() ?? "죄송합니다. 응답을 생성할 수 없습니다."));
      });
    }

    setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Chat with PDF'),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: chats.length,
              itemBuilder: (context, index) {
                ChatMessage chat = chats[index];
                return ListTile(
                  title: Text(
                    chat.message,
                    style: TextStyle(
                      color: chat.sender == 'user' ? Colors.blue : Colors.green,
                    ),
                  ),
                );
              },
            ),
          ),
          if (_loading) const CircularProgressIndicator(),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  decoration: const InputDecoration(hintText: 'Type a message...'),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.send),
                onPressed: () {
                  if (controller.text.isNotEmpty) {
                    String input = controller.text;
                    controller.clear();
                    handlePdfChat(input);
                  }
                },
              ),
            ],
          ),
        ],
      ),
    );
  }
}