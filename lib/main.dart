import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'screens/login_screen.dart';
import 'screens/server_setup_screen.dart';
import 'screens/home_screen.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const PhotoApp());
}

class PhotoApp extends StatelessWidget {
  const PhotoApp({super.key});

  static const _blue = Color(0xFF1261A0);
  static const _sky = Color(0xFF4DB8E8);

  ThemeData _theme(Brightness brightness) {
    final dark = brightness == Brightness.dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: _blue,
      brightness: brightness,
      primary: _blue,
      secondary: _sky,
      surface: dark ? const Color(0xFF101820) : const Color(0xFFF7FBFF),
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      fontFamily: 'Georgia',
      scaffoldBackgroundColor: scheme.surface,
      appBarTheme: AppBarTheme(
        backgroundColor: dark ? const Color(0xFF0B1117) : Colors.white,
        foregroundColor: scheme.onSurface,
        elevation: 2,
        shadowColor: _blue.withValues(alpha: 0.2),
        titleTextStyle: TextStyle(
          color: scheme.onSurface,
          fontFamily: 'Georgia',
          fontSize: 21,
          fontWeight: FontWeight.bold,
        ),
      ),
      cardTheme: CardThemeData(
        color: dark ? const Color(0xFF17232E) : Colors.white,
        elevation: 3,
        shadowColor: _blue.withValues(alpha: 0.18),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? const Color(0xFF17232E) : Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(3)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()..bootstrap()),
      ],
      child: MaterialApp(
        title: 'Photos',
        debugShowCheckedModeBanner: false,
        theme: _theme(Brightness.light),
        darkTheme: _theme(Brightness.dark),
        home: const AppRoot(),
      ),
    );
  }
}

/// Switches between the server-setup, login, and main app screens based
/// on [AuthProvider.status], so nothing else in the app needs to think
/// about navigation guards.
class AppRoot extends StatelessWidget {
  const AppRoot({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    switch (auth.status) {
      case AuthStatus.unknown:
        return const SplashScreen();
      case AuthStatus.needsServer:
        return const ServerSetupScreen();
      case AuthStatus.needsLogin:
        return const LoginScreen();
      case AuthStatus.authenticated:
        return const HomeScreen();
    }
  }
}
