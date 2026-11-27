from pathlib import Path

xaml_path = Path('NexusLauncher/MainWindow.xaml')
xaml = xaml_path.read_text(encoding='utf-8')

# The samurai theme patch rewrites the original multiline badge into one compact line.
old_theme_badge = '<TextBlock Text="Версия: " Foreground="{StaticResource Muted}"/><TextBlock x:Name="VersionText" FontWeight="SemiBold"/>'
new_theme_badge = '<Button x:Name="VersionPickerButton" Click="VersionPicker_Click" Background="#283246" Foreground="White" BorderThickness="0" Padding="8,3" Margin="0,0,8,0" ToolTip="Открыть полный список версий Minecraft"><StackPanel Orientation="Horizontal"><TextBlock Text="Версия: " Foreground="{StaticResource Muted}"/><TextBlock x:Name="VersionText" FontWeight="SemiBold"/><TextBlock Text="  ▾" Foreground="#E2B96F"/></StackPanel></Button>'
if old_theme_badge in xaml:
    xaml = xaml.replace(old_theme_badge, new_theme_badge, 1)
else:
    old_base_badge = '''                            <TextBlock Text="Версия: " Foreground="{StaticResource Muted}" />
                            <TextBlock x:Name="VersionText" />'''
    new_base_badge = '''                            <Button x:Name="VersionPickerButton" Click="VersionPicker_Click"
                                    Background="#252B3B" BorderBrush="#475573" BorderThickness="1"
                                    Padding="10,5" Margin="3,0"
                                    ToolTip="Открыть полный список версий Minecraft">
                                <StackPanel Orientation="Horizontal">
                                    <TextBlock Text="Версия:" Foreground="{StaticResource Muted}" />
                                    <TextBlock x:Name="VersionText" Margin="5,0,0,0" FontWeight="SemiBold" />
                                    <TextBlock Text="  ▾" Foreground="#D8B15A" />
                                </StackPanel>
                            </Button>'''
    assert old_base_badge in xaml, 'Could not find the current version label in MainWindow.xaml'
    xaml = xaml.replace(old_base_badge, new_base_badge, 1)

if 'Content="Обновить список версий" Click="Versions_Click"' in xaml:
    xaml = xaml.replace('Content="Обновить список версий" Click="Versions_Click"', 'Content="Выбрать версию" Click="VersionPicker_Click"', 1)
elif 'Content="Обновить версии" Click="Versions_Click"' in xaml:
    xaml = xaml.replace('Content="Обновить версии" Click="Versions_Click"', 'Content="Выбрать версию" Click="VersionPicker_Click"', 1)

xaml = xaml.replace(
    '<ComboBox x:Name="VersionBox" SelectionChanged="VersionBox_SelectionChanged"/>',
    '<ComboBox x:Name="VersionBox" Visibility="Collapsed" SelectionChanged="VersionBox_SelectionChanged"/>',
    1
)
xaml = xaml.replace(
    '<ComboBox x:Name="VersionBox" Width="160" SelectionChanged="VersionBox_SelectionChanged" />',
    '<ComboBox x:Name="VersionBox" Width="160" Visibility="Collapsed" SelectionChanged="VersionBox_SelectionChanged" />',
    1
)
xaml_path.write_text(xaml, encoding='utf-8')

cs_path = Path('NexusLauncher/MainWindow.xaml.cs')
cs = cs_path.read_text(encoding='utf-8')
marker = '    private void VersionBox_SelectionChanged(object sender, SelectionChangedEventArgs e)\n'
assert marker in cs, 'Could not find version selection handler in MainWindow.xaml.cs'
if 'private async void VersionPicker_Click(' not in cs:
    method = '''    private async void VersionPicker_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            if (_availableVersions.Count == 0)
            {
                Log("Получаю полный официальный список версий Minecraft от Mojang...");
                _availableVersions = await _minecraftVersions.GetVersionsAsync();
            }

            _changingVersion = true;
            VersionBox.ItemsSource = _availableVersions.Select(v => $"{v.Id}  [{v.Type}]").ToList();
            var currentIndex = _availableVersions.ToList().FindIndex(v => v.Id == Current.MinecraftVersion);
            VersionBox.SelectedIndex = currentIndex >= 0 ? currentIndex : -1;
            _changingVersion = false;

            var picker = new MinecraftVersionPickerWindow(_availableVersions, Current.MinecraftVersion) { Owner = this };
            if (picker.ShowDialog() != true || string.IsNullOrWhiteSpace(picker.SelectedVersionId)) return;

            var selected = _availableVersions.FirstOrDefault(v => v.Id == picker.SelectedVersionId);
            if (selected is null) return;
            if (Current.MinecraftVersion == selected.Id) return;

            Current.MinecraftVersion = selected.Id;
            Current.Loader = "Vanilla";
            Current.InstalledVersionId = "";
            _profiles.Save(_items);
            VersionText.Text = selected.Id;
            LoaderText.Text = "Vanilla";

            _changingVersion = true;
            VersionBox.SelectedIndex = _availableVersions.ToList().FindIndex(v => v.Id == selected.Id);
            _changingVersion = false;
            Log("Для профиля выбрана версия Minecraft " + selected.Id + ".");
        }
        catch (Exception ex)
        {
            _changingVersion = false;
            Log("Не удалось открыть список версий Minecraft: " + ex.Message);
        }
    }

'''
    cs = cs.replace(marker, method + marker, 1)
cs_path.write_text(cs, encoding='utf-8')

picker_source = Path('build/MinecraftVersionPickerWindow.cs').read_text(encoding='utf-8')
Path('NexusLauncher/MinecraftVersionPickerWindow.cs').write_text(picker_source, encoding='utf-8')
