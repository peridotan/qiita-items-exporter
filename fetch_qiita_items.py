from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import requests


API_URL = "https://qiita.com/api/v2/items"
PER_PAGE = 100


@dataclass(frozen=True)
class QiitaItem:
    title: str
    url: str
    created_at: str

    @property
    def created_date(self) -> str:
        return self.created_at[:10]


class QiitaApiError(RuntimeError):
    pass


def parse_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date: {value!r}. Use YYYY-MM-DD."
        ) from exc


def parse_users(value: str) -> list[str]:
    users = [user.strip() for user in value.split(",") if user.strip()]
    if not users:
        raise argparse.ArgumentTypeError("at least one user ID is required")
    return users


def build_query(user: str, start: str, end: str) -> str:
    return f"user:{user} created:>={start} created:<={end}"


def resolve_token(cli_token: str | None) -> str | None:
    return cli_token or os.environ.get("QIITA_TOKEN")


def request_items(
    session: requests.Session,
    *,
    user: str,
    start: str,
    end: str,
    page: int,
    token: str | None,
) -> list[dict[str, Any]]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = session.get(
        API_URL,
        params={
            "query": build_query(user, start, end),
            "page": page,
            "per_page": PER_PAGE,
        },
        headers=headers,
        timeout=30,
    )

    if response.status_code in {403, 429}:
        remaining = response.headers.get("Rate-Remaining")
        reset = response.headers.get("Rate-Reset")
        extra = ""
        if remaining is not None or reset is not None:
            extra = f" (Rate-Remaining={remaining}, Rate-Reset={reset})"
        raise QiitaApiError(f"rate limited while fetching {user}{extra}")

    if response.status_code == 401:
        raise QiitaApiError("invalid QIITA_TOKEN")

    if response.status_code == 404:
        raise QiitaApiError(f"user or endpoint not found while fetching {user}")

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise QiitaApiError(
            f"Qiita API error while fetching {user}: HTTP {response.status_code}"
        ) from exc

    data = response.json()
    if not isinstance(data, list):
        raise QiitaApiError(f"unexpected API response while fetching {user}")
    return data


def fetch_user_items(
    user: str,
    *,
    start: str,
    end: str,
    token: str | None,
    session: requests.Session | None = None,
) -> list[QiitaItem]:
    owns_session = session is None
    session = session or requests.Session()
    items: list[QiitaItem] = []

    try:
        page = 1
        while True:
            raw_items = request_items(
                session,
                user=user,
                start=start,
                end=end,
                page=page,
                token=token,
            )
            if not raw_items:
                break

            for raw_item in raw_items:
                title = str(raw_item.get("title", ""))
                url = str(raw_item.get("url", ""))
                created_at = str(raw_item.get("created_at", ""))
                if title and url and created_at:
                    items.append(QiitaItem(title=title, url=url, created_at=created_at))

            page += 1
    finally:
        if owns_session:
            session.close()

    return items


def render_markdown(results: dict[str, list[QiitaItem]], *, start: str, end: str) -> str:
    total_count = sum(len(items) for items in results.values())
    lines: list[str] = [
        "# Qiita記事一覧",
        "",
        f"対象期間: {start} ～ {end}",
        f"取得件数: {total_count}件",
        "",
    ]

    for user, items in results.items():
        lines.append(f"## {user}")
        lines.append(f"件数: {len(items)}件")
        lines.append("")

        if items:
            for item in sorted(items, key=lambda x: x.created_at):
                lines.append(f"- {item.created_date} [{item.title}]({item.url})")
        else:
            lines.append("_該当記事なし_")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Qiita items for multiple users and write Markdown."
    )
    parser.add_argument(
        "--users",
        required=True,
        type=parse_users,
        help="Comma-separated Qiita user IDs. Example: peridotan,user2,user3",
    )
    parser.add_argument("--start", required=True, type=parse_date, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, type=parse_date, help="YYYY-MM-DD")
    parser.add_argument("--out", required=True, help="Output Markdown file path")
    parser.add_argument(
        "--token",
        help="Qiita API access token. If omitted, QIITA_TOKEN is used.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.start > args.end:
        parser.error("--start must be earlier than or equal to --end")

    token = resolve_token(args.token)
    results: dict[str, list[QiitaItem]] = {}

    with requests.Session() as session:
        for user in args.users:
            try:
                results[user] = fetch_user_items(
                    user,
                    start=args.start,
                    end=args.end,
                    token=token,
                    session=session,
                )
            except QiitaApiError as exc:
                print(f"warning: {exc}", file=sys.stderr)
                results[user] = []

    output = render_markdown(results, start=args.start, end=args.end)
    Path(args.out).write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
