import 'package:flutter/material.dart';
import '../providers/media_provider.dart';

class UploadBanner extends StatelessWidget {
  const UploadBanner({super.key, required this.tasks});

  final List<UploadTask> tasks;

  @override
  Widget build(BuildContext context) {
    if (tasks.isEmpty) return const SizedBox.shrink();
    return Material(
      elevation: 2,
      color: Theme.of(context).colorScheme.surfaceContainerHigh,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxHeight: 160),
        child: ListView.builder(
          padding: const EdgeInsets.symmetric(vertical: 4),
          shrinkWrap: true,
          itemCount: tasks.length,
          itemBuilder: (context, i) {
            final task = tasks[i];
            return ListTile(
              dense: true,
              leading: task.error != null
                  ? const Icon(Icons.error_outline, color: Colors.redAccent)
                  : (task.done
                      ? const Icon(Icons.check_circle_outline, color: Colors.green)
                      : const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )),
              title: Text(task.label, overflow: TextOverflow.ellipsis),
              subtitle: task.error != null ? Text(task.error!) : null,
            );
          },
        ),
      ),
    );
  }
}
