from pathlib import Path

runtime_path = Path("NexusLauncher/Services/MinecraftRuntimeService.cs")
runtime = runtime_path.read_text(encoding="utf-8")
if "using System.Collections.Concurrent;" not in runtime:
    runtime = "using System.Collections.Concurrent;\nusing System.Text;\n" + runtime
class_marker = "public sealed class MinecraftRuntimeService\n{\n"
assert class_marker in runtime
if "DownloadPathLocks" not in runtime:
    runtime = runtime.replace(
        class_marker,
        class_marker + """    private static readonly ConcurrentDictionary<string, SemaphoreSlim> DownloadPathLocks = new(StringComparer.OrdinalIgnoreCase);

    // FileShare.None coordinates downloads between separate NEXUS processes too.
    private static async Task<FileStream> AcquireDownloadPathLockAsync(string target, CancellationToken ct)
    {
        var normalized = Path.GetFullPath(target);
        var key = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(normalized.ToUpperInvariant())));
        var lockDirectory = Path.Combine(Path.GetTempPath(), "NEXUS", "download-locks");
        Directory.CreateDirectory(lockDirectory);
        var lockPath = Path.Combine(lockDirectory, key + ".lock");
        while (true)
        {
            ct.ThrowIfCancellationRequested();
            try
            {
                return new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None,
                    1, FileOptions.DeleteOnClose);
            }
            catch (IOException)
            {
                await Task.Delay(200, ct);
            }
        }
    }
""",
        1
    )

start = runtime.index("    private static async Task DownloadVerifiedAsync(")
end = runtime.index("    private static async Task<bool> IsValidAsync(", start)
method = runtime[start:end]
if "DownloadPathLocks.GetOrAdd" not in method:
    old_head = """    {
        const long maximumBytes = 2_000_000_000;"""
    new_head = """    {
        var fullTarget = Path.GetFullPath(target);
        var gate = DownloadPathLocks.GetOrAdd(fullTarget, static _ => new SemaphoreSlim(1, 1));
        await gate.WaitAsync(ct);
        try
        {
            // A previous launcher process may already have completed this download.
            await using var fileLock = await AcquireDownloadPathLockAsync(fullTarget, ct);
            if (await IsValidAsync(fullTarget, sha1, expectedSize, ct)) return;
        const long maximumBytes = 2_000_000_000;"""
    assert old_head in method, "Download method start not found"
    method = method.replace(old_head, new_head, 1)
    old_tail = """        }, Path.GetFileName(target), progress, ct);
    }

"""
    new_tail = """        }, Path.GetFileName(target), progress, ct);
        }
        finally
        {
            gate.Release();
        }
    }

"""
    assert old_tail in method, "Download method end not found"
    method = method.replace(old_tail, new_tail, 1)
    runtime = runtime[:start] + method + runtime[end:]

# Treat sharing violations as "not verified" so downloader can wait for the path lock.
old_valid = """    private static async Task<bool> IsValidAsync(string path, string? sha1, long expectedSize, CancellationToken ct)
    {
        if (!File.Exists(path)) return false;
        var info = new FileInfo(path);
        if (expectedSize >= 0 && info.Length != expectedSize) return false;
        return string.IsNullOrWhiteSpace(sha1) || await HashMatchesAsync(path, sha1, ct);
    }

"""
new_valid = """    private static async Task<bool> IsValidAsync(string path, string? sha1, long expectedSize, CancellationToken ct)
    {
        try
        {
            if (!File.Exists(path)) return false;
            var info = new FileInfo(path);
            if (expectedSize >= 0 && info.Length != expectedSize) return false;
            return string.IsNullOrWhiteSpace(sha1) || await HashMatchesAsync(path, sha1, ct);
        }
        catch (IOException) { return false; }
        catch (UnauthorizedAccessException) { return false; }
    }

"""
assert old_valid in runtime, "IsValidAsync method not found"
runtime = runtime.replace(old_valid, new_valid, 1)
runtime_path.write_text(runtime, encoding="utf-8")

main_path = Path("NexusLauncher/MainWindow.xaml.cs")
main = main_path.read_text(encoding="utf-8")
if "private bool _launchInProgress;" not in main:
    marker = "public partial class MainWindow : Window\n{\n"
    assert marker in main
    main = main.replace(marker, marker + "    private bool _launchInProgress;\n", 1)

old_start = """    private async void Launch_Click(object sender, RoutedEventArgs e)
    {
        var account = _offlineMode ? _offlineAccount : AccountBox.SelectedItem as ElyAccount;
        if (account is null) { Log("Сначала выбери Ely.by или введи ник и нажми «Офлайн-вход»."); return; }
        try"""
new_start = """    private async void Launch_Click(object sender, RoutedEventArgs e)
    {
        if (_gameProcess is { } runningGame)
        {
            try
            {
                if (!runningGame.HasExited)
                {
                    Log("Minecraft уже запущен. Сначала закрой игру, затем запускай её снова.");
                    return;
                }
            }
            catch (InvalidOperationException) { }
            _gameProcess = null;
        }
        if (_launchInProgress)
        {
            Log("Запуск уже выполняется. Дождись завершения текущей операции.");
            return;
        }
        var account = _offlineMode ? _offlineAccount : AccountBox.SelectedItem as ElyAccount;
        if (account is null) { Log("Сначала выбери Ely.by или введи ник и нажми «Офлайн-вход»."); return; }
        _launchInProgress = true;
        try"""
if old_start in main:
    main = main.replace(old_start, new_start, 1)
elif "Запуск уже выполняется. Дождись завершения текущей операции." not in main:
    raise AssertionError("Launch_Click start not found")

old_finally = """        finally { EndProgress(); }
    }
    private static int JavaVersionNumber"""
new_finally = """        finally { EndProgress(); _launchInProgress = false; }
    }
    private static int JavaVersionNumber"""
if old_finally in main:
    main = main.replace(old_finally, new_finally, 1)
elif "_launchInProgress = false;" not in main:
    raise AssertionError("Launch_Click finally not found")
main_path.write_text(main, encoding="utf-8")
