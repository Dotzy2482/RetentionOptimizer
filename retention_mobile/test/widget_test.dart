import 'package:flutter_test/flutter_test.dart';
import 'package:retention_mobile/main.dart';

void main() {
  testWidgets('App renders without errors', (WidgetTester tester) async {
    await tester.pumpWidget(const RetentionApp());
    expect(find.text('Retention Mobile App'), findsOneWidget);
  });
}
