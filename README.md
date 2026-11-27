# NEXUS LAUNCHER 0.5.1

NEXUS LAUNCHER is a Windows 10/11 x64 WPF Minecraft launcher built with .NET 8.

## Build the Windows installer

The source project is stored in `NexusLauncher_0.5.1_Source.zip` in this repository. GitHub Actions extracts it, runs the static source validator, publishes a self-contained Windows x64 application, and creates:

`NexusLauncherSetup.exe`

To start a build manually, open **Actions → Build NEXUS Windows installer → Run workflow**. Pushes to `main` also trigger a build. The installer is attached to a GitHub Release when a `v*` tag is pushed.

A successful build will expose the installer under **Actions → latest successful run → Artifacts → NexusLauncherSetup-Windows-x64**.

## First launch and Ely.by

Ely.by is the only supported account provider. There is no Microsoft login and no offline-account mode. The user must configure their own Ely.by OAuth application in NEXUS settings by entering its Client ID and Client Secret and registering the exact redirect URI shown by the launcher. OAuth secrets are not embedded in this public repository; NEXUS encrypts locally saved settings for the current Windows user.

## Product scope

- No news feed and no launcher auto-updater.
- Multiple Ely.by accounts with DPAPI-protected tokens.
- Minecraft versions, Java management, Vanilla and mod-loader installation.
- Modrinth and CurseForge catalogues, local mod files, server status, screenshots and profile backups.
- Ely.by skin/cape preview and authlib-injector integration.
- Optional user-managed Mesa3D compatibility files. Mesa binaries are not bundled and are preserved in the user's LocalAppData folder.

## Important limitations

The source validator is a static check; it is not a substitute for a real Windows build and live Minecraft launch test. Minecraft versions, mod loaders, Ely.by authentication and Mesa compatibility must be tested on the target PC. Intel HD Graphics 2000 compatibility is experimental and not guaranteed.
