import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_client.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthProvider>().refreshUser();
    });
  }

  String _humanSize(int bytes) {
    double b = bytes.toDouble();
    for (final unit in ['B', 'KB', 'MB', 'GB', 'TB']) {
      if (b < 1024) return '${b.toStringAsFixed(1)} $unit';
      b /= 1024;
    }
    return '${b.toStringAsFixed(1)} PB';
  }

  Future<void> _confirmLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Log out?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Log out')),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      await context.read<AuthProvider>().logout();
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          CircleAvatar(
            radius: 36,
            child: Text(
              (user?.username ?? '?').substring(0, 1).toUpperCase(),
              style: const TextStyle(fontSize: 28),
            ),
          ),
          const SizedBox(height: 12),
          Center(
            child: Text(user?.username ?? '', style: Theme.of(context).textTheme.titleLarge),
          ),
          if (user?.email != null && user!.email!.isNotEmpty)
            Center(
              child: Text(user.email!, style: Theme.of(context).textTheme.bodyMedium),
            ),
          const SizedBox(height: 24),
          if (user != null) ...[
            Text('Storage', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: user.usedFraction,
                minHeight: 8,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '${_humanSize(user.storageUsedBytes)} of ${_humanSize(user.quotaBytes)} used',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
          const SizedBox(height: 24),
          Text('Server', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(ApiClient.instance.baseUrl ?? '', style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 32),
          OutlinedButton.icon(
            onPressed: _confirmLogout,
            icon: const Icon(Icons.logout),
            label: const Text('Log out'),
          ),
        ],
      ),
    );
  }
}
