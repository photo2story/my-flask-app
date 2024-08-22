import 'package:flutter/material.dart';
import 'package:flutter_gemini/flutter_gemini.dart';
import 'package:example/sections/chat.dart';
import 'package:example/sections/chat_stream.dart';
import 'package:example/sections/embed_batch_contents.dart';
import 'package:example/sections/embed_content.dart';
import 'package:example/sections/response_widget_stream.dart';
import 'package:example/sections/stream.dart';
import 'package:example/sections/text_and_image.dart';
import 'package:example/sections/text_only.dart';
import 'stock_comparison.dart';  // stock_comparison.dart 파일을 import

void main() async {
  /// flutter run --dart-define=apiKey='Your Api Key'
  Gemini.init(
      apiKey: const String.fromEnvironment('apiKey'), enableDebugging: true);

  // Gemini.reInitialize(apiKey: "new api key", enableDebugging: false);

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Gemini',
      themeMode: ThemeMode.dark,
      debugShowCheckedModeBanner: false,
      darkTheme: ThemeData.dark().copyWith(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
          cardTheme: CardTheme(color: Colors.blue.shade900)),
      home: const MyHomePage(),
    );
  }
}

class SectionItem {
  final int index;
  final String title;
  final Widget widget;

  SectionItem(this.index, this.title, this.widget);
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key});

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _selectedItem = 0;

  final _sections = <SectionItem>[
    SectionItem(0, 'Stream text', const SectionTextStreamInput()),
    SectionItem(1, 'textAndImage', const SectionTextAndImageInput()),
    SectionItem(2, 'chat', const SectionChat()),
    SectionItem(3, 'Stream chat', const SectionStreamChat()),
    SectionItem(4, 'text', const SectionTextInput()),
    SectionItem(5, 'embedContent', const SectionEmbedContent()),
    SectionItem(6, 'batchEmbedContents', const SectionBatchEmbedContents()),
    SectionItem(7, 'Stock Comparison', StockComparison(stockTicker: 'TSLA')), // 주식 비교 섹션 추가
    SectionItem(8, 'response without setState()', const ResponseWidgetSection()),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(_sections[_selectedItem].title),
        actions: [
          PopupMenuButton<int>(
            initialValue: _selectedItem,
            onSelected: (value) => setState(() => _selectedItem = value),
            itemBuilder: (context) => _sections.map((e) {
              return PopupMenuItem<int>(value: e.index, child: Text(e.title));
            }).toList(),
            child: const Icon(Icons.more_vert_rounded),
          )
        ],
      ),
      body: IndexedStack(
        index: _selectedItem,
        children: _sections.map((e) => e.widget).toList(),
      ),
    );
  }
}
