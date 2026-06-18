from fetch_qiita_items import (
    QiitaItem,
    build_query,
    create_outlook_mail,
    parse_users,
    render_markdown,
    resolve_token,
)


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


def test_resolve_token_prefers_cli_token(monkeypatch):
    monkeypatch.setenv("QIITA_TOKEN", "env-token")

    assert resolve_token("cli-token") == "cli-token"


def test_resolve_token_uses_environment_token(monkeypatch):
    monkeypatch.setenv("QIITA_TOKEN", "env-token")

    assert resolve_token(None) == "env-token"


def test_resolve_token_returns_none_without_cli_or_environment(monkeypatch):
    monkeypatch.delenv("QIITA_TOKEN", raising=False)

    assert resolve_token(None) is None


class FakeMail:
    def __init__(self):
        self.To = None
        self.Subject = None
        self.Body = None
        self.displayed = False
        self.sent = False

    def Display(self):
        self.displayed = True

    def Send(self):
        self.sent = True


class FakeOutlook:
    def __init__(self, mail):
        self.mail = mail
        self.created_item_type = None

    def CreateItem(self, item_type):
        self.created_item_type = item_type
        return self.mail


def test_create_outlook_mail_displays_draft(monkeypatch):
    monkeypatch.setattr("fetch_qiita_items.sys.platform", "win32")
    mail = FakeMail()
    outlook = FakeOutlook(mail)

    def dispatch(name):
        assert name == "Outlook.Application"
        return outlook

    create_outlook_mail(
        body="# Qiita記事一覧\n",
        to="user@example.com",
        subject="Qiita記事一覧",
        send_now=False,
        dispatch=dispatch,
    )

    assert outlook.created_item_type == 0
    assert mail.To == "user@example.com"
    assert mail.Subject == "Qiita記事一覧"
    assert mail.Body == "# Qiita記事一覧\n"
    assert mail.displayed is True
    assert mail.sent is False


def test_create_outlook_mail_sends_when_requested(monkeypatch):
    monkeypatch.setattr("fetch_qiita_items.sys.platform", "win32")
    mail = FakeMail()
    outlook = FakeOutlook(mail)

    create_outlook_mail(
        body="body",
        to="user@example.com",
        subject="subject",
        send_now=True,
        dispatch=lambda name: outlook,
    )

    assert mail.sent is True
    assert mail.displayed is False


def test_create_outlook_mail_rejects_non_windows(monkeypatch):
    monkeypatch.setattr("fetch_qiita_items.sys.platform", "linux")

    try:
        create_outlook_mail(
            body="body",
            to="user@example.com",
            subject="subject",
            send_now=False,
            dispatch=lambda name: FakeOutlook(FakeMail()),
        )
    except RuntimeError as exc:
        assert "only supported on Windows" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
