import 'package:flutter/material.dart';
import '../services/api_client.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  final _api = ApiClient.instance;
  late Future<Map<String, dynamic>> _dashboard;

  @override
  void initState() {
    super.initState();
    _dashboard = _loadDashboard();
  }

  Future<Map<String, dynamic>> _loadDashboard() async {
    final results = await Future.wait([
      _api.get('/admin/stats'),
      _api.get('/admin/users'),
    ]);
    return {
      'stats': results[0] as Map<String, dynamic>,
      'users': results[1]['users'] as List<dynamic>,
    };
  }

  void _reload() {
    setState(() => _dashboard = _loadDashboard());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Administration'),
        actions: [IconButton(onPressed: _reload, icon: const Icon(Icons.refresh))],
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _dashboard,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text(snapshot.error.toString()));
          }
          final data = snapshot.data!;
          final stats = data['stats'] as Map<String, dynamic>;
          final users = data['users'] as List<dynamic>;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Row(
                children: [
                  Expanded(child: _stat('Users', stats['users'])),
                  const SizedBox(width: 12),
                  Expanded(child: _stat('Images', stats['media'])),
                ],
              ),
              const SizedBox(height: 24),
              Text('Accounts', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              for (final entry in users) _userTile(entry as Map<String, dynamic>),
            ],
          );
        },
      ),
    );
  }

  Widget _stat(String label, dynamic value) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label),
            const SizedBox(height: 4),
            Text('$value', style: Theme.of(context).textTheme.headlineSmall),
          ],
        ),
      ),
    );
  }

  Widget _userTile(Map<String, dynamic> user) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(child: Text('${user['username']}'.substring(0, 1).toUpperCase())),
        title: Text('${user['username']}'),
        subtitle: Text('${user['storage_used_bytes']} bytes used'),
        trailing: user['is_admin'] == true
            ? const Icon(Icons.admin_panel_settings_outlined)
            : null,
      ),
    );
  }
}
