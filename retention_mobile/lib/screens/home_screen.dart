import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/user.dart';
import '../services/auth_provider.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../widgets/error_view.dart';
import '../widgets/skeleton.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late Future<User> _profileFuture;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  void _loadProfile() {
    final user = context.read<AuthProvider>().currentUser!;
    _profileFuture = ApiService.instance.getProfile(user.customerId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: FutureBuilder<User>(
          future: _profileFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const HomeScreenSkeleton();
            }
            if (snapshot.hasError) {
              return ErrorView(
                message: snapshot.error.toString(),
                onRetry: () => setState(() => _loadProfile()),
              );
            }
            return _buildContent(snapshot.data!);
          },
        ),
      ),
    );
  }

  Widget _buildContent(User user) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(user),
          const SizedBox(height: 32),
          _buildGaugeCard(user),
          const SizedBox(height: 24),
          _buildStatsRow(user),
          const SizedBox(height: 24),
          _buildTipsSection(user.segment),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildHeader(User user) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Merhaba, ${user.name.split(' ').first}!',
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Hoş geldin, sadakat puanın:',
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
        InkWell(
          borderRadius: BorderRadius.circular(24),
          splashColor: AppColors.primary.withValues(alpha: 0.10),
          onTap: () async {
            HapticFeedback.lightImpact();
            await context.read<AuthProvider>().logout();
          },
          child: Row(
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: AppColors.primary,
                child: Text(
                  user.avatarInitial,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.surface,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              const Icon(
                Icons.logout,
                size: 20,
                color: AppColors.textTertiary,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildGaugeCard(User user) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 32),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: user.loyaltyScore),
            duration: const Duration(milliseconds: 1500),
            curve: Curves.easeOutCubic,
            builder: (context, value, _) {
              return SizedBox(
                width: 200,
                height: 200,
                child: CustomPaint(
                  painter: _GaugePainter(value / 100),
                  child: Center(
                    child: RichText(
                      text: TextSpan(
                        children: [
                          TextSpan(
                            text: value.round().toString(),
                            style: const TextStyle(
                              fontSize: 48,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          const TextSpan(
                            text: '/100',
                            style: TextStyle(
                              fontSize: 16,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          _SegmentBadge(segment: user.segment),
        ],
      ),
    );
  }

  Widget _buildStatsRow(User user) {
    final moneyStr =
        '₺${NumberFormat('#,##0', 'tr_TR').format(user.monetary.round())}';
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            label: 'Son\nAktiflik',
            value: '${user.recency} gün',
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            label: 'Toplam\nSipariş',
            value: user.frequency.toString(),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            label: 'Toplam\nHarcama',
            value: moneyStr,
          ),
        ),
      ],
    );
  }

  Widget _buildTipsSection(CustomerSegment segment) {
    final tips = _tipsForSegment(segment);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'İpuçları',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 12),
        ...tips.map(
          (tip) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: _TipCard(text: tip),
          ),
        ),
      ],
    );
  }

  List<String> _tipsForSegment(CustomerSegment segment) {
    switch (segment) {
      case CustomerSegment.highValueLoyal:
        return [
          'VIP statünü koruyor olman harika!',
          'Her hafta yeni hediyeler seni bekliyor.',
        ];
      case CustomerSegment.active:
        return [
          'Bir adım daha at, VIP olabilirsin!',
          'Sadakat puanını yükseltmek için bu hafta alışveriş yap.',
        ];
      case CustomerSegment.atRisk:
        return [
          'Geri dönmen için sana özel kupon hazırladık.',
          'Alışveriş yap ve puanlarını koru!',
        ];
      case CustomerSegment.lowEngagement:
        return [
          'İlk alışverişine %15 indirim seni bekliyor.',
          'Hemen başla ve puanlarını biriktir!',
        ];
    }
  }
}

// ─── Gauge Painter ────────────────────────────────────────────────────────────

class _GaugePainter extends CustomPainter {
  final double progress;

  _GaugePainter(this.progress);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 12;
    const strokeWidth = 14.0;
    const startAngle = -2.356; // -135°
    const totalSweep = 4.712; // 270°

    final bgPaint = Paint()
      ..color = const Color(0x1A7C3AED)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      totalSweep,
      false,
      bgPaint,
    );

    if (progress > 0) {
      final fgPaint = Paint()
        ..color = AppColors.primary
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth
        ..strokeCap = StrokeCap.round;

      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        totalSweep * progress,
        false,
        fgPaint,
      );
    }
  }

  @override
  bool shouldRepaint(_GaugePainter old) => old.progress != progress;
}

// ─── Segment Badge ────────────────────────────────────────────────────────────

class _SegmentBadge extends StatelessWidget {
  final CustomerSegment segment;

  const _SegmentBadge({required this.segment});

  @override
  Widget build(BuildContext context) {
    final (bg, fg) = switch (segment) {
      CustomerSegment.lowEngagement => (
          const Color(0xFFE5E7EB),
          const Color(0xFF9CA3AF),
        ),
      CustomerSegment.atRisk => (
          const Color(0xFFFCA5A5),
          const Color(0xFFDC2626),
        ),
      CustomerSegment.active => (
          const Color(0xFF93C5FD),
          const Color(0xFF1D4ED8),
        ),
      CustomerSegment.highValueLoyal => (
          const Color(0xFFDDD6FE),
          const Color(0xFF7C3AED),
        ),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        segment.label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: fg,
        ),
      ),
    );
  }
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

class _StatCard extends StatelessWidget {
  final String label;
  final String value;

  const _StatCard({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              color: AppColors.textSecondary,
              height: 1.3,
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Tip Card ─────────────────────────────────────────────────────────────────

class _TipCard extends StatelessWidget {
  final String text;

  const _TipCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: const Color(0x1A7C3AED),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.lightbulb_outline,
              size: 18,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.textPrimary,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
