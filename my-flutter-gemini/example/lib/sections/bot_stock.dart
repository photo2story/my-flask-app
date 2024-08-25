import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:async';

class BotStock extends StatefulWidget {
  @override
  _BotStockState createState() => _BotStockState();
}

class _BotStockState extends State<BotStock> {
  final TextEditingController _controller = TextEditingController();
  String _responseMessage = '';
  bool _isLoading = false;

  // 서버에 명령을 전송하는 함수
  Future<void> sendDiscordCommand(String command) async {
    setState(() {
      _isLoading = true;
      _responseMessage = '';
    });

    final String? baseUrl = dotenv.env['DDNS_KEY'];
    if (baseUrl == null || baseUrl.isEmpty) {
      setState(() {
        _responseMessage = 'Error: DDNS_KEY is not set in .env file';
        _isLoading = false;
      });
      return;
    }

    final url = Uri.parse('http://$baseUrl:5000/send_discord_command');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'command': command}),
      ).timeout(Duration(seconds: 10)); // 10초 타임아웃 설정

      print('Response status: ${response.statusCode}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        setState(() {
          _responseMessage = 'Command executed successfully! Command: $command';
        });
      } else {
        setState(() {
          _responseMessage = 'Failed to execute command. Status: ${response.statusCode}, Body: ${response.body}';
        });
      }
    } on TimeoutException {
      setState(() {
        _responseMessage = 'Error: Connection timed out. Please check your network.';
      });
    } catch (e) {
      setState(() {
        _responseMessage = 'Error: ${e.toString()}';
      });
      print('Error: $e');
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
              onPressed: _isLoading ? null : () => sendDiscordCommand(_controller.text),
              child: _isLoading ? CircularProgressIndicator() : Text('Send Command'),
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