using System.ComponentModel;
using NexusLauncher.Services;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Input;
using System.Windows.Media;

namespace NexusLauncher;

/// <summary>Searchable picker for every version published in Mojang's official manifest.</summary>
public sealed class MinecraftVersionPickerWindow : Window
{
    private sealed record VersionRow(string Id, string Type, string TypeLabel);

    private readonly List<VersionRow> _rows;
    private readonly ICollectionView _view;
    private readonly TextBox _searchBox;
    private readonly ComboBox _filterBox;
    private readonly ListView _versionList;
    private readonly TextBlock _countText;
    private readonly Button _selectButton;

    public string? SelectedVersionId => (_versionList.SelectedItem as VersionRow)?.Id;

    public MinecraftVersionPickerWindow(IReadOnlyList<MinecraftVersion> versions, string currentVersion)
    {
        Title = "Выбор версии Minecraft — NEXUS";
        Width = 720;
        Height = 650;
        MinWidth = 580;
        MinHeight = 480;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        ResizeMode = ResizeMode.CanResize;
        Background = Brush("#10131B");
        Foreground = Brushes.White;
        FontFamily = new FontFamily("Segoe UI");

        _rows = versions.Select(v => new VersionRow(v.Id, v.Type, TypeLabel(v.Type))).ToList();

        var root = new Grid { Margin = new Thickness(22) };
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

        var heading = new StackPanel { Margin = new Thickness(0, 0, 0, 16) };
        heading.Children.Add(new TextBlock
        {
            Text = "Версии Minecraft",
            FontSize = 25,
            FontWeight = FontWeights.SemiBold,
            Foreground = Brushes.White
        });
        heading.Children.Add(new TextBlock
        {
            Text = "Полный официальный список: релизы, снапшоты, бета- и альфа-версии",
            Margin = new Thickness(0, 4, 0, 0),
            FontSize = 12,
            Foreground = Brush("#A7B0C0")
        });
        root.Children.Add(heading);
        Grid.SetRow(heading, 0);

        var searchArea = new Grid { Margin = new Thickness(0, 0, 0, 12) };
        searchArea.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        searchArea.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(190) });
        _searchBox = new TextBox
        {
            Height = 38,
            Margin = new Thickness(0, 0, 10, 0),
            Padding = new Thickness(10, 7, 10, 7),
            FontSize = 14,
            Background = Brush("#191F2B"),
            Foreground = Brushes.White,
            BorderBrush = Brush("#39445A"),
            BorderThickness = new Thickness(1),
            VerticalContentAlignment = VerticalAlignment.Center,
            ToolTip = "Например: 1.20.4, 1.8.9, 24w14a"
        };
        _filterBox = new ComboBox
        {
            Height = 38,
            Margin = new Thickness(0),
            Padding = new Thickness(7, 4, 7, 4),
            Background = Brush("#191F2B"),
            Foreground = Brushes.White,
            BorderBrush = Brush("#39445A"),
            ItemsSource = new[] { "Все версии", "Релизы", "Снапшоты", "Бета и альфа" },
            SelectedIndex = 0
        };
        searchArea.Children.Add(_searchBox);
        searchArea.Children.Add(_filterBox);
        Grid.SetColumn(_filterBox, 1);
        root.Children.Add(searchArea);
        Grid.SetRow(searchArea, 1);

        var listBorder = new Border
        {
            Background = Brush("#171D28"),
            BorderBrush = Brush("#30394B"),
            BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(9),
            Padding = new Thickness(6)
        };
        _versionList = new ListView
        {
            Background = Brushes.Transparent,
            Foreground = Brushes.White,
            BorderThickness = new Thickness(0),
            FontSize = 14,
            SelectionMode = SelectionMode.Single
        };
        _versionList.Resources[SystemColors.HighlightBrushKey] = Brush("#51402A");
        _versionList.Resources[SystemColors.HighlightTextBrushKey] = Brushes.White;
        _versionList.View = new GridView
        {
            Columns =
            {
                new GridViewColumn { Header = "Версия", Width = 390, DisplayMemberBinding = new Binding(nameof(VersionRow.Id)) },
                new GridViewColumn { Header = "Тип", Width = 220, DisplayMemberBinding = new Binding(nameof(VersionRow.TypeLabel)) }
            }
        };
        listBorder.Child = _versionList;
        root.Children.Add(listBorder);
        Grid.SetRow(listBorder, 2);

        var footer = new Grid { Margin = new Thickness(0, 14, 0, 0) };
        footer.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        footer.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        _countText = new TextBlock
        {
            VerticalAlignment = VerticalAlignment.Center,
            Foreground = Brush("#A7B0C0"),
            FontSize = 12
        };
        var actions = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
        var cancelButton = MakeButton("Отмена", "#292F40");
        cancelButton.IsCancel = true;
        cancelButton.Click += (_, _) => DialogResult = false;
        _selectButton = MakeButton("Выбрать версию", "#7C5CFC");
        _selectButton.IsDefault = true;
        _selectButton.IsEnabled = false;
        _selectButton.Click += (_, _) => AcceptSelection();
        actions.Children.Add(cancelButton);
        actions.Children.Add(_selectButton);
        footer.Children.Add(_countText);
        footer.Children.Add(actions);
        Grid.SetColumn(actions, 1);
        root.Children.Add(footer);
        Grid.SetRow(footer, 3);

        _view = CollectionViewSource.GetDefaultView(_rows);
        _view.Filter = IncludeVersion;
        _versionList.ItemsSource = _view;
        _searchBox.TextChanged += (_, _) => RefreshList();
        _filterBox.SelectionChanged += (_, _) => RefreshList();
        _versionList.SelectionChanged += (_, _) => _selectButton.IsEnabled = _versionList.SelectedItem is VersionRow;
        _versionList.MouseDoubleClick += (_, _) => AcceptSelection();
        _versionList.KeyDown += (_, e) =>
        {
            if (e.Key == Key.Enter && _versionList.SelectedItem is VersionRow)
            {
                AcceptSelection();
                e.Handled = true;
            }
        };

        Content = root;
        var selected = _rows.FirstOrDefault(v => v.Id.Equals(currentVersion, StringComparison.OrdinalIgnoreCase));
        _versionList.SelectedItem = selected;
        if (selected is not null) _versionList.ScrollIntoView(selected);
        RefreshList();
    }

    private bool IncludeVersion(object item)
    {
        if (item is not VersionRow version) return false;
        var query = _searchBox.Text.Trim();
        if (query.Length > 0 && !version.Id.Contains(query, StringComparison.OrdinalIgnoreCase)) return false;
        return _filterBox.SelectedIndex switch
        {
            1 => version.Type.Equals("release", StringComparison.OrdinalIgnoreCase),
            2 => version.Type.Equals("snapshot", StringComparison.OrdinalIgnoreCase),
            3 => version.Type.Equals("old_beta", StringComparison.OrdinalIgnoreCase) || version.Type.Equals("old_alpha", StringComparison.OrdinalIgnoreCase),
            _ => true
        };
    }

    private void RefreshList()
    {
        _view.Refresh();
        _countText.Text = $"Найдено версий: {_view.Cast<VersionRow>().Count():N0}";
        _selectButton.IsEnabled = _versionList.SelectedItem is VersionRow row && _view.Cast<VersionRow>().Any(v => v.Id == row.Id);
    }

    private void AcceptSelection()
    {
        if (SelectedVersionId is not null) DialogResult = true;
    }

    private static Button MakeButton(string text, string background) => new()
    {
        Content = text,
        Background = Brush(background),
        Foreground = Brushes.White,
        BorderThickness = new Thickness(0),
        Padding = new Thickness(16, 9, 16, 9),
        Margin = new Thickness(4, 0, 0, 0),
        MinWidth = 94,
        Cursor = Cursors.Hand
    };

    private static string TypeLabel(string type) => type.ToLowerInvariant() switch
    {
        "release" => "Релиз",
        "snapshot" => "Снапшот",
        "old_beta" => "Старая бета",
        "old_alpha" => "Старая альфа",
        _ => type
    };

    private static SolidColorBrush Brush(string color) => new((Color)ColorConverter.ConvertFromString(color));
}