import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class BotStock extends StatefulWidget {
  @override
  _BotStockState createState() => _BotStockState();
}

class _BotStockState extends State<BotStock> {
  final TextEditingController _controller = TextEditingController();
  String _responseMessage = '';

  // 서버에 명령을 전송하는 함수
  Future<void> sendDiscordCommand(String command) async {
    final String? baseUrl = dotenv.env['DDNS_KEY']; // .env 파일에서 DDNS_KEY 불러오기
    final url = Uri.parse('http://$baseUrl:5000/send_discord_command');  // Flask 서버의 URL로 설정
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'command': command}),
      );

      print('Response status: ${response.statusCode}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        setState(() {
          _responseMessage = 'Command executed successfully!';
        });
      } else {
        setState(() {
          _responseMessage = 'Failed to execute command: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _responseMessage = 'Error: $e';
      });
      print('Error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Send Discord Command'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _controller,
              decoration: InputDecoration(
                labelText: 'Enter Command',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                sendDiscordCommand(_controller.text);
              },
              child: Text('Send Command'),
            ),
            SizedBox(height: 20),
            Text(
              _responseMessage,
              style: TextStyle(fontSize: 16),
            ),
          ],
        ),
      ),
    );
  }
}

void main() async {
  await dotenv.load(fileName: ".env");  // .env 파일 로드
  runApp(MaterialApp(
    home: BotStock(),
  ));
}
