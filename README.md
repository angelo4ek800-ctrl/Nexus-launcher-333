# NEXUS LAUNCHER

Windows Minecraft launcher (WPF / .NET 8).

## Build on GitHub

The repository includes a Windows GitHub Actions workflow at `.github/workflows/windows-installer.yml`. After the project source is uploaded under `NexusLauncher/`, run it from **Actions → Build NEXUS Windows installer → Run workflow**.

The workflow validates the project, publishes the x64 Windows application, and creates `NexusLauncherSetup.exe` with Inno Setup. The installer is published as a workflow artifact.

## Important

The source project is not yet present in this repository. No installer has been built or tested yet.
