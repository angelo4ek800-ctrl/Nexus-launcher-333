from pathlib import Path

runtime_path = Path("NexusLauncher/Services/MinecraftRuntimeService.cs")
runtime = runtime_path.read_text(encoding="utf-8")
if "using System.Collections.Concurrent;" not in runtime:
    runtime = "using System.Collections.Concurrent;\n" + runtime
class_marker = "public sealed class MinecraftRuntimeService\n{\n"
assert class_marker in runtime
if "LibraryDownloadLocks" not in runtime:
    runtime = runtime.replace(class_marker, class_marker + "    private static readonly ConcurrentDictionary<string, SemaphoreSlim> LibraryDownloadLocks = new(StringComparer.OrdinalIgnoreCase);\n", 1)
old = '''        if (!await IsValidAsync(target, hash, size, ct))
        {
            progress?.Report("Загрузка библиотеки: " + Path.GetFileName(target));
            await DownloadVerifiedAsync(url, target, hash, size, progress, ct);
        }
        return target;'''
new = '''        // Multiple launch/install actions can request the same library at once.
        // Serialize by canonical destination and re-check after entering the gate.
        var gateKey = Path.GetFullPath(target);
        var gate = LibraryDownloadLocks.GetOrAdd(gateKey, static _ => new SemaphoreSlim(1, 1));
        await gate.WaitAsync(ct);
        try
        {
            if (!await IsValidAsync(target, hash, size, ct))
            {
                progress?.Report("Загрузка библиотеки: " + Path.GetFileName(target));
                await DownloadVerifiedAsync(url, target, hash, size, progress, ct);
            }
            return target;
        }
        finally
        {
            gate.Release();
        }'''
assert old in runtime, "Library download block not found"
runtime = runtime.replace(old, new, 1)
runtime_path.write_text(runtime, encoding="utf-8")

main_path = Path("NexusLauncher/MainWindow.xaml.cs")
main = main_path.read_text(encoding="utf-8")
if "private bool _launchInProgress;" not in main:
    marker = "public partial class MainWindow : Window\n{\n"
    assert marker in main
    main = main.replace(marker, marker + "    private bool _launchInProgress;\n", 1)
old_start = '''    private async void Launch_Click(object sender, RoutedEventArgs e)
    {
        var account = _offlineMode ? _offlineAccount : AccountBox.SelectedItem as ElyAccount;'''
new_start = '''    private async void Launch_Click(object sender, RoutedEventArgs e)
    {
        if (_launchInProgress)
        {
            Log("Запуск уже выполняется. Дождись завершения текущей операции.");
            return;
        }
        _launchInProgress = true;
        var account = _offlineMode ? _offlineAccount : AccountBox.SelectedItem as ElyAccount;'''
assert old_start in main, "Launch_Click start not found"
main = main.replace(old_start, new_start, 1)
old_finally = '''        finally { EndProgress(); }
    }
    private static int JavaVersionNumber'''
new_finally = '''        finally { EndProgress(); _launchInProgress = false; }
    }
    private static int JavaVersionNumber'''
assert old_finally in main, "Launch_Click finally block not found"
main = main.replace(old_finally, new_finally, 1)
main_path.write_text(main, encoding="utf-8")
