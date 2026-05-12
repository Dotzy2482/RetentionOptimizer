import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

class SkeletonBox extends StatelessWidget {
  final double width;
  final double height;
  final double radius;

  const SkeletonBox({
    super.key,
    required this.width,
    required this.height,
    this.radius = 8,
  });

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey.shade300,
      highlightColor: Colors.grey.shade100,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(radius),
        ),
      ),
    );
  }
}

class HomeScreenSkeleton extends StatelessWidget {
  const HomeScreenSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SkeletonBox(width: 200, height: 28),
                  SizedBox(height: 8),
                  SkeletonBox(width: 160, height: 14),
                ],
              ),
              SkeletonBox(width: 48, height: 48, radius: 24),
            ],
          ),
          const SizedBox(height: 32),
          const Center(child: SkeletonBox(width: 280, height: 280, radius: 14)),
          const SizedBox(height: 24),
          const Row(
            children: [
              Expanded(
                  child: SkeletonBox(
                      width: double.infinity, height: 80, radius: 14)),
              SizedBox(width: 8),
              Expanded(
                  child: SkeletonBox(
                      width: double.infinity, height: 80, radius: 14)),
              SizedBox(width: 8),
              Expanded(
                  child: SkeletonBox(
                      width: double.infinity, height: 80, radius: 14)),
            ],
          ),
        ],
      ),
    );
  }
}

class CouponsScreenSkeleton extends StatelessWidget {
  const CouponsScreenSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 4,
      separatorBuilder: (_, _) => const SizedBox(height: 12),
      itemBuilder: (_, _) =>
          const SkeletonBox(width: double.infinity, height: 120, radius: 14),
    );
  }
}
