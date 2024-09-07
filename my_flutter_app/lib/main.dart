import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:photo_view/photo_view.dart';
import 'package:photo_view/photo_view_gallery.dart';
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
  List<String> _tickers = [];
  final TextEditingController _controller = TextEditingController();

  final String apiUrl = 'http://localhost:5000/api';

  @override
  void initState() {
    super.initState();
    fetchReviewedTickers();
  }

  Future<void> fetchReviewedTickers() async {
    try {
      final response = await http.get(Uri.parse('$apiUrl/get_reviewed_tickers'));
      if (response.statusCode == 200) {
        final List<dynamic> tickers = json.decode(response.body);
        setState(() {
          _tickers = tickers.cast<String>();
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
      final response = await http.get(Uri.parse('$apiUrl/get_images?ticker=$stockTicker'));
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        setState(() {
          _comparisonImageUrl = data['comparison_image'] ?? '';
          _resultImageUrl = data['result_image'] ?? '';
          _reportText = data['report'] ?? '';
          _message = '';
        });
      } else {
        setState(() {
          _comparisonImageUrl = '';
          _resultImageUrl = '';
          _reportText = '';
          _message = 'Failed to fetch images and report: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _comparisonImageUrl = '';
        _resultImageUrl = '';
        _reportText = '';
        _message = 'Error occurred: $e';
      });
    }
  }

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
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: TextField(
                  controller: _controller,
                  textCapitalization: TextCapitalization.characters,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: 'Enter Stock Ticker',
                  ),
                  onChanged: (value) {
                    _controller.value = TextEditingValue(
                      text: value.toUpperCase(),
                      selection: _controller.selection,
                    );
                  },
                  onSubmitted: (value) {
                    fetchImagesAndReport(_controller.text.toUpperCase());
                  },
                ),
              ),
              ElevatedButton(
                onPressed: () {
                  fetchImagesAndReport(_controller.text.toUpperCase());
                },
                child: Text('Search Review'),
              ),
              SizedBox(height: 20),
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
              _comparisonImageUrl.isNotEmpty
                  ? GestureDetector(
                      onTap: () => _openImage(context, _comparisonImageUrl),
                      child: Image.network(
                        _comparisonImageUrl,
                        errorBuilder: (context, error, stackTrace) {
                          return Text('Failed to load comparison image');
                        },
                      ),
                    )
                  : Container(),
              SizedBox(height: 20),
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


// flutter devices

// flutter run -d R3CX404VPHE

// flutter run -d chrome