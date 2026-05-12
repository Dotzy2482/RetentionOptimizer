import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import '../services/coupons_provider.dart';
import '../theme/app_colors.dart';
import '../widgets/coupon_card.dart';
import '../widgets/error_view.dart';
import '../widgets/skeleton.dart';

class CouponsScreen extends StatefulWidget {
  const CouponsScreen({super.key});

  @override
  State<CouponsScreen> createState() => _CouponsScreenState();
}

class _CouponsScreenState extends State<CouponsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _load());
  }

  void _load() {
    final user = context.read<AuthProvider>().currentUser;
    if (user == null) return;
    context.read<CouponsProvider>().loadCoupons(user.customerId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Consumer<CouponsProvider>(
          builder: (context, provider, _) {
            if (provider.isLoading && provider.coupons.isEmpty) {
              return const CouponsScreenSkeleton();
            }
            if (provider.error != null && provider.coupons.isEmpty) {
              return ErrorView(
                message: provider.error!,
                onRetry: _load,
              );
            }
            if (provider.coupons.isEmpty) return _buildEmpty();
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
                  child: _buildHeader(),
                ),
                const SizedBox(height: 16),
                Expanded(child: _buildList(provider)),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Kuponlarım',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        SizedBox(height: 4),
        Text(
          'Kazandığın indirimleri burada bulabilirsin.',
          style: TextStyle(
            fontSize: 12,
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildList(CouponsProvider provider) {
    final coupons = provider.coupons;
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: coupons.length,
      separatorBuilder: (_, _) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final coupon = coupons[index];
        return AnimatedSlide(
          offset: Offset.zero,
          duration: Duration(milliseconds: 200 + index * 40),
          curve: Curves.easeOut,
          child: AnimatedOpacity(
            opacity: 1.0,
            duration: Duration(milliseconds: 200 + index * 40),
            child: Dismissible(
              key: ValueKey(coupon.couponId),
              direction: DismissDirection.endToStart,
              background: Container(
                alignment: Alignment.centerRight,
                padding: const EdgeInsets.symmetric(horizontal: 24),
                margin: const EdgeInsets.symmetric(vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.danger,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.delete_outline, color: Colors.white, size: 24),
                    SizedBox(width: 8),
                    Text(
                      'Sil',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              confirmDismiss: (direction) async {
                return await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Text('Kuponu Sil'),
                    content: Text(
                        '"${coupon.title}" kuponunu silmek istediğine emin misin?'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('İptal'),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        style: TextButton.styleFrom(
                            foregroundColor: AppColors.danger),
                        child: const Text('Sil'),
                      ),
                    ],
                  ),
                );
              },
              onDismissed: (direction) async {
                HapticFeedback.mediumImpact();
                try {
                  await context
                      .read<CouponsProvider>()
                      .deleteCoupon(coupon.couponId);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text('"${coupon.title}" silindi'),
                      duration: const Duration(seconds: 2),
                      behavior: SnackBarBehavior.floating,
                    ));
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text('Hata: $e'),
                      backgroundColor: AppColors.danger,
                    ));
                  }
                }
              },
              child: CouponCard(
                coupon: coupon,
                onTap: () {
                  HapticFeedback.lightImpact();
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Kupon kodu kopyalandı: ${coupon.code}'),
                      behavior: SnackBarBehavior.floating,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      backgroundColor: AppColors.textPrimary,
                    ),
                  );
                },
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildEmpty() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('🎁', style: TextStyle(fontSize: 64)),
            SizedBox(height: 16),
            Text(
              'Henüz kuponun yok',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Sadakat puanın arttıkça kuponların\nburada görünecek.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                color: AppColors.textSecondary,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
