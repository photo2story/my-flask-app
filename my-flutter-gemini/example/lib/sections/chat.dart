import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart'; // To store the file locally
import 'package:syncfusion_flutter_pdf/pdf.dart'; // To extract text from PDF

class ChatMessage {
  final String sender; // 'user' or 'system'
  final String message;
  ChatMessage({required this.sender, required this.message});
}

class SectionChat extends StatefulWidget {
  const SectionChat({super.key});

  @override
  State<SectionChat> createState() => _SectionChatState();
}

class _SectionChatState extends State<SectionChat> {
  final controller = TextEditingController();
  bool _loading = false;
  List<ChatMessage> chats = []; // List of ChatMessage to manage conversation more cleanly

  final String githubPdfUrl =
      "https://raw.githubusercontent.com/photo2story/flutter_gemini_chat/master/example/data/20231226_Guide_1000.pdf";

  // Function to download and read PDF using syncfusion_flutter_pdf
  Future<String> fetchPdfFromGithub(String url, {int? startPage, int? endPage}) async {
    try {
      final response = await http.get(Uri.parse(url));

      if (response.statusCode == 200) {
        final directory = await getTemporaryDirectory();
        final filePath = '${directory.path}/temp_guide.pdf';
        final file = File(filePath);
        await file.writeAsBytes(response.bodyBytes);

        // Load the PDF document
        final List<int> bytes = file.readAsBytesSync();
        final PdfDocument document = PdfDocument(inputBytes: bytes);

        // Extract text from the given page range or default to the first page
        int start = startPage ?? 0;
        int end = endPage ?? 0;
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

  // Handle chat input including /pdf and /summary commands
  void handlePdfChat(String input) async {
    setState(() => _loading = true);

    if (input.startsWith('/pdf')) {
      // Parse the page number if provided
      int? pageNumber;
      List<String> inputParts = input.split(" ");
      if (inputParts.length > 1) {
        pageNumber = int.tryParse(inputParts[1]);
      }

      String extractedText = await fetchPdfFromGithub(githubPdfUrl,
          startPage: pageNumber != null ? pageNumber - 1 : 0, endPage: pageNumber != null ? pageNumber - 1 : 0);

      setState(() {
        chats.add(ChatMessage(sender: 'system', message: "PDF 페이지 내용: $extractedText"));
        _loading = false;
      });
    } else if (input.startsWith('/summary')) {
      String extractedText = await fetchPdfFromGithub(githubPdfUrl);
      setState(() {
        chats.add(ChatMessage(
            sender: 'system', message: "PDF 요약 기능은 준비 중입니다. PDF 첫 페이지 내용은 다음과 같습니다: $extractedText"));
        _loading = false;
      });
    } else {
      // General user message handling
      setState(() {
        chats.add(ChatMessage(sender: 'user', message: input));
        _loading = false;
      });
    }
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
                    handlePdfChat(input); // Fetch PDF from GitHub or handle other commands
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
