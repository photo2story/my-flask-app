import 'package:flutter/material.dart';
import 'package:photo_view/photo_view.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Image Test',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: ImageTestPage(),
    );
  }
}

class ImageTestPage extends StatelessWidget {
  final String imageUrl = 'http://192.168.0.5:5000/static/images/comparison_AAPL_VOO.png';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Image Test'),
      ),
      body: Center(
        child: GestureDetector(
          onTap: () => _openImage(context),
          child: Image.network(
            imageUrl,
            errorBuilder: (context, error, stackTrace) {
              return Text('Failed to load image: $error');
            },
          ),
        ),
      ),
    );
  }

  void _openImage(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ImagePreviewScreen(imageUrl: imageUrl),
      ),
    );
  }
}

class ImagePreviewScreen extends StatelessWidget {
  final String imageUrl;

  ImagePreviewScreen({required this.imageUrl});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Preview Image'),
      ),
      body: Center(
        child: PhotoView(
          imageProvider: NetworkImage(imageUrl),
          errorBuilder: (context, error, stackTrace) {
            return Text('Failed to load image: $error');
          },
        ),
      ),
    );
  }
}
