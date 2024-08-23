import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class RasaChat extends StatefulWidget {
  @override
  _RasaChatState createState() => _RasaChatState();
}

class _RasaChatState extends State<RasaChat> {
  final TextEditingController _controller = TextEditingController();
  String _responseMessage = '';

  // Rasa 서버에 메시지를 전송하는 함수
  Future<void> sendMessageToRasa(String message) async {
    final url = Uri.parse('http://your-rasa-server-url/webhooks/rest/webhook');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'sender': 'user', 'message': message}),
      );

      print('Response status: ${response.statusCode}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final List<dynamic> responseData = json.decode(response.body);
        if (responseData.isNotEmpty) {
          setState(() {
            _responseMessage = responseData.first['text'];
          });
        } else {
          setState(() {
            _responseMessage = 'No response from Rasa server.';
          });
        }
      } else {
        setState(() {
          _responseMessage = 'Failed to communicate with Rasa server: ${response.statusCode}';
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
        title: Text('Rasa Chatbot'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _controller,
              decoration: InputDecoration(
                labelText: 'Enter your message',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                sendMessageToRasa(_controller.text);
              },
              child: Text('Send Message'),
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
