from fetch_qiita_items import QiitaItem, build_query, parse_users, render_markdown


def test_render_markdown_groups_items_by_user():
    markdown = render_markdown(
        {
            "peridotan": [
                QiitaItem(
                    title="Later article",
                    url="https://qiita.com/peridotan/items/later",
                    created_at="2026-03-31T10:00:00+09:00",
                ),
                QiitaItem(
                    title="Early article",
                    url="https://qiita.com/peridotan/items/early",
                    created_at="2025-04-01T09:00:00+09:00",
                ),
            ],
            "user2": [],
        },
        start="2025-04-01",
        end="2026-03-31",
    )

    assert markdown.startswith("# Qiita記事一覧\n")
    assert "対象期間: 2025-04-01 ～ 2026-03-31" in markdown
    assert "取得件数: 2件" in markdown
    assert "## peridotan" in markdown
    assert "件数: 2件" in markdown
    assert "- 2025-04-01 [Early article](https://qiita.com/peridotan/items/early)" in markdown
    assert "- 2026-03-31 [Later article](https://qiita.com/peridotan/items/later)" in markdown
    assert "## user2" in markdown
    assert "件数: 0件" in markdown
    assert "_該当記事なし_" in markdown


def test_render_markdown_keeps_expected_layout_for_empty_user():
    markdown = render_markdown(
        {"nobody": []},
        start="2025-04-01",
        end="2026-03-31",
    )

    assert markdown == (
        "# Qiita記事一覧\n"
        "\n"
        "対象期間: 2025-04-01 ～ 2026-03-31\n"
        "取得件数: 0件\n"
        "\n"
        "## nobody\n"
        "件数: 0件\n"
        "\n"
        "_該当記事なし_\n"
    )


def test_build_query_uses_required_search_conditions():
    assert (
        build_query("peridotan", "2025-04-01", "2026-03-31")
        == "user:peridotan created:>=2025-04-01 created:<=2026-03-31"
    )


def test_parse_users_trims_empty_entries():
    assert parse_users(" peridotan, user2,,user3 ") == ["peridotan", "user2", "user3"]
